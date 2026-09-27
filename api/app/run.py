"""Stream one reconcile run. The model writes the script. The sandbox runs it."""

import csv
import io
import json
import os
from collections.abc import Iterator

from app.composer import LABEL, ComposerModel
from app.invariants import repeated_ids, tie_out_problems
from app.loop import ScriptModel, iter_heal
from app.match import reconcile
from app.parse import parse_amount, parse_date
from app.report import describe
from app.schema import Invoice, Ledger, Receipt
from app.writer import FIRST_HINT, HEAL_HINT, TASK, LocalWriter, bind_sources


class _Advising(ScriptModel):
    """Steer the first script toward the sample date, then hand it the traceback."""

    def __init__(self, inner: ScriptModel) -> None:
        self.inner = inner
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        extra = FIRST_HINT if self.calls == 1 else HEAL_HINT
        return self.inner.complete(prompt + extra)


def choose_model() -> tuple[ScriptModel, str, str]:
    if os.environ.get("CURSOR_API_KEY", "").strip():
        return _Advising(ComposerModel()), "cursor", LABEL
    return LocalWriter(), "local", "local writer"


def invoices_from_csv(text: str) -> list[Invoice]:
    return [
        Invoice(
            invoice_id=row["invoice_id"],
            supplier=row["supplier"],
            amount=parse_amount(row["amount_ksh"]),
            date=parse_date(row["date"]),
            ref=row["ref"],
        )
        for row in csv.DictReader(io.StringIO(text))
    ]


def receipts_from_json(text: str) -> list[Receipt]:
    rows = json.loads(text)
    return [
        Receipt(
            receipt_id=row["receipt_id"],
            ref=row["ref"],
            amount=parse_amount(row["amount"]),
            date=parse_date(row["date"]),
            counterparty=row["counterparty"],
        )
        for row in rows
    ]


def _sse(payload: dict[str, object]) -> str:
    return "data: " + json.dumps(payload) + "\n\n"


def reconcile_events(csv_text: str, statement_text: str, *, pace: float = 0) -> Iterator[str]:
    if len(csv_text) > 200_000 or len(statement_text) > 200_000:
        yield _sse({"kind": "note", "tone": "error", "text": "Error: that file is too large."})
        return
    if not csv_text.strip() or not statement_text.strip():
        yield _sse({"kind": "note", "tone": "error", "text": "Error: both files are required."})
        return
    try:
        invoices = invoices_from_csv(csv_text)
        receipts = receipts_from_json(statement_text)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        yield _sse({"kind": "note", "tone": "error", "text": f"Error: {exc}"})
        return

    model, engine, label = choose_model()
    yield _sse({"kind": "meta", "engine": engine, "model": label})

    def bind(source: str) -> str:
        return bind_sources(source, csv_text, statement_text)

    succeeded = False
    for event in iter_heal(
        model,
        TASK,
        invoices=invoices,
        receipts=receipts,
        bind=bind,
        pace=pace,
    ):
        if event["kind"] == "result" and isinstance(event.get("ledger"), dict):
            ledger = Ledger.model_validate(event["ledger"])
            problems = repeated_ids(ledger) + tie_out_problems(ledger, invoices, receipts)
            if problems:
                continue
            event = {**event, **describe(ledger, invoices, statement_text)}
            succeeded = True
        if event["kind"] in {"status", "done"}:
            continue
        yield _sse(event)
    if succeeded:
        return
    ledger = reconcile(invoices, receipts)
    yield _sse(
        {
            "kind": "note",
            "tone": "warn",
            "text": "Three attempts failed. The deterministic ledger is shown. This run is fallback.",
        }
    )
    yield _sse(
        {
            "kind": "result",
            "mode": "fallback",
            "ledger": ledger.model_dump(mode="json"),
            **describe(ledger, invoices, statement_text),
        }
    )

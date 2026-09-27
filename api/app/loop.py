"""Ask for a script, run it, and hand the failure back. Three tries, then stop."""

import json
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from app.invariants import repeated_ids, tie_out_problems
from app.sandbox import ScriptRejected, run_script
from app.schema import Invoice, Ledger, Receipt


@dataclass(frozen=True)
class Attempt:
    iteration: int
    status: str
    detail: str


@dataclass(frozen=True)
class HealResult:
    ledger: Ledger | None
    attempts: list[Attempt]
    mode: str


class ScriptModel:
    def complete(self, prompt: str) -> str:
        raise NotImplementedError


def extract_code(text: str) -> str:
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    if "```" not in text:
        return text
    block = text.split("```", 2)[1]
    if block.startswith("python"):
        block = block[len("python") :]
    return block.strip() + "\n"


def _error_note(detail: str) -> str:
    line = ""
    for candidate in reversed(detail.splitlines()):
        if candidate.strip():
            line = candidate.strip()
            break
    if not line:
        return "Error: the script failed"
    if ": " in line:
        kind, rest = line.split(": ", 1)
        if kind.endswith("Error") or kind.endswith("Exception"):
            return f"Error: {kind} — {rest}"
    return f"Error: {line}"


def _execute(
    source: str,
    invoices: list[Invoice] | None,
    receipts: list[Receipt] | None,
) -> tuple[str, str, Ledger | None]:
    try:
        completed = run_script(source)
    except ScriptRejected as exc:
        return "rejected", str(exc), None
    except subprocess.TimeoutExpired:
        return "timeout", "the script exceeded the time limit", None
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout)[-2000:]
        return "crashed", detail, None
    try:
        ledger = Ledger.model_validate(json.loads(completed.stdout))
    except (json.JSONDecodeError, ValueError) as exc:
        return "invalid", f"output was not a ledger: {exc}", None
    if invoices is not None and receipts is not None:
        problems = repeated_ids(ledger) + tie_out_problems(ledger, invoices, receipts)
        if problems:
            return "unbalanced", "\n".join(problems), None
    return "accepted", "ledger accepted", ledger


def iter_heal(
    model: ScriptModel,
    task: str,
    *,
    invoices: list[Invoice] | None = None,
    receipts: list[Receipt] | None = None,
    bind: Callable[[str], str] | None = None,
    max_tries: int = 3,
    pace: float = 0,
) -> Iterator[dict[str, object]]:
    """Yield the notes, the script, and the real sandbox result as they happen."""
    error = ""
    yield _paced({"kind": "note", "tone": "info", "text": "Analyzing data structure..."}, pace)
    for iteration in range(1, max_tries + 1):
        yield _paced({"kind": "attempt", "iteration": iteration, "total": max_tries}, pace)
        yield _paced(
            {"kind": "note", "tone": "info", "text": "Generating reconciliation script..."},
            pace,
        )
        prompt = task if not error else f"{task}\n\nThe previous script failed:\n{error}"
        try:
            source = extract_code(model.complete(prompt))
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            yield {
                "kind": "status",
                "iteration": iteration,
                "status": "crashed",
                "detail": error,
            }
            yield _paced({"kind": "note", "tone": "error", "text": _error_note(error)}, pace)
            if iteration < max_tries:
                yield _paced(
                    {
                        "kind": "note",
                        "tone": "warn",
                        "text": "Diagnosing failure... regenerating script...",
                    },
                    pace,
                )
            continue
        yield _paced({"kind": "code", "iteration": iteration, "text": source}, pace)
        yield _paced(
            {"kind": "note", "tone": "info", "text": "Running the script in the sandbox..."},
            pace,
        )
        ran_source = bind(source) if bind else source
        status, detail, ledger = _execute(ran_source, invoices, receipts)
        yield {"kind": "status", "iteration": iteration, "status": status, "detail": detail}
        if status == "accepted" and ledger is not None:
            mode = "healed" if iteration > 1 else "clean"
            yield _paced({"kind": "note", "tone": "ok", "text": "Reconciliation complete."}, pace)
            yield {
                "kind": "result",
                "mode": mode,
                "ledger": ledger.model_dump(mode="json"),
            }
            return
        error = detail
        yield _paced({"kind": "note", "tone": "error", "text": _error_note(detail)}, pace)
        if "\n" in detail.strip():
            yield _paced({"kind": "trace", "text": detail}, pace)
        if iteration < max_tries:
            yield _paced(
                {
                    "kind": "note",
                    "tone": "warn",
                    "text": "Diagnosing failure... regenerating script...",
                },
                pace,
            )
    yield {"kind": "done", "mode": "failed"}


def _paced(event: dict[str, object], pace: float) -> dict[str, object]:
    if pace > 0:
        time.sleep(pace)
    return event


def heal(
    model: ScriptModel,
    task: str,
    *,
    invoices: list[Invoice] | None = None,
    receipts: list[Receipt] | None = None,
    max_tries: int = 3,
) -> HealResult:
    ledger: Ledger | None = None
    attempts: list[Attempt] = []
    mode = "failed"
    for event in iter_heal(
        model,
        task,
        invoices=invoices,
        receipts=receipts,
        max_tries=max_tries,
        pace=0,
    ):
        if event["kind"] == "status":
            attempts.append(
                Attempt(int(event["iteration"]), str(event["status"]), str(event["detail"]))
            )
            if event["status"] == "accepted":
                mode = "healed" if int(event["iteration"]) > 1 else "clean"
        elif event["kind"] == "result":
            ledger = Ledger.model_validate(event["ledger"])
            mode = str(event["mode"])
    return HealResult(ledger, attempts, mode)

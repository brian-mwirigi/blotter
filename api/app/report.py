"""Turn a ledger into the rows and the sentence the demo shows."""

import json
from decimal import Decimal

from app.parse import parse_amount
from app.schema import Invoice, Ledger


def _cell(value: object) -> str:
    if isinstance(value, str) and not value.strip().replace(",", "").isdigit():
        return value.strip()
    return f"{parse_amount(value):,.0f}"


def _ksh(amount: Decimal) -> str:
    return f"KSh {amount:,.0f}"


def describe(ledger: Ledger, invoices: list[Invoice], statement_text: str) -> dict[str, object]:
    raw_amounts: dict[str, object] = {}
    try:
        for row in json.loads(statement_text):
            raw_amounts[str(row["receipt_id"])] = row["amount"]
    except (json.JSONDecodeError, TypeError, KeyError):
        raw_amounts = {}

    match_by_invoice = {match.invoice_id: match for match in ledger.matches}
    anomaly_by_invoice = {
        anomaly.invoice_id: anomaly for anomaly in ledger.anomalies if anomaly.invoice_id
    }
    anomaly_by_ref = {anomaly.ref: anomaly for anomaly in ledger.anomalies if anomaly.ref}

    rows: list[dict[str, str]] = []
    for invoice in invoices:
        partial = anomaly_by_invoice.get(invoice.invoice_id)
        duplicate = anomaly_by_ref.get(invoice.ref)
        match = match_by_invoice.get(invoice.invoice_id)
        if partial is not None and partial.kind == "partial":
            receipt_id = partial.receipt_ids[0] if partial.receipt_ids else ""
            received = _cell(raw_amounts.get(receipt_id, "0"))
            gap = partial.gap if partial.gap is not None else Decimal("0")
            rows.append(
                {
                    "supplier": invoice.supplier,
                    "invoice": _cell(invoice.amount),
                    "received": received,
                    "status": f"Short {gap:,.0f}",
                    "tone": "short",
                }
            )
            continue
        if duplicate is not None and duplicate.kind == "duplicate_ref":
            receipt_id = match.receipt_id if match is not None else ""
            received = _cell(raw_amounts.get(receipt_id, invoice.amount))
            rows.append(
                {
                    "supplier": invoice.supplier,
                    "invoice": _cell(invoice.amount),
                    "received": received,
                    "status": "Duplicate",
                    "tone": "",
                }
            )
            continue
        if match is not None:
            rows.append(
                {
                    "supplier": invoice.supplier,
                    "invoice": _cell(invoice.amount),
                    "received": _cell(raw_amounts.get(match.receipt_id, match.amount)),
                    "status": "Matched",
                    "tone": "",
                }
            )
            continue
        rows.append(
            {
                "supplier": invoice.supplier,
                "invoice": _cell(invoice.amount),
                "received": "—",
                "status": "Open",
                "tone": "short",
            }
        )

    partials = [anomaly for anomaly in ledger.anomalies if anomaly.kind == "partial" and anomaly.gap]
    if partials:
        partial = partials[0]
        receipt = partial.receipt_ids[0] if partial.receipt_ids else "the receipt"
        headline = f"{_ksh(partial.gap or Decimal('0'))} shortfall — invoice {partial.invoice_id} vs receipt {receipt}"
        detail = partial.detail
    else:
        headline = f"{_ksh(ledger.shortfall)} still open"
        detail = ""

    return {
        "headline": headline,
        "detail": detail,
        "matched": len(ledger.matches),
        "anomalies": len(ledger.anomalies),
        "rows": rows,
    }

"""Checks that sit outside the model. A clean process exit is not a balanced ledger."""

from app.schema import Ledger


def repeated_ids(ledger: Ledger) -> list[str]:
    invoice_ids: list[str] = []
    receipt_ids: list[str] = []
    for match in ledger.matches:
        invoice_ids.append(match.invoice_id)
        receipt_ids.append(match.receipt_id)
    for anomaly in ledger.anomalies:
        if anomaly.invoice_id:
            invoice_ids.append(anomaly.invoice_id)
        receipt_ids.extend(anomaly.receipt_ids)

    problems: list[str] = []
    for label, ids in (("invoice", invoice_ids), ("receipt", receipt_ids)):
        seen: set[str] = set()
        for item in ids:
            if item in seen:
                problems.append(f"{label} {item} is used more than once")
            seen.add(item)
    return problems

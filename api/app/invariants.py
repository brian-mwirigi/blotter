"""Checks that sit outside the model. A clean process exit is not a balanced ledger."""

from decimal import Decimal

from app.schema import Invoice, Ledger, Receipt


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


def tie_out_problems(
    ledger: Ledger, invoices: list[Invoice], receipts: list[Receipt]
) -> list[str]:
    invoice_amounts = {invoice.invoice_id: invoice.amount for invoice in invoices}
    receipt_amounts = {receipt.receipt_id: receipt.amount for receipt in receipts}
    problems: list[str] = []

    applied: dict[str, Decimal] = {}
    for match in ledger.matches:
        if match.receipt_id not in receipt_amounts:
            problems.append(f"receipt {match.receipt_id} is not on the statement")
            continue
        if match.invoice_id not in invoice_amounts:
            problems.append(f"invoice {match.invoice_id} is not in the file")
        applied[match.receipt_id] = applied.get(match.receipt_id, Decimal("0")) + match.amount

    for receipt_id, amount in applied.items():
        if receipt_id in receipt_amounts and amount > receipt_amounts[receipt_id]:
            problems.append(
                f"receipt {receipt_id} applies {amount}, above {receipt_amounts[receipt_id]}"
            )

    leftover = sum(
        (amount for receipt_id, amount in receipt_amounts.items() if receipt_id not in applied),
        Decimal("0"),
    )
    statement = sum(receipt_amounts.values(), Decimal("0"))
    applied_total = sum(applied.values(), Decimal("0"))
    if applied_total + leftover != statement:
        problems.append(
            f"applied {applied_total} plus leftover {leftover} is not the statement {statement}"
        )

    for anomaly in ledger.anomalies:
        if anomaly.kind != "partial" or anomaly.gap is None or anomaly.invoice_id is None:
            continue
        invoice_amount = invoice_amounts.get(anomaly.invoice_id)
        if invoice_amount is None:
            problems.append(f"partial {anomaly.invoice_id} is not an invoice")
            continue
        paid = sum(
            (
                receipt_amounts[receipt_id]
                for receipt_id in anomaly.receipt_ids
                if receipt_id in receipt_amounts
            ),
            Decimal("0"),
        )
        expected = invoice_amount - paid
        if anomaly.gap != expected:
            problems.append(f"gap on {anomaly.invoice_id} is {anomaly.gap}, not {expected}")
    return problems

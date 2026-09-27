"""Match receipts to invoices. A later pull flags duplicate references."""

from decimal import Decimal

from app.schema import Anomaly, Invoice, Ledger, Match, Receipt


def reconcile(invoices: list[Invoice], receipts: list[Receipt]) -> Ledger:
    invoices_by_ref: dict[str, list[Invoice]] = {}
    for invoice in invoices:
        invoices_by_ref.setdefault(invoice.ref, []).append(invoice)

    matches: list[Match] = []
    anomalies: list[Anomaly] = []
    for receipt in receipts:
        candidates = invoices_by_ref.get(receipt.ref, [])
        if len(candidates) != 1:
            continue
        invoice = candidates[0]
        if receipt.amount == invoice.amount:
            matches.append(
                Match(
                    invoice_id=invoice.invoice_id,
                    receipt_id=receipt.receipt_id,
                    ref=receipt.ref,
                    amount=receipt.amount,
                )
            )
            continue
        if receipt.amount < invoice.amount:
            gap = invoice.amount - receipt.amount
            anomalies.append(
                Anomaly(
                    kind="partial",
                    invoice_id=invoice.invoice_id,
                    receipt_ids=[receipt.receipt_id],
                    ref=receipt.ref,
                    gap=gap,
                    detail=f"{invoice.supplier} was paid {receipt.amount} of {invoice.amount}",
                )
            )
    shortfall = sum((anomaly.gap for anomaly in anomalies if anomaly.gap is not None), Decimal("0"))
    return Ledger(matches=matches, anomalies=anomalies, shortfall=shortfall)

"""Match receipts to invoices and flag a reference that was used twice."""

from decimal import Decimal

from app.schema import Anomaly, Invoice, Ledger, Match, Receipt


def reconcile(invoices: list[Invoice], receipts: list[Receipt]) -> Ledger:
    invoices_by_ref: dict[str, list[Invoice]] = {}
    for invoice in invoices:
        invoices_by_ref.setdefault(invoice.ref, []).append(invoice)

    receipts_by_ref: dict[str, list[Receipt]] = {}
    for receipt in receipts:
        receipts_by_ref.setdefault(receipt.ref, []).append(receipt)

    matches: list[Match] = []
    anomalies: list[Anomaly] = []
    for ref, group in receipts_by_ref.items():
        candidates = invoices_by_ref.get(ref, [])
        if len(group) > 1:
            matched_first = len(candidates) == 1 and group[0].amount == candidates[0].amount
            extras = group[1:] if matched_first else group
            anomalies.append(
                Anomaly(
                    kind="duplicate_ref",
                    invoice_id=None if matched_first or len(candidates) != 1 else candidates[0].invoice_id,
                    receipt_ids=[receipt.receipt_id for receipt in extras],
                    ref=ref,
                    detail=f"{ref} appears on {len(group)} receipts",
                )
            )
            if matched_first:
                matches.append(
                    Match(
                        invoice_id=candidates[0].invoice_id,
                        receipt_id=group[0].receipt_id,
                        ref=ref,
                        amount=group[0].amount,
                    )
                )
            continue
        if len(candidates) != 1:
            continue
        invoice = candidates[0]
        receipt = group[0]
        if receipt.amount == invoice.amount:
            matches.append(
                Match(
                    invoice_id=invoice.invoice_id,
                    receipt_id=receipt.receipt_id,
                    ref=ref,
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
                    ref=ref,
                    gap=gap,
                    detail=f"{invoice.supplier} was paid {receipt.amount} of {invoice.amount}",
                )
            )
    shortfall = sum((anomaly.gap for anomaly in anomalies if anomaly.gap is not None), Decimal("0"))
    return Ledger(matches=matches, anomalies=anomalies, shortfall=shortfall)

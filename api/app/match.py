"""Match receipts to invoices. Later pulls add partials and duplicate refs."""

from decimal import Decimal

from app.schema import Invoice, Ledger, Match, Receipt


def reconcile(invoices: list[Invoice], receipts: list[Receipt]) -> Ledger:
    invoices_by_ref: dict[str, list[Invoice]] = {}
    for invoice in invoices:
        invoices_by_ref.setdefault(invoice.ref, []).append(invoice)

    matches: list[Match] = []
    for receipt in receipts:
        candidates = invoices_by_ref.get(receipt.ref, [])
        if len(candidates) != 1:
            continue
        invoice = candidates[0]
        if receipt.amount != invoice.amount:
            continue
        matches.append(
            Match(
                invoice_id=invoice.invoice_id,
                receipt_id=receipt.receipt_id,
                ref=receipt.ref,
                amount=receipt.amount,
            )
        )
    return Ledger(matches=matches, anomalies=[], shortfall=Decimal("0"))

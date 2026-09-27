from decimal import Decimal

from app.invariants import repeated_ids, tie_out_problems
from app.load import load_invoices, load_receipts
from app.match import reconcile


def test_sample_files_lock_the_hero_numbers():
    invoices = load_invoices()
    receipts = load_receipts()
    hero_invoice = next(invoice for invoice in invoices if invoice.invoice_id == "INV-100")
    hero_receipt = next(receipt for receipt in receipts if receipt.receipt_id == "RCPT-100")
    assert hero_invoice.amount == Decimal("18000")
    assert hero_receipt.amount == Decimal("13500")

    ledger = reconcile(invoices, receipts)
    assert ledger.shortfall == Decimal("4500")
    partial = next(anomaly for anomaly in ledger.anomalies if anomaly.kind == "partial")
    assert partial.invoice_id == "INV-100"
    assert partial.gap == Decimal("4500")
    assert partial.receipt_ids == ["RCPT-100"]
    assert any(anomaly.kind == "duplicate_ref" and anomaly.ref == "REF-102" for anomaly in ledger.anomalies)
    assert any(match.invoice_id == "INV-103" for match in ledger.matches)
    assert repeated_ids(ledger) == []
    assert tie_out_problems(ledger, invoices, receipts) == []

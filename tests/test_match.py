from datetime import date
from decimal import Decimal

from app.invariants import repeated_ids
from app.match import reconcile
from app.schema import Invoice, Receipt


def _invoice(invoice_id: str, amount: str, ref: str) -> Invoice:
    return Invoice(
        invoice_id=invoice_id,
        supplier="Supplier",
        amount=Decimal(amount),
        date=date(2026, 3, 12),
        ref=ref,
    )


def _receipt(receipt_id: str, amount: str, ref: str) -> Receipt:
    return Receipt(
        receipt_id=receipt_id,
        ref=ref,
        amount=Decimal(amount),
        date=date(2026, 3, 12),
        counterparty="Supplier",
    )


def test_exact_reference_and_amount_match():
    ledger = reconcile(
        [_invoice("INV-101", "7500", "REF-101")],
        [_receipt("RCPT-101", "7500", "REF-101")],
    )
    assert len(ledger.matches) == 1
    assert ledger.matches[0].invoice_id == "INV-101"
    assert ledger.shortfall == Decimal("0")


def test_hero_partial_is_a_gap_of_4500():
    ledger = reconcile(
        [_invoice("INV-100", "18000", "REF-100")],
        [_receipt("RCPT-100", "13500", "REF-100")],
    )
    assert ledger.matches == []
    assert ledger.shortfall == Decimal("4500")
    assert ledger.anomalies[0].kind == "partial"
    assert ledger.anomalies[0].invoice_id == "INV-100"
    assert ledger.anomalies[0].gap == Decimal("4500")


def test_duplicate_ref_stays_visible_and_the_shortfall_stays_4500():
    ledger = reconcile(
        [
            _invoice("INV-100", "18000", "REF-100"),
            _invoice("INV-102", "22000", "REF-102"),
        ],
        [
            _receipt("RCPT-100", "13500", "REF-100"),
            _receipt("RCPT-102A", "22000", "REF-102"),
            _receipt("RCPT-102B", "22000", "REF-102"),
        ],
    )
    duplicate = next(anomaly for anomaly in ledger.anomalies if anomaly.kind == "duplicate_ref")
    assert duplicate.ref == "REF-102"
    assert duplicate.receipt_ids == ["RCPT-102B"]
    assert any(match.receipt_id == "RCPT-102A" for match in ledger.matches)
    assert repeated_ids(ledger) == []
    assert ledger.shortfall == Decimal("4500")

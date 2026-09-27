from datetime import date
from decimal import Decimal

from app.schema import Anomaly, Invoice, Ledger, Match, Receipt


def test_ledger_accepts_the_hero_partial():
    ledger = Ledger(
        matches=[],
        anomalies=[
            Anomaly(
                kind="partial",
                invoice_id="INV-100",
                receipt_ids=["RCPT-100"],
                ref="REF-100",
                gap=Decimal("4500"),
                detail="Amani Hardware was paid 13500 of 18000",
            )
        ],
        shortfall=Decimal("4500"),
    )
    assert ledger.shortfall == Decimal("4500")
    assert ledger.anomalies[0].invoice_id == "INV-100"


def test_records_keep_their_dates():
    invoice = Invoice(
        invoice_id="INV-100",
        supplier="Amani Hardware",
        amount=Decimal("18000"),
        date=date(2026, 3, 12),
        ref="REF-100",
    )
    receipt = Receipt(
        receipt_id="RCPT-100",
        ref="REF-100",
        amount=Decimal("13500"),
        date=date(2026, 3, 12),
        counterparty="Amani Hardware",
    )
    match = Match(invoice_id="INV-100", receipt_id="RCPT-100", ref="REF-100", amount=Decimal("13500"))
    assert invoice.amount - receipt.amount == Decimal("4500")
    assert match.ref == "REF-100"

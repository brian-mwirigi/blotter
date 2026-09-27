from datetime import date
from decimal import Decimal

from app.invariants import repeated_ids, tie_out_problems
from app.schema import Anomaly, Invoice, Ledger, Match, Receipt


def test_repeated_receipt_id_is_rejected():
    ledger = Ledger(
        matches=[
            Match(invoice_id="INV-101", receipt_id="RCPT-101", ref="REF-101", amount=Decimal("7500")),
        ],
        anomalies=[
            Anomaly(
                kind="duplicate_ref",
                invoice_id="INV-101",
                receipt_ids=["RCPT-101"],
                ref="REF-101",
                detail="same receipt listed twice",
            )
        ],
        shortfall=Decimal("0"),
    )
    problems = repeated_ids(ledger)
    assert any("RCPT-101" in problem for problem in problems)


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


def test_applied_plus_leftover_must_equal_the_statement():
    invoices = [_invoice("INV-100", "18000", "REF-100"), _invoice("INV-101", "7500", "REF-101")]
    receipts = [_receipt("RCPT-100", "13500", "REF-100"), _receipt("RCPT-101", "7500", "REF-101")]
    balanced = Ledger(
        matches=[
            Match(invoice_id="INV-101", receipt_id="RCPT-101", ref="REF-101", amount=Decimal("7500")),
        ],
        anomalies=[
            Anomaly(
                kind="partial",
                invoice_id="INV-100",
                receipt_ids=["RCPT-100"],
                ref="REF-100",
                gap=Decimal("4500"),
                detail="short",
            )
        ],
        shortfall=Decimal("4500"),
    )
    assert tie_out_problems(balanced, invoices, receipts) == []

    over_applied = balanced.model_copy(
        update={
            "matches": [
                Match(invoice_id="INV-101", receipt_id="RCPT-101", ref="REF-101", amount=Decimal("8000")),
            ]
        }
    )
    assert tie_out_problems(over_applied, invoices, receipts)

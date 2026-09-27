from decimal import Decimal

from app.invariants import repeated_ids
from app.schema import Anomaly, Ledger, Match


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

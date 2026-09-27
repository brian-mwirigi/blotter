from datetime import date
from decimal import Decimal

from app.loop import heal
from app.schema import Invoice, Receipt

GOOD = """
import json
print(json.dumps({
  "matches": [],
  "anomalies": [{
    "kind": "partial",
    "invoice_id": "INV-100",
    "receipt_ids": ["RCPT-100"],
    "ref": "REF-100",
    "gap": "4500",
    "detail": "Amani Hardware was paid 13500 of 18000"
  }],
  "shortfall": "4500"
}))
"""

BROKEN = "raise TypeError(\"time data '1773273600' does not match format '%d/%m/%Y'\")\n"


class Stub:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if len(self.prompts) == 1:
            return BROKEN
        return GOOD


def test_a_type_error_is_healed_on_the_second_run():
    stub = Stub()
    result = heal(stub, "Reconcile the sample.")
    assert result.mode == "healed"
    assert [attempt.status for attempt in result.attempts] == ["crashed", "accepted"]
    assert "TypeError" in result.attempts[0].detail
    assert "TypeError" in stub.prompts[1]
    assert result.ledger is not None
    assert result.ledger.shortfall == Decimal("4500")


BAD_GAP = """
import json
print(json.dumps({
  "matches": [],
  "anomalies": [{
    "kind": "partial",
    "invoice_id": "INV-100",
    "receipt_ids": ["RCPT-100"],
    "ref": "REF-100",
    "gap": "9999",
    "detail": "wrong"
  }],
  "shortfall": "9999"
}))
"""


class LiesThenFixes:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return BAD_GAP if self.calls == 1 else GOOD


def test_a_clean_exit_with_a_bad_gap_is_rejected():
    invoices = [
        Invoice(
            invoice_id="INV-100",
            supplier="Amani Hardware",
            amount=Decimal("18000"),
            date=date(2026, 3, 12),
            ref="REF-100",
        )
    ]
    receipts = [
        Receipt(
            receipt_id="RCPT-100",
            ref="REF-100",
            amount=Decimal("13500"),
            date=date(2026, 3, 12),
            counterparty="Amani Hardware",
        )
    ]
    result = heal(LiesThenFixes(), "Reconcile.", invoices=invoices, receipts=receipts)
    assert result.mode == "healed"
    assert result.attempts[0].status == "unbalanced"
    assert result.ledger is not None
    assert result.ledger.shortfall == Decimal("4500")

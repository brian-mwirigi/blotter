from decimal import Decimal

from app.loop import heal

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

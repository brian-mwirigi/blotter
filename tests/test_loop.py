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


class Once:
    def complete(self, prompt: str) -> str:
        return GOOD


def test_a_good_script_is_accepted_on_the_first_try():
    result = heal(Once(), "Reconcile the sample files.")
    assert result.mode == "clean"
    assert result.ledger is not None
    assert result.ledger.shortfall == Decimal("4500")
    assert len(result.attempts) == 1
    assert result.attempts[0].status == "accepted"

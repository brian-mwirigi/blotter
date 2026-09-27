import json

from app.load import INVOICES, STATEMENT
from app.run import reconcile_events


def _payloads(chunks: list[str]) -> list[dict]:
    text = "".join(chunks)
    payloads = []
    for block in text.split("\n\n"):
        line = block.strip()
        if line.startswith("data:"):
            payloads.append(json.loads(line[len("data:") :].strip()))
    return payloads


def test_the_sample_day_crashes_then_heals(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    events = _payloads(
        list(
            reconcile_events(
                INVOICES.read_text(encoding="utf-8"),
                STATEMENT.read_text(encoding="utf-8"),
                pace=0,
            )
        )
    )
    codes = [event["text"] for event in events if event["kind"] == "code"]
    notes = [event["text"] for event in events if event["kind"] == "note"]
    assert "raise" not in codes[0]
    assert "strptime" in codes[0]
    assert any("1773273600" in event.get("text", "") for event in events)
    assert any(event["kind"] == "attempt" and event["iteration"] == 1 for event in events)
    assert any(event["kind"] == "attempt" and event["iteration"] == 2 for event in events)
    assert "Diagnosing failure... regenerating script..." in notes
    assert "Reconciliation complete." in notes
    result = next(event for event in events if event["kind"] == "result")
    assert result["mode"] == "healed"
    assert result["matched"] == 3
    assert result["anomalies"] == 2
    assert result["headline"] == "KSh 4,500 shortfall — invoice INV-100 vs receipt RCPT-100"
    assert any(row["supplier"] == "Coast Sugar" and row["received"] == "KSh 4,500" for row in result["rows"])
    assert any(row["tone"] == "short" and "4,500" in row["status"] for row in result["rows"])

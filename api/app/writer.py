"""Scripts the sandbox actually runs.

The first script parses every date as DD/MM/YYYY, which is the shape of the
sample row. The UNIX timestamp later in the statement makes that call raise.
The second script reads the same strings and builds the ledger from them.
"""

from app.loop import ScriptModel

TASK = """Write a Python script that reconciles INVOICES_CSV with STATEMENT_JSON.
Those two names are already Python string variables. Do not read files. Do not import pandas. Do not call open, eval, or exec.
Invoice columns: invoice_id, supplier, amount_ksh, date, ref.
Each statement object has receipt_id, ref, amount, date, counterparty.
A sample statement object is {"receipt_id": "RCPT-101", "ref": "REF-101", "amount": 7500, "date": "12/03/2026", "counterparty": "Lake Flour"}.
Match a receipt to the invoice with the same ref.
If the amounts are equal, add a match with invoice_id, receipt_id, ref, and amount as a string.
If the receipt amount is smaller, add an anomaly with kind "partial", invoice_id, receipt_ids, ref, gap as a string, and detail.
If one ref is on several receipts and the first amount equals the invoice, match only that first receipt. Add kind "duplicate_ref" whose receipt_ids are the other receipts, and omit invoice_id on that anomaly.
Print only a JSON object, with no markdown, in this shape:
{"matches": [], "anomalies": [], "shortfall": "0"}
shortfall is the sum of the partial gaps.
"""

FIRST_HINT = (
    "\n\nParse every date with datetime.strptime(str(value), '%d/%m/%Y'). "
    "The sample date is written DD/MM/YYYY."
)

HEAL_HINT = (
    "\n\nThe traceback is from the script you just wrote. "
    "If a date is an integer or an all-digit string, it is a UNIX timestamp in UTC: "
    "datetime.fromtimestamp(int(value), tz=timezone.utc). "
    "If an amount is text, remove KSh, KES, and commas before converting it. "
    "Keep the ledger rules above."
)

NAIVE = """import json
from datetime import datetime

def parse_date(value):
    return datetime.strptime(str(value), "%d/%m/%Y").date().isoformat()

rows = json.loads(STATEMENT_JSON)
for row in rows:
    row["date"] = parse_date(row["date"])
print(json.dumps({"rows": len(rows)}))
"""

HEALED = """import json
from datetime import datetime, timezone
from decimal import Decimal

def money(value):
    if isinstance(value, bool):
        raise ValueError("amount")
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).replace("KSh", "").replace("KES", "").replace("ksh", "").replace(",", "").strip()
    return Decimal(text)

def invoice_rows():
    lines = [line for line in INVOICES_CSV.splitlines() if line.strip()]
    header = lines[0].split(",")
    parsed = []
    for line in lines[1:]:
        row = dict(zip(header, line.split(",")))
        parsed.append({
            "invoice_id": row["invoice_id"],
            "supplier": row["supplier"],
            "amount": money(row["amount_ksh"]),
            "ref": row["ref"],
        })
    return parsed

def receipt_rows():
    parsed = []
    for row in json.loads(STATEMENT_JSON):
        parsed.append({
            "receipt_id": row["receipt_id"],
            "ref": row["ref"],
            "amount": money(row["amount"]),
        })
    return parsed

invoices_by_ref = {}
for item in invoice_rows():
    invoices_by_ref.setdefault(item["ref"], []).append(item)
receipts_by_ref = {}
for item in receipt_rows():
    receipts_by_ref.setdefault(item["ref"], []).append(item)

matches = []
anomalies = []
for ref, group in receipts_by_ref.items():
    candidates = invoices_by_ref.get(ref, [])
    if len(group) > 1:
        matched_first = len(candidates) == 1 and group[0]["amount"] == candidates[0]["amount"]
        extras = group[1:] if matched_first else group
        anomaly = {
            "kind": "duplicate_ref",
            "receipt_ids": [item["receipt_id"] for item in extras],
            "ref": ref,
            "detail": ref + " appears on " + str(len(group)) + " receipts",
        }
        if not matched_first and len(candidates) == 1:
            anomaly["invoice_id"] = candidates[0]["invoice_id"]
        anomalies.append(anomaly)
        if matched_first:
            matches.append({
                "invoice_id": candidates[0]["invoice_id"],
                "receipt_id": group[0]["receipt_id"],
                "ref": ref,
                "amount": str(group[0]["amount"]),
            })
        continue
    if len(candidates) != 1:
        continue
    invoice = candidates[0]
    receipt = group[0]
    if receipt["amount"] == invoice["amount"]:
        matches.append({
            "invoice_id": invoice["invoice_id"],
            "receipt_id": receipt["receipt_id"],
            "ref": ref,
            "amount": str(receipt["amount"]),
        })
        continue
    if receipt["amount"] < invoice["amount"]:
        gap = invoice["amount"] - receipt["amount"]
        anomalies.append({
            "kind": "partial",
            "invoice_id": invoice["invoice_id"],
            "receipt_ids": [receipt["receipt_id"]],
            "ref": ref,
            "gap": str(gap),
            "detail": invoice["supplier"] + " was paid " + str(receipt["amount"]) + " of " + str(invoice["amount"]),
        })

shortfall = sum((Decimal(item["gap"]) for item in anomalies if "gap" in item), Decimal("0"))
print(json.dumps({"matches": matches, "anomalies": anomalies, "shortfall": str(shortfall)}))
"""


def bind_sources(source: str, invoices_csv: str, statement_json: str) -> str:
    """Hand the uploaded text to the script as literals. The script cannot open files."""
    import json

    return (
        "INVOICES_CSV = "
        + json.dumps(invoices_csv)
        + "\nSTATEMENT_JSON = "
        + json.dumps(statement_json)
        + "\n"
        + source
    )


class LocalWriter(ScriptModel):
    """Used only when NVIDIA_API_KEY is absent. The scripts still execute."""

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return NAIVE
        return HEALED

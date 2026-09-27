"""Read the synthetic invoice file and the mobile-money statement."""

import csv
import json
from pathlib import Path

from app.parse import parse_amount, parse_date
from app.schema import Invoice, Receipt

ROOT = Path(__file__).resolve().parents[2]
INVOICES = ROOT / "data" / "supplier_invoices.csv"
STATEMENT = ROOT / "data" / "mock_mpesa_statement.json"


def load_invoices(path: Path = INVOICES) -> list[Invoice]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            Invoice(
                invoice_id=row["invoice_id"],
                supplier=row["supplier"],
                amount=parse_amount(row["amount_ksh"]),
                date=parse_date(row["date"]),
                ref=row["ref"],
            )
            for row in csv.DictReader(handle)
        ]


def load_receipts(path: Path = STATEMENT) -> list[Receipt]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [
        Receipt(
            receipt_id=row["receipt_id"],
            ref=row["ref"],
            amount=parse_amount(row["amount"]),
            date=parse_date(row["date"]),
            counterparty=row["counterparty"],
        )
        for row in rows
    ]

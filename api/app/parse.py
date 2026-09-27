"""Turn the messy amount and date cells into values the ledger can add."""

from datetime import date, datetime, timezone
from decimal import Decimal


def parse_amount(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError(f"not an amount: {value!r}")
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip()
    for token in ("KSh", "KES", "ksh"):
        text = text.replace(token, "")
    text = text.replace(",", "").strip()
    if not text:
        raise ValueError(f"not an amount: {value!r}")
    return Decimal(text)


def parse_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, bool):
        raise ValueError(f"not a date: {value!r}")
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().isdigit()):
        stamp = int(value)
        return datetime.fromtimestamp(stamp, tz=timezone.utc).date()
    text = str(value).strip()
    return datetime.strptime(text, "%d/%m/%Y").date()

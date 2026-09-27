from datetime import date
from decimal import Decimal

from app.parse import parse_amount, parse_date


def test_ksh_string_amount():
    assert parse_amount("KSh 4,500") == Decimal("4500")


def test_plain_amount():
    assert parse_amount(13500) == Decimal("13500")


def test_day_first_date():
    assert parse_date("12/03/2026") == date(2026, 3, 12)


def test_unix_timestamp_date():
    assert parse_date(1773273600) == date(2026, 3, 12)

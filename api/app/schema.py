"""The ledger shape the sandbox must return, and the matcher returns too."""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class Invoice(BaseModel):
    invoice_id: str
    supplier: str
    amount: Decimal
    date: date
    ref: str


class Receipt(BaseModel):
    receipt_id: str
    ref: str
    amount: Decimal
    date: date
    counterparty: str


class Match(BaseModel):
    invoice_id: str
    receipt_id: str
    ref: str
    amount: Decimal


class Anomaly(BaseModel):
    kind: Literal["partial", "duplicate_ref", "unmatched_invoice", "unmatched_receipt"]
    invoice_id: str | None = None
    receipt_ids: list[str] = Field(default_factory=list)
    ref: str | None = None
    gap: Decimal | None = None
    detail: str


class Ledger(BaseModel):
    matches: list[Match]
    anomalies: list[Anomaly]
    shortfall: Decimal

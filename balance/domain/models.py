from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True, slots=True)
class Transaction:
    id: int
    date: date
    value: Decimal
    category: str
    type: Literal["income", "expense"] = "expense"
    name: str = ""
    nfe_link: str = ""

@dataclass(frozen=True, slots=True)
class Item:
    transaction_id: int
    item: str
    quantity: Decimal
    unit_value: Decimal
    total_value: Decimal

@dataclass(frozen=True, slots=True)
class Category:
    name: str
    color: str 



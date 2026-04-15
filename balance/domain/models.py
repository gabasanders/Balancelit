from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True, slots=True)
class Transaction:
    occurred_on: date
    value: Decimal
    category: str
    type: Literal["income", "expense"] = "expense"
    name: str = ""

@dataclass(frozen=True, slots=True)
class Category:
    name: str
    type: Literal["income", "expense"]
    color: str = "#000000"



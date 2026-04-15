from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Literal

import pandas as pd

from balance.domain.models import Transaction

def _parse_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    if not s:
        raise ValueError("date is required")
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"invalid date: {s!r}")

def _parse_amount(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    s = str(value).strip()
    if not s:
        raise ValueError("amount is required")
    s = s.replace("R$", "").strip()
    s = s.replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"invalid amount: {value!r}") from e

def _parse_category(value: Any) -> str:
    s = str(value).strip()
    if not s:
        raise ValueError("category is required")
    return s

def _parse_type(value: Any) -> Literal["income", "expense"]:
    s = str(value).strip()
    if not s:
        raise ValueError("type is required")
    return s

def _parse_name(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    return "" if s.lower() == "nan" else s

def transaction_from_row(row: dict[str, Any]) -> Transaction:
    return Transaction(
        occurred_on=_parse_date(row.get("Data")),
        value=_parse_amount(row.get("Valor")),
        category=_parse_category(row.get("Categoria")),
        type=_parse_type(row.get("Tipo")),
        name=_parse_name(row.get("Nome")),
)

def transactions_from_dataframe(df: pd.DataFrame) -> list[Transaction]:
    if df is None or df.empty:
        return []
    required = {"Data", "Valor", "Categoria", "Tipo", "Nome"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
        
    rows = df[list(required)].to_dict(orient="records")
    return [transaction_from_row(r) for r in rows]


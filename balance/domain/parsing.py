from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Literal

import pandas as pd

from balance.domain.models import Category, Transaction, Item

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
    s = str(value).lower().strip()
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
        id=_parse_id(row.get("id")),
        date=_parse_date(row.get("date")),
        value=_parse_amount(row.get("value")),
        category=_parse_category(row.get("category")),
        type=_parse_type(row.get("type")),
        name=_parse_name(row.get("name")),
        nfe_link=_parse_name(row.get("nfe-link", row.get("nfe_link"))),
)

def _parse_id(value: Any) -> int:
    if value is None:
        return 0
    return int(value)

def _parse_color(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "#888888"
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return "#888888"
    if not s.startswith("#") and len(s) in (3, 6) and all(
        c in "0123456789abcdefABCDEF" for c in s
    ):
        s = "#" + s
    return s


def categories_from_dataframe(df: pd.DataFrame) -> list[Category]:
    if df is None or df.empty:
        return []
    lower = {str(c).strip().lower(): c for c in df.columns}
    name_key = lower.get("name")
    if not name_key:
        return []
    color_key = lower.get("color")
    out: list[Category] = []
    for raw in df.to_dict(orient="records"):
        name_val = raw.get(name_key)
        try:
            name = _parse_category(name_val)
        except ValueError:
            continue
        color_raw = raw.get(color_key) if color_key else None
        out.append(Category(name=name, color=_parse_color(color_raw)))
    return out


def transactions_from_dataframe(df: pd.DataFrame) -> list[Transaction]:
    if df is None or df.empty:
        return []
    
    rows = df.to_dict(orient="records")
    return [transaction_from_row(r) for r in rows]

def item_from_row(row: dict[str, Any]) -> Item:
    return Item(
        transaction_id=_parse_id(row.get("transaction_id")),
        item=_parse_name(row.get("item")),
        quantity=_parse_amount(row.get("quantity")),
        unit_value=_parse_amount(row.get("unit_value")),
        total_value=_parse_amount(row.get("total_value")),
    )

def items_from_dataframe(df: pd.DataFrame) -> list[Item]:
    if df is None or df.empty:
        return []
    rows = df.to_dict(orient="records")
    return [item_from_row(r) for r in rows]


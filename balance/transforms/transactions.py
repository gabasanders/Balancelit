from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

import pandas as pd

from balance.domain.models import Transaction


def _item_line(name: str, value: float) -> str:
    n = (name or "").strip()
    return f"{n}: {value:,.2f}" if n else f"{value:,.2f}"


def filter_transactions(
    transactions: list[Transaction],
    start: date,
    end: date,
    categories: list[str] | None,
) -> list[Transaction]:
    out: list[Transaction] = []
    cat_set = set(categories) if categories else None
    for t in transactions:
        if t.date < start or t.date > end:
            continue
        if cat_set is not None and t.category not in cat_set:
            continue
        out.append(t)
    return out


def calculate_balance(transactions: list[Transaction]) -> Decimal:
    income = Decimal(0)
    expenses = Decimal(0)
    for t in transactions:
        if t.type == "income":
            income += t.value
        elif t.type == "expense":
            expenses += t.value
    return income - expenses


def aggregate_expenses_for_chart(
    transactions: list[Transaction],
    view_type: Literal["Yearly", "Monthly"],
) -> pd.DataFrame:
    rows = [
        {"date": t.date, "category": t.category, "value": float(t.value), "name": t.name}
        for t in transactions
        if t.type == "expense"
    ]
    if not rows:
        return pd.DataFrame(columns=["period", "category", "value", "items"])
    df = pd.DataFrame(rows)
    dt = pd.to_datetime(df["date"])
    if view_type == "Yearly":
        df["period"] = dt.dt.to_period("M").astype(str)
    else:
        df["period"] = dt.dt.strftime("%Y-%m-%d")
    df["item_line"] = [_item_line(str(r["name"]), float(r["value"])) for r in rows]
    sums = df.groupby(["period", "category"], as_index=False)["value"].sum()
    items = (
        df.sort_values("value", ascending=False)
        .groupby(["period", "category"], sort=False)["item_line"]
        .agg("<br>".join)
        .reset_index(name="items")
    )
    return sums.merge(items, on=["period", "category"]).sort_values("period")

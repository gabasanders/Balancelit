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


def calculate_income(transactions: list[Transaction]) -> Decimal:
    return sum((t.value for t in transactions if t.type == "income"), Decimal(0))


def calculate_expenses(transactions: list[Transaction]) -> Decimal:
    return sum((t.value for t in transactions if t.type == "expense"), Decimal(0))


def calculate_balance(transactions: list[Transaction]) -> Decimal:
    return calculate_income(transactions) - calculate_expenses(transactions)


def income_transaction_details(
    transactions: list[Transaction],
) -> list[tuple[str, str, Decimal]]:
    return [
        (t.name or "—", str(t.date), t.value)
        for t in transactions
        if t.type == "income"
    ]


def expenses_by_category_breakdown(
    transactions: list[Transaction],
) -> list[tuple[str, Decimal, float]]:
    from collections import defaultdict

    totals: dict[str, Decimal] = defaultdict(Decimal)
    for t in transactions:
        if t.type == "expense":
            totals[t.category] += t.value
    grand = sum(totals.values(), Decimal(0))
    result = [
        (cat, total, float(total / grand * 100) if grand else 0.0)
        for cat, total in totals.items()
    ]
    return sorted(result, key=lambda x: x[1], reverse=True)


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

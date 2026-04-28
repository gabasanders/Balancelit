import pandas as pd
from typing import List

from balance.db.google_sheets import BalanceDatabase
from balance.domain.models import Item
from balance.domain.parsing import items_from_dataframe

def get_all_items(db: BalanceDatabase) -> List[Item]:
    df = db.fetch_all_items()
    if df is None or df.empty:
        return []
    df = df.dropna(how="all")
    return items_from_dataframe(df)

def add_items(db: BalanceDatabase, items: List[Item]) -> None:
    if not items:
        return
    rows = [
        [
            i.transaction_id,
            i.item,
            float(i.quantity),
            float(i.unit_value),
            float(i.total_value),
        ]
        for i in items
    ]
    db.insert_items(rows)

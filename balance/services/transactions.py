import pandas as pd

from balance.db.google_sheets import BalanceDatabase
from balance.domain.models import Transaction
from balance.domain.parsing import transactions_from_dataframe


def list_transactions(db: BalanceDatabase) -> list[Transaction]:
    raw = db.fetch_all_transactions()
    return transactions_from_dataframe(raw)


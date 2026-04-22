from balance.db.google_sheets import BalanceDatabase
from balance.domain.models import Category
from balance.domain.parsing import categories_from_dataframe


def list_categories(db: BalanceDatabase) -> list[Category]:
    raw = db.fetch_all_categories()
    return categories_from_dataframe(raw)

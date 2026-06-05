import streamlit as st
import pandas as pd

from balance.config.settings import get_google_service_account_file, get_google_spreadsheet_name
from balance.db.google_sheets import BalanceDatabase
from balance.services.transactions import list_transactions
from balance.services.items import get_all_items

st.set_page_config(page_title="Items", layout="wide")


@st.cache_resource
def get_db():
    return BalanceDatabase(get_google_service_account_file(), get_google_spreadsheet_name())


db = get_db()


@st.cache_data(ttl=300)
def load_data():
    return list_transactions(db), get_all_items(db)


title_col, refresh_col = st.columns([9, 1])
with title_col:
    st.title("Items")
with refresh_col:
    if st.button("Refresh"):
        load_data.clear()
        st.rerun()

with st.spinner("Loading items..."):
    transactions, items = load_data()

items_df = (
    pd.DataFrame(
        [
            {
                "transaction_id": i.transaction_id,
                "item": i.item,
                "quantity": float(i.quantity),
                "unit_value": float(i.unit_value),
                "total_value": float(i.total_value),
            }
            for i in items
        ]
    )
    if items
    else pd.DataFrame()
)

items_by_tx: dict = {}
if not items_df.empty:
    for tx_id, group in items_df.groupby("transaction_id"):
        items_by_tx[tx_id] = group

shown = 0
for tx in transactions:
    tx_items = items_by_tx.get(tx.id)
    if tx_items is not None and not tx_items.empty:
        shown += 1
        with st.expander(f"{tx.date} — {tx.name} ({tx.category}) · R$ {tx.value:.2f}"):
            tx_total = float(tx.value)
            display_df = tx_items.drop(columns=["transaction_id"]).copy()
            display_df["% of Total"] = (
                (display_df["total_value"] / tx_total * 100).round(2).astype(str) + "%"
                if tx_total > 0
                else "0%"
            )
            st.dataframe(display_df, use_container_width=True, hide_index=True)

if shown == 0:
    st.info("No transactions with items found.")

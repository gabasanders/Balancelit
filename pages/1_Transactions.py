import streamlit as st

from balance.config.settings import (
    get_google_service_account_file,
    get_google_spreadsheet_name,
)
from balance.db.google_sheets import BalanceDatabase
from balance.services.categories import list_categories
from balance.services.transactions import list_transactions
from balance.transforms.transactions import (
    aggregate_expenses_for_chart,
    calculate_balance,
    filter_transactions,
)
from balance.viz.charts import plot_expenses_stacked_bar

st.title("Transactions")

try:
    db = BalanceDatabase(
        get_google_service_account_file(),
        get_google_spreadsheet_name(),
    )
    all_txs = list_transactions(db)
    sheet_categories = list_categories(db)
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

if not all_txs:
    st.info("No transactions.")
    st.stop()

date_list = [t.date for t in all_txs]
d_min, d_max = min(date_list), max(date_list)
categories = sorted({t.category for t in all_txs})

c1, c2 = st.columns(2)
with c1:
    start = st.date_input("Start", value=d_min, min_value=d_min, max_value=d_max)
with c2:
    end = st.date_input("End", value=d_max, min_value=d_min, max_value=d_max)

if start > end:
    st.warning("Start date must be on or before end date.")
    st.stop()

selected = st.multiselect("Categories", options=categories, default=categories)
if not selected:
    st.warning("Select at least one category.")
    st.stop()

view_type = st.radio("View", ["Monthly","Yearly"], horizontal=True)

filtered = filter_transactions(all_txs, start, end, selected)
bal = calculate_balance(filtered)
st.metric("Balance (income − expenses)", f"{bal:,.2f}")

chart_df = aggregate_expenses_for_chart(filtered, view_type)
category_colors = {c.name: c.color for c in sheet_categories}
st.plotly_chart(
    plot_expenses_stacked_bar(chart_df, view_type, category_colors),
    use_container_width=True,
)

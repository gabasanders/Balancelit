import streamlit as st
from datetime import date
from decimal import Decimal

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
    calculate_income,
    calculate_expenses,
    expenses_by_category_breakdown,
    filter_transactions,
    income_transaction_details,
)
from balance.viz.charts import plot_expenses_stacked_bar

st.title("Transactions")

with st.spinner("Loading transactions..."):
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

today = date.today()
month_start = today.replace(day=1)
default_start = max(min(month_start, d_max), d_min)
default_end = max(min(today, d_max), default_start)

c1, c2 = st.columns(2)
with c1:
    start = st.date_input(
        "Start", value=default_start, min_value=d_min, max_value=d_max
    )
with c2:
    end = st.date_input("End", value=default_end, min_value=d_min, max_value=d_max)

if start > end:
    st.warning("Start date must be on or before end date.")
    st.stop()

selected = st.multiselect("Categories", options=categories, default=categories)
if not selected:
    st.warning("Select at least one category.")
    st.stop()

view_type = st.radio("View", ["Monthly", "Yearly"], horizontal=True)

with st.spinner("Calculating..."):
    filtered = filter_transactions(all_txs, start, end, selected)
    bal = calculate_balance(filtered)
    income = calculate_income(filtered)
    expenses = calculate_expenses(filtered)
    income_details = income_transaction_details(filtered)
    expenses_cats = expenses_by_category_breakdown(filtered)
    chart_df = aggregate_expenses_for_chart(filtered, view_type)
    category_colors = {c.name: c.color for c in sheet_categories}


def _summary_cards_html(
    bal: Decimal,
    income: Decimal,
    expenses: Decimal,
    income_details: list[tuple[str, str, Decimal]],
    expenses_cats: list[tuple[str, Decimal, float]],
) -> str:
    bal_color = "#4ade80" if bal >= 0 else "#f87171"

    income_rows = "".join(
        f"<tr><td>{name}</td><td class='date'>{date}</td>"
        f"<td class='num'>{float(val):,.2f}</td></tr>"
        for name, date, val in income_details
    ) or "<tr><td colspan='3' class='empty'>No income transactions</td></tr>"

    expense_rows = "".join(
        f"<tr><td>{cat}</td><td class='num'>{float(total):,.2f}</td>"
        f"<td class='num pct'>{pct:.1f}%</td></tr>"
        for cat, total, pct in expenses_cats
    ) or "<tr><td colspan='3' class='empty'>No expenses</td></tr>"

    return f"""
<style>
  .bc-wrap {{
    display: flex;
    gap: 14px;
    margin-bottom: 1.5rem;
  }}
  .bc-card {{
    flex: 1;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 14px 18px 16px;
    position: relative;
    cursor: default;
    transition: border-color 0.15s;
  }}
  .bc-card:hover {{
    border-color: rgba(255,255,255,0.25);
  }}
  .bc-label {{
    font-size: 0.72rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-weight: 600;
  }}
  .bc-value {{
    display: block;
    font-size: 1.8rem;
    font-weight: 700;
    margin-top: 4px;
    letter-spacing: -0.02em;
  }}
  .bc-hint {{
    font-size: 0.68rem;
    color: #555;
    margin-top: 6px;
  }}
  .bc-tooltip {{
    display: none;
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    z-index: 1000;
    background: #16161e;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px;
    padding: 10px 14px;
    min-width: 320px;
    max-height: 280px;
    overflow-y: auto;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    scrollbar-width: thin;
  }}
  .bc-card:hover .bc-tooltip {{
    display: block;
  }}
  .bc-tooltip table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
  }}
  .bc-tooltip th {{
    color: #666;
    font-weight: 600;
    padding: 4px 6px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    text-align: left;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .bc-tooltip td {{
    padding: 5px 6px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    color: #ccc;
  }}
  .bc-tooltip td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .bc-tooltip td.date {{ color: #666; font-size: 0.72rem; }}
  .bc-tooltip td.pct {{ color: #888; }}
  .bc-tooltip td.empty {{ color: #555; text-align: center; padding: 12px 0; }}
  .bc-tooltip-title {{
    font-size: 0.72rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 6px;
    font-weight: 600;
  }}
</style>
<div class="bc-wrap">
  <div class="bc-card">
    <span class="bc-label">Balance</span>
    <span class="bc-value" style="color:{bal_color}">{float(bal):+,.2f}</span>
  </div>

  <div class="bc-card">
    <span class="bc-label">Income</span>
    <span class="bc-value" style="color:#4ade80">{float(income):,.2f}</span>
    <div class="bc-hint">Hover to see transactions</div>
    <div class="bc-tooltip">
      <div class="bc-tooltip-title">Income Transactions</div>
      <table>
        <thead><tr><th>Name</th><th>Date</th><th style="text-align:right">Amount</th></tr></thead>
        <tbody>{income_rows}</tbody>
      </table>
    </div>
  </div>

  <div class="bc-card">
    <span class="bc-label">Expenses</span>
    <span class="bc-value" style="color:#f87171">{float(expenses):,.2f}</span>
    <div class="bc-hint">Hover to see by category</div>
    <div class="bc-tooltip" style="left:auto;right:0">
      <div class="bc-tooltip-title">Expenses by Category</div>
      <table>
        <thead><tr><th>Category</th><th style="text-align:right">Total</th><th style="text-align:right">%</th></tr></thead>
        <tbody>{expense_rows}</tbody>
      </table>
    </div>
  </div>
</div>
"""


st.markdown(
    _summary_cards_html(bal, income, expenses, income_details, expenses_cats),
    unsafe_allow_html=True,
)

with st.spinner("Rendering chart..."):
    st.plotly_chart(
        plot_expenses_stacked_bar(chart_df, view_type, category_colors),
        use_container_width=True,
    )

import streamlit as st
from balance.config.settings import (
    get_google_service_account_file,
    get_google_spreadsheet_name,
)
from balance.db.google_sheets import BalanceDatabase
from balance.viz.charts import plot_recurring_waterfall

st.set_page_config(page_title="Recurring Expenses", page_icon="🔁", layout="wide")
st.title("Recurring Expenses")

@st.cache_data(ttl=600)
def fetch_data():
    db = BalanceDatabase(
        get_google_service_account_file(),
        get_google_spreadsheet_name(),
    )
    try:
        df_rec = db.fetch_all_recurring()
        return df_rec
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

df_rec = fetch_data()

if df_rec is not None and not df_rec.empty:
    fig = plot_recurring_waterfall(df_rec)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No recurring expenses found. You can add them in the 'Add Info' page.")

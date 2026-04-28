import streamlit as st
import pandas as pd
from decimal import Decimal

from balance.config.settings import get_google_service_account_file, get_google_spreadsheet_name
from balance.db.google_sheets import BalanceDatabase
from balance.services.transactions import list_transactions
from balance.services.items import get_all_items, add_items
from balance.services.nfe_scrape import extract_nfce_data
from balance.domain.models import Item

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

mode = st.radio("", ["Analysis", "Add NFE"], horizontal=True)

transactions, items = load_data()

if mode == "Analysis":
    items_df = pd.DataFrame([{
        "transaction_id": i.transaction_id,
        "item": i.item,
        "quantity": float(i.quantity),
        "unit_value": float(i.unit_value),
        "total_value": float(i.total_value),
    } for i in items]) if items else pd.DataFrame()

    items_by_tx = {}
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
                    if tx_total > 0 else "0%"
                )
                st.dataframe(display_df, use_container_width=True, hide_index=True)

    if shown == 0:
        st.info("No transactions with items found.")

else:  # Add NFE
    recent_txs = sorted(transactions, key=lambda x: x.date, reverse=True)[:20]
    items_tx_ids = {i.transaction_id for i in items}

    link_entries = {}
    for tx in recent_txs:
        c1, c2, c3 = st.columns([3, 5, 1])
        with c1:
            st.markdown(f"**{tx.date}** — {tx.name}")
        with c3:
            st.markdown(f"R$ {tx.value:.2f}")
        with c2:
            link = st.text_input(
                "link",
                value=tx.nfe_link or "",
                key=f"nfe_{tx.id}",
                label_visibility="collapsed",
                placeholder="NFe link...",
            )
            if link:
                link_entries[tx.id] = link

    pending = {tx_id: lnk for tx_id, lnk in link_entries.items() if lnk}

    if pending:
        duplicates = [tx_id for tx_id in pending if tx_id in items_tx_ids]
        confirmed = True

        if duplicates:
            dup_labels = [
                f"{tx.date} - {tx.name}" for tx in recent_txs if tx.id in duplicates
            ]
            st.warning(
                "The following transactions already have items: "
                + ", ".join(dup_labels)
                + ". Uploading will add duplicate entries."
            )
            confirmed = st.checkbox("Proceed anyway")

        if st.button("Upload") and confirmed:
            all_new_items = []
            errors = []
            with st.spinner("Processing NFe links..."):
                for tx_id, link in pending.items():
                    tx = next((t for t in recent_txs if t.id == tx_id), None)
                    if not tx:
                        continue
                    try:
                        db.update_transaction_nfe_link(tx_id, link)
                    except Exception as e:
                        errors.append(f"nfe_link update failed for {tx.name}: {e}")

                    scraped = extract_nfce_data(link)
                    if not scraped:
                        errors.append(f"No items extracted from {tx.name}")
                        continue

                    for data in scraped:
                        try:
                            all_new_items.append(Item(
                                transaction_id=tx_id,
                                item=data["product"],
                                quantity=Decimal(data["qty"].replace(",", ".")),
                                unit_value=Decimal(data["unit_price"].replace(",", ".")),
                                total_value=Decimal(data["total"].replace(",", ".")),
                            ))
                        except Exception as e:
                            errors.append(f"Parse error for {data.get('product', '?')}: {e}")

            if all_new_items:
                try:
                    add_items(db, all_new_items)
                    st.success(f"Added {len(all_new_items)} items!")
                    load_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Upload failed: {e}")

            for err in errors:
                st.warning(err)

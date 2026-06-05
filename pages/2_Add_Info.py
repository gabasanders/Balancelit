import json
import os
from decimal import Decimal

import streamlit as st

from balance.config.settings import (
    get_google_service_account_file,
    get_google_spreadsheet_name,
)
from balance.db.google_sheets import BalanceDatabase
from balance.domain.models import Item
from balance.services.items import add_items, get_all_items
from balance.services.nfe_scrape import extract_nfce_data
from balance.services.transactions import list_transactions

st.title("Add Info")

MEMORY_FILE = "local_entries.json"


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f)


def clear_memory():
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)


if "memory" not in st.session_state:
    st.session_state.memory = load_memory()

db = BalanceDatabase(
    get_google_service_account_file(),
    get_google_spreadsheet_name(),
)


@st.cache_data(ttl=600)
def get_categories():
    try:
        df = db.fetch_all_categories()
        if not df.empty and "name" in df.columns:
            return df["name"].dropna().tolist()
    except Exception:
        raise Exception("Could not fetch categories")
    return []


@st.cache_data(ttl=300)
def get_nfe_data():
    txs = list_transactions(db)
    items = get_all_items(db)
    items_tx_ids = {i.transaction_id for i in items}
    no_nfe = sorted(
        [t for t in txs if not t.nfe_link],
        key=lambda t: t.date,
        reverse=True,
    )
    return no_nfe, items_tx_ids


categories = get_categories()

entry_type = st.radio(
    "Select entry type",
    ["Transactions", "Categories", "Recurring", "Add NFE"],
    horizontal=True,
)

# ── Add NFE tab ──────────────────────────────────────────────────────────────
if entry_type == "Add NFE":
    title_col, refresh_col = st.columns([9, 1])
    with title_col:
        st.subheader("Link NFe receipts to transactions")
    with refresh_col:
        if st.button("Refresh"):
            get_nfe_data.clear()
            st.rerun()

    no_nfe_txs, items_tx_ids = get_nfe_data()

    if not no_nfe_txs:
        st.info("All transactions already have NFe links!")
    else:
        link_entries: dict[int, str] = {}
        for tx in no_nfe_txs:
            c1, c2, c3 = st.columns([3, 5, 1])
            with c1:
                st.markdown(f"**{tx.date}** — {tx.name} ({tx.category})")
            with c3:
                st.markdown(f"R$ {tx.value:.2f}")
            with c2:
                link = st.text_input(
                    "link",
                    key=f"nfe_{tx.id}",
                    label_visibility="collapsed",
                    placeholder="NFe link...",
                )
                if link:
                    link_entries[tx.id] = link

        pending = {tx_id: lnk for tx_id, lnk in link_entries.items() if lnk}

        if pending:
            tx_map = {t.id: t for t in no_nfe_txs}
            duplicates = [tx_id for tx_id in pending if tx_id in items_tx_ids]
            confirmed = True

            if duplicates:
                dup_labels = [
                    f"{tx_map[tid].date} – {tx_map[tid].name}"
                    for tid in duplicates
                    if tid in tx_map
                ]
                st.warning(
                    "These transactions already have items: "
                    + ", ".join(dup_labels)
                    + ". Uploading will add duplicate entries."
                )
                confirmed = st.checkbox("Proceed anyway", key="nfe_confirm")

            if st.button("Upload", key="nfe_upload") and confirmed:
                all_new_items: list[Item] = []
                errors: list[str] = []
                with st.spinner("Processing NFe links..."):
                    for tx_id, link in pending.items():
                        tx = tx_map.get(tx_id)
                        if not tx:
                            continue
                        try:
                            db.update_transaction_nfe_link(tx_id, link)
                        except Exception as e:
                            errors.append(f"nfe_link update failed for {tx.name}: {e}")

                        scraped = extract_nfce_data(link)
                        if not scraped:
                            errors.append(f"No items extracted for {tx.name}")
                            continue

                        for data in scraped:
                            try:
                                all_new_items.append(
                                    Item(
                                        transaction_id=tx_id,
                                        item=data["product"],
                                        quantity=Decimal(
                                            str(data["qty"]).replace(",", ".")
                                        ),
                                        unit_value=Decimal(
                                            str(data["unit_price"]).replace(",", ".")
                                        ),
                                        total_value=Decimal(
                                            str(data["total"]).replace(",", ".")
                                        ),
                                    )
                                )
                            except Exception as e:
                                errors.append(
                                    f"Parse error for {data.get('product', '?')}: {e}"
                                )

                if all_new_items:
                    try:
                        add_items(db, all_new_items)
                        st.success(f"Added {len(all_new_items)} items!")
                        get_nfe_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {e}")

                for err in errors:
                    st.warning(err)

# ── Transactions / Categories / Recurring tabs ───────────────────────────────
else:
    with st.form("add_form"):
        if entry_type == "Transactions":
            col1, col2 = st.columns(2)
            with col1:
                date_input = st.date_input("Date")
                category_input = st.selectbox("Category", categories)
                type_input = st.selectbox("Type", ["expense", "income"])
            with col2:
                name_input = st.text_input("Name")
                value_input = st.number_input("Value", min_value=0.0, step=0.01)
                nfe_link_input = st.text_input("NFE-link")
        elif entry_type == "Categories":
            col1, col2 = st.columns(2)
            with col1:
                cat_name_input = st.text_input("Name")
            with col2:
                color_input = st.color_picker("Color", "#00f900")
        elif entry_type == "Recurring":
            col1, col2 = st.columns(2)
            with col1:
                rec_category_input = st.selectbox("Category", categories)
                rec_type_input = st.selectbox("Type", ["expense", "income"])
            with col2:
                rec_name_input = st.text_input("Name")
                rec_value_input = st.number_input("Value", min_value=0.0, step=0.01)

        add_btn = st.form_submit_button("Add to List")

    if add_btn:
        if entry_type == "Transactions":
            entry = {
                "type_entry": "transaction",
                "date": date_input.strftime("%d/%m/%Y"),
                "category": category_input,
                "type": type_input,
                "name": name_input,
                "value": float(value_input),
                "nfe-link": nfe_link_input,
            }
        elif entry_type == "Categories":
            entry = {
                "type_entry": "category",
                "name": cat_name_input,
                "color": color_input,
            }
        elif entry_type == "Recurring":
            entry = {
                "type_entry": "recurring",
                "name": rec_name_input,
                "category": rec_category_input,
                "type": rec_type_input,
                "value": float(rec_value_input),
            }
        st.session_state.memory.append(entry)
        save_memory(st.session_state.memory)
        st.success("Added to local list!")

    if st.session_state.memory:
        st.write("### Pending Entries")
        st.table(st.session_state.memory)

        if st.button("Upload"):
            try:
                txs = [
                    e for e in st.session_state.memory if e.get("type_entry") == "transaction"
                ]
                cats = [
                    e for e in st.session_state.memory if e.get("type_entry") == "category"
                ]
                recs = [
                    e for e in st.session_state.memory if e.get("type_entry") == "recurring"
                ]

                tx_with_nfe: list[tuple[int, str, str]] = []  # (tx_id, nfe_link, name)

                if txs:
                    df = db.fetch_all_transactions()
                    max_id = (
                        int(df["id"].max())
                        if not df.empty
                        and "id" in df.columns
                        and not df["id"].isna().all()
                        else 0
                    )
                    rows_to_insert = []
                    for entry in txs:
                        max_id += 1
                        rows_to_insert.append(
                            [
                                max_id,
                                entry["date"],
                                entry["category"],
                                entry["name"],
                                entry["type"],
                                entry["value"],
                                entry["nfe-link"],
                            ]
                        )
                        if entry.get("nfe-link"):
                            tx_with_nfe.append((max_id, entry["nfe-link"], entry["name"]))
                    db.insert_transactions(rows_to_insert)

                if cats:
                    df_cats = db.fetch_all_categories()
                    max_cat_id = (
                        int(df_cats["id"].max())
                        if not df_cats.empty
                        and "id" in df_cats.columns
                        and not df_cats["id"].isna().all()
                        else 0
                    )
                    rows_to_insert = []
                    for entry in cats:
                        max_cat_id += 1
                        rows_to_insert.append([max_cat_id, entry["name"], entry["color"]])
                    db.insert_categories(rows_to_insert)
                    st.cache_data.clear()

                if recs:
                    rows_to_insert = [
                        [e["name"], e["category"], e["type"], e["value"]] for e in recs
                    ]
                    db.insert_recurring(rows_to_insert)

                clear_memory()
                st.session_state.memory = []
                st.success("Successfully uploaded!")

                # Auto-process NFe links from newly added transactions
                if tx_with_nfe:
                    all_new_items: list[Item] = []
                    nfe_errors: list[str] = []
                    with st.spinner("Processing NFe links..."):
                        for tx_id, nfe_link, tx_name in tx_with_nfe:
                            scraped = extract_nfce_data(nfe_link)
                            if not scraped:
                                nfe_errors.append(f"No items extracted for {tx_name}")
                                continue
                            for data in scraped:
                                try:
                                    all_new_items.append(
                                        Item(
                                            transaction_id=tx_id,
                                            item=data["product"],
                                            quantity=Decimal(
                                                str(data["qty"]).replace(",", ".")
                                            ),
                                            unit_value=Decimal(
                                                str(data["unit_price"]).replace(",", ".")
                                            ),
                                            total_value=Decimal(
                                                str(data["total"]).replace(",", ".")
                                            ),
                                        )
                                    )
                                except Exception as e:
                                    nfe_errors.append(
                                        f"Parse error for {data.get('product', '?')}: {e}"
                                    )
                    if all_new_items:
                        try:
                            add_items(db, all_new_items)
                            st.success(
                                f"Auto-added {len(all_new_items)} items from NFe links!"
                            )
                        except Exception as e:
                            st.error(f"Items upload failed: {e}")
                    for err in nfe_errors:
                        st.warning(err)

                st.rerun()
            except Exception as e:
                st.error(f"Error uploading: {e}")

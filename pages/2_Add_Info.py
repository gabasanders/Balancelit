import json
import os
import streamlit as st
import pandas as pd
from balance.config.settings import (
    get_google_service_account_file,
    get_google_spreadsheet_name,
)
from balance.db.google_sheets import BalanceDatabase

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
    

categories = get_categories()

entry_type = st.radio("Select entry type", ["Transactions", "Categories", "Recurring"], horizontal=True)

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
            "nfe-link": nfe_link_input
        }
    elif entry_type == "Categories":
        entry = {
            "type_entry": "category",
            "name": cat_name_input,
            "color": color_input
        }
    elif entry_type == "Recurring":
        entry = {
            "type_entry": "recurring",
            "name": rec_name_input,
            "category": rec_category_input,
            "type": rec_type_input,
            "value": float(rec_value_input)
        }
    st.session_state.memory.append(entry)
    save_memory(st.session_state.memory)
    st.success("Added to local list!")

if st.session_state.memory:
    st.write("### Pending Entries")
    st.table(st.session_state.memory)
    
    if st.button("Upload"):
        try:
            txs = [e for e in st.session_state.memory if e.get("type_entry") == "transaction"]
            cats = [e for e in st.session_state.memory if e.get("type_entry") == "category"]
            recs = [e for e in st.session_state.memory if e.get("type_entry") == "recurring"]

            if txs:
                df = db.fetch_all_transactions()
                max_id = int(df["id"].max()) if not df.empty and "id" in df.columns and not df["id"].isna().all() else 0
                
                rows_to_insert = []
                for entry in txs:
                    max_id += 1
                    rows_to_insert.append([
                        max_id,
                        entry["date"],
                        entry["category"],
                        entry["name"],
                        entry["type"],
                        entry["value"],
                        entry["nfe-link"]
                    ])
                db.insert_transactions(rows_to_insert)

            if cats:
                df_cats = db.fetch_all_categories()
                max_cat_id = int(df_cats["id"].max()) if not df_cats.empty and "id" in df_cats.columns and not df_cats["id"].isna().all() else 0

                rows_to_insert = []
                for entry in cats:
                    max_cat_id += 1
                    rows_to_insert.append([
                        max_cat_id,
                        entry["name"],
                        entry["color"]
                    ])
                db.insert_categories(rows_to_insert)
                st.cache_data.clear()

            if recs:
                rows_to_insert = []
                for entry in recs:
                    rows_to_insert.append([
                        entry["name"],
                        entry["category"],
                        entry["type"],
                        entry["value"]
                    ])
                db.insert_recurring(rows_to_insert)

            clear_memory()
            st.session_state.memory = []
            st.success("Successfully uploaded!")
            st.rerun()
        except Exception as e:
            st.error(f"Error uploading: {e}")

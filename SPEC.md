## 1. Project Overview
**Flux-Ledger** is a cloud-based personal finance management system built with **Python** and **Streamlit**. It uses **Google Sheets** as a serverless backend to ensure data accessibility across different devices while maintaining a "Zero-Cost" infrastructure.

### Tech Stack:
* **Frontend:** Streamlit
* **Backend:** Google Sheets API (via `gspread`)
* **Data Processing:** Pandas
* **Visualization:** Plotly
* **IDE:** Cursor AI

---

## 2. Data Architecture (Google Sheets)
The database consists of four tables (worksheets):

* **`Transactions`**: The primary ledger.
    * Columns: `id`, `date`, `category`, `name`, `type`, `value`, 'nfe-link'
* **`Recurring`**: Definitions for fixed monthly costs.
    * Columns: `name`, `category`, `type`, `var`, `max`, `min`.

---

## 3. Page Specifications

### Page 1: Transactions Page
Goal: Provide a real-time transactions page to understand all the incomes and outcomes in a given period of time.

* **Core Calculation:**
    `Balance = Income - Expenses`
* **Must have:**
    1. Stacked Bar Graph showing the amount spent with: 
     - Date filters and Category filters
     - Categories represent different colors in the same bar.
     - Yearly (bars are months) and monthly (bars are days) view. Should be able to toggle between them



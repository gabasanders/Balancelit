import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe


class BalanceDatabase:
    def __init__(self, service_account_file: str, spreadsheet_name: str):
        self.service_file = service_account_file
        self.spreadsheet_name = spreadsheet_name

    def _open_sheet(self, index=0):
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(self.service_file, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open(self.spreadsheet_name).get_worksheet(index)

    def fetch_all_transactions(self):
        try:
            return get_as_dataframe(self._open_sheet(0))
        except Exception as e:
            raise Exception(f"Error fetching transactions: {e}")

    def insert_transactions(self, rows):
        self._open_sheet(0).append_rows(rows)

    def fetch_all_categories(self):
        try:
            return get_as_dataframe(self._open_sheet(1))
        except Exception as e:
            raise Exception(f"Error fetching categories: {e}")

    def insert_categories(self, rows):
        self._open_sheet(1).append_rows(rows)

    def fetch_all_recurring(self):
        try:
            return get_as_dataframe(self._open_sheet(2))
        except Exception as e:
            raise Exception(f"Error fetching recurring: {e}")

    def insert_recurring(self, rows):
        self._open_sheet(2).append_rows(rows)

    def fetch_all_items(self):
        try:
            return get_as_dataframe(self._open_sheet(3))
        except Exception as e:
            raise Exception(f"Error fetching items: {e}")

    def insert_items(self, rows):
        self._open_sheet(3).append_rows(rows)

    def update_transaction_nfe_link(self, tx_id: int, nfe_link: str) -> None:
        sheet = self._open_sheet(0)
        headers = sheet.row_values(1)
        col_idx = next(
            (i + 1 for i, h in enumerate(headers) if h.lower().strip() in ("nfe-link", "nfe_link")),
            None,
        )
        if col_idx is None:
            raise ValueError("nfe_link column not found in Transactions sheet")
        id_col = sheet.col_values(1)
        row_idx = next(
            (i + 2 for i, val in enumerate(id_col[1:]) if str(val).strip() == str(tx_id)),
            None,
        )
        if row_idx is None:
            raise ValueError(f"Transaction ID {tx_id} not found")
        sheet.update_cell(row_idx, col_idx, nfe_link)


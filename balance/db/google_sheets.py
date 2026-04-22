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


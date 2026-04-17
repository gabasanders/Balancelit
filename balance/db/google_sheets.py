import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe


class BalanceDatabase:
    def __init__(self, service_account_file: str, spreadsheet_name: str):
        self.service_file = service_account_file
        self.spreadsheet_name = spreadsheet_name

    def _open_first_sheet(self):
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(self.service_file, scopes=scopes)
        client = gspread.authorize(creds)
        print(f"Opening spreadsheet: {self.spreadsheet_name}")
        print(f"Client: {client}")
        return client.open(self.spreadsheet_name).sheet1

    def fetch_all_transactions(self):
        try:
            sheet = self._open_first_sheet()
            return get_as_dataframe(sheet)
        except Exception as e:
            raise Exception(f"Error fetching all transactions: {e}")

    def insert_transaction(self, data, valor, categoria, descricao):
        sheet = self._open_first_sheet()
        sheet.append_row([data, valor, categoria, descricao])
        return None


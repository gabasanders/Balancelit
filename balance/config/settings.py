import os


def get_google_service_account_file() -> str:
    return os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"]


def get_google_spreadsheet_name() -> str:
    return os.environ["GOOGLE_SPREADSHEET_NAME"]


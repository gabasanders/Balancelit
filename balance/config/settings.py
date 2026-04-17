import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(_ROOT / ".env")


_maybe_load_dotenv()


def get_google_service_account_file() -> str:
    v = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not v:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_FILE is not set. "
            "Export it in your shell, add it to a .env file in the project root, "
            "or install python-dotenv so .env is loaded automatically (pip install python-dotenv)."
        )
    return v


def get_google_spreadsheet_name() -> str:
    v = os.getenv("GOOGLE_SPREADSHEET_NAME")
    if not v:
        raise RuntimeError(
            "GOOGLE_SPREADSHEET_NAME is not set. "
            "Export it or add it to .env in the project root."
        )
    return v

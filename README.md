# Balance

Personal finance tracker built with Streamlit (UI) + Python (backend) and Google Sheets (database via `gspread`).

## Architecture

- `app.py`: Streamlit entrypoint
- `pages/`: Streamlit pages (UI)
- `balance/`: core package
  - `balance/db/`: Google Sheets access (gspread)
  - `balance/domain/`: domain models + parsing/normalization
  - `balance/services/`: use-cases called by the UI
  - `balance/transforms/`: pandas transformations/aggregations
  - `balance/viz/`: Plotly chart builders
  - `balance/config/`: settings + constants

Compatibility wrappers remain at repo root (`database.py`, `transformations.py`, `constants.py`) to preserve older imports.

## Configuration

Create a local `.env` (not committed) or export environment variables:

- `GOOGLE_SERVICE_ACCOUNT_FILE`: absolute path to your Google service account JSON
- `GOOGLE_SPREADSHEET_NAME`: Google Sheets spreadsheet name (e.g. `FINANÇAS`)

See `.env.example`.

## Run

```bash
streamlit run app.py
```

## Security

Do not commit Google service account credentials. Keep the JSON key outside the repo (or in a local ignored folder).

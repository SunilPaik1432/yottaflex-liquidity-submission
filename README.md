# YottaFlex Liquidity Forecasting & Risk Analytics Platform

A learning prototype for exploring synthetic treasury data, due-date cash flow forecasts, and basic liquidity risk indicators. All generated values are demo data; exchange rates are synthetic and are not live market rates.

## Current project status

- 11 SQLite tables are defined in `database/schema.py`.
- `database/liquidity.db` contains 30 legal entities, 150 bank accounts, 100,000 ledger entries, 3,000 receivables, 3,000 payables, 20 synthetic FX pairs, 1 base scenario, 1 forecast run, and 579 cash flow forecast rows.
- `src/generate_data.py` creates the seed data without deleting existing rows.
- `src/forecast_summary.py` prints forecast totals by date and currency.
- `src/risk_analytics.py` reports overdue exposures and negative-flow days by currency.
- `app.py` is an interactive Streamlit dashboard with an executive overview, forecast and risk tabs, live controls, scenario overlays, projected balances, CSV report downloads, and a 3D liquidity landscape.

Amounts are kept separate by currency. Do not add amounts from different currencies unless they have first been converted using an appropriate exchange rate.

## Setup

Run these commands from the repository root.

```powershell
$PythonExe = "python"
& $PythonExe -m pip install -r requirements.txt
```

## Run the project

### 1. Generate a fresh synthetic dataset

```powershell
& $PythonExe src/generate_dataset.py --db database/liquidity-full.db --scale full
& $PythonExe src/generate_dataset.py --db database/liquidity-starter.db --scale starter
```

Use a new path for each run. The generator refuses to overwrite an existing
database. The default seed is `20261022`. The full profile contains 30 entities,
150 accounts, 100,000 ledger entries and 20,000 forecast items. The starter
profile contains 5 entities, 25 accounts, 1,000 ledger entries and 200 forecast
items. Both use five currencies and report overdue obligations separately.

To preview a generated database in the dashboard, set the environment variable
before starting Streamlit. Leave it unset to use the original database.

```powershell
$env:YOTTAFLEX_DB_PATH = (Resolve-Path database/liquidity-full.db).Path
& $PythonExe -m streamlit run app.py
```

### 2. Print forecast summary

```powershell
& $PythonExe src\forecast_summary.py
```

This reports inflow, outflow, and net flow grouped by forecast date and currency, followed by totals for each currency.

### 3. Print risk indicators

```powershell
& $PythonExe src\risk_analytics.py
```

This reports overdue receivables and payables, plus the number and total value of negative-flow forecast days for each currency. A negative-flow day is a warning indicator, not proof of insolvency.

### 4. Open the interactive dashboard

```powershell
& $PythonExe -m streamlit run app.py
```

If Streamlit asks for an email address the first time, leave it blank and press Enter. Open the local URL printed in the terminal. Keep that terminal open while using the dashboard; press `Ctrl+C` there to stop it.

## Main files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit dashboard |
| `database/schema.py` | SQLite table definitions |
| `database/db.py` | SQLite connection helper |
| `src/generate_data.py` | Deterministic synthetic seed data |
| `src/forecast_summary.py` | Date and currency forecast summary |
| `src/risk_analytics.py` | Overdue exposure and shortfall indicators |
| `database/liquidity.db` | Local SQLite database |

## Current limitations

- The main forecast uses unpaid receivable and payable due dates. Forecast Lab adds a 90-day weekday-average ledger baseline; no trained predictive model is used.
- Projected cash positions are shown in consolidated INR and separately in each source currency; they start from opening balances plus ledger movements before the 2026-11-10 cutoff.
- FX rates and financial records are synthetic demonstration values.
- Forecast and risk reports retain source-currency detail. The dashboard also shows a consolidated INR forecast using synthetic rates; overdue risk exposures are not converted to INR.
- Forecast Lab compares Base, Delayed Receipt (receipts 7 calendar days later), Stress (10% lower inflows and 20% higher outflows), and adjustable Upside and Downside. All scenarios use the same opening cash and cutoff FX rates. The save button stores each run's assumptions and daily INR flows as new records.
- Run the database and generator checks with `python -m pytest`.

## Actual vs forecast

Generate a fresh starter or full database and open **Forecast Lab → Actual vs
forecast**. The comparison covers the full dataset. It pairs each forecast with
one synthetic settlement and leaves the original forecast intact. Selected
receipts arrive five days late and every eleventh settlement is 5% below the
forecast amount. All settlements occur after the cutoff.

Amount effect uses cutoff FX. FX effect uses the difference between settlement
and cutoff FX on the actual amount. Together they explain the signed net cash
variance. The daily chart uses the forecast and settlement dates to show timing
differences. The CSV includes all matched rows and the settlement IDs.

## Submission data

From the project root, run:

```powershell
& $PythonExe -m src.export_submission --output exports/submission --scale full
& $PythonExe -m pytest
```

Use a new output directory. The export includes one CSV per SQLite table,
a source manifest, and a validation summary. The validation generates the
dataset twice and compares ordered row counts and SHA-256 checksums for
each table. `exception_cases.json` contains the five negative inputs.
`ground_truth.json` maps their case IDs to expected findings.

## Streamlit Community Cloud

Set the main file path to `streamlit_app.py`. That entry point creates a full
synthetic database when the process starts, so visitors can try Actual vs
Forecast without a data upload. Saved scenario runs are stored in that
instance's temporary database and can reset when the instance restarts.

The checked-in [submission data](submission/) includes the CSV seed files,
labelled exception cases, ground truth, manifest and validation summary.
See [design and validation](docs/design.md) for the model choices and
[AI assistance](docs/ai-assistance.md) for the available project prompt record.

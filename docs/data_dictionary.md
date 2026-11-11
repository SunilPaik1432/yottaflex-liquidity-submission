# Data Dictionary — YottaFlex Liquidity Forecasting System

This document outlines the schema, field types, constraints, and validation rules for all 10 core tables in the SQLite store (`liquidity.db`).

---

### 1. `legal_entities`
Monitored corporate subsidiaries.
- `entity_id` (TEXT, PK): Unique identifier formatted as `ENT-XXXXXX`.
- `entity_name` (TEXT, Required): Registered operating name.
- `country` (TEXT, Required): Territory code (USA, GBR, EUR, JPN, SGP).
- `base_currency` (TEXT, Required): Functional currency (USD, EUR, GBP, JPY, SGD).
- `status` (TEXT, Required): `ACTIVE` or `DORMANT`.
- `created_at` (TEXT, Required): Record creation timestamp.

---

### 2. `bank_accounts`
Operating treasury bank accounts.
- `account_id` (TEXT, PK): Formatted as `BANKACC-ENT-XXXXXX-XXX`.
- `entity_id` (TEXT, FK): References `legal_entities.entity_id`.
- `bank_name` (TEXT, Required): Custodian financial institution.
- `account_number` (TEXT, Required): External bank account number.
- `currency` (TEXT, Required): Currency code.
- `opening_balance` (REAL, Required): Initial starting balance.
- `closing_balance` (REAL, Optional): Ledger-reconciled current balance.
- `status` (TEXT, Required): `ACTIVE` or `FROZEN`.

---

### 3. `ledger_entries`
Actual historical transactions.
- `ledger_id` (TEXT, PK): Identifier formatted as `LED-YYYY-XXXXXXXX`.
- `account_id` (TEXT, FK): References `bank_accounts.account_id`.
- `transaction_date` (TEXT, Required): Date of transaction (`YYYY-MM-DD`).
- `description` (TEXT, Optional): Narration/memo.
- `entry_type` (TEXT, Required): `SWEEP`, `PAYMENT`, `RECEIPT`, `FEE`.
- `amount` (REAL, Required): Monetary amount (+ Inflow / - Outflow).
- `currency` (TEXT, Required): Currency code.

---

### 4. `receivables` & `payables`
Contractual expected obligations.
- `receivable_id` / `payable_id` (TEXT, PK): Unique contract ID.
- `entity_id` (TEXT, FK): References `legal_entities.entity_id`.
- `customer_name` / `vendor_name` (TEXT, Required): Counterparty name.
- `due_date` (TEXT, Required): Due date (`YYYY-MM-DD`).
- `amount` (REAL, Required): Scheduled amount.
- `currency` (TEXT, Required): Currency code.
- `status` (TEXT, Required): `PENDING` or `SETTLED`.

---

### 5. `currency_rates`
Foreign exchange conversion rates.
- `rate_id` (TEXT, PK): Identifier `FX-FROM-TO-YYYYMMDD`.
- `from_currency` (TEXT, Required): Base currency.
- `to_currency` (TEXT, Required): Target currency (USD / INR).
- `exchange_rate` (REAL, Required): Multiplier rate.
- `effective_date` (TEXT, Required): Fixing date.

---

### 6. `cash_flow_forecasts`
Projected cash items.
- `forecast_id` (TEXT, PK): Identifier `CF-YYYY-XXXXXX`.
- `entity_id` (TEXT, FK): References `legal_entities.entity_id`.
- `forecast_date` (TEXT, Required): Forecast date (`YYYY-MM-DD`).
- `forecast_type` (TEXT, Required): `INFLOW` or `OUTFLOW`.
- `amount` (REAL, Required): Projected nominal amount.
- `currency` (TEXT, Required): Currency code.
- `source_type` (TEXT, Optional): `RECEIVABLE`, `PAYABLE`, `MANUAL`.
- `source_id` (TEXT, Optional): Identifier of source obligation.

---

### 7. `liquidity_scenarios` & `forecast_runs`
Simulation parameters and batch execution runs.
- `scenario_id` (TEXT, PK): `BASE`, `UPSIDE`, `DOWNSIDE`.
- `scenario_name` (TEXT, Required): Scenario label.
- `assumptions` (TEXT, Required): Parameters (e.g., haircut % and delay days).
- `run_id` (TEXT, PK): Identifier `FCAST-YYYY-MM-DD-XXX`.
- `cutoff_date` (TEXT, Required): Actuals/ledger cutoff date.
- `status` (TEXT, Required): `COMPLETED` or `FAILED`.

---

### 8. `scenario_forecasts`
Consolidated daily simulation positions.
- `forecast_id` (TEXT, PK): Unique projection entry ID.
- `run_id` (TEXT, FK): References `forecast_runs.run_id`.
- `forecast_date` (TEXT, Required): Date of projection.
- `currency` (TEXT, Required): Target currency.
- `inflow` (REAL, Required): Total projected receipts.
- `outflow` (REAL, Required): Total projected disbursements.
- `net_flow` (REAL, Required): Inflow minus Outflow.
### 9. `settlements`
One synthetic actual cash movement per matched forecast in a freshly generated
dataset. The forecast-to-settlement relationship is 1:0..1. Settlement records
are inserted separately and keep the original forecast amount and date intact.

- `settlement_id` (TEXT, PK): Required, unique `SET-YYYY-XXXXXX` identifier.
- `forecast_id` (TEXT, FK): Required, unique reference to `cash_flow_forecasts.forecast_id`.
- `settlement_date` (TEXT): Required ISO date after the forecast cutoff.
- `amount` (REAL): Required positive actual amount in the forecast item's source currency.

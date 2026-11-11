
import sqlite3
if __package__:
    from .db import get_connection
else:
    from db import get_connection


def initialize_schema(connection: sqlite3.Connection):
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS legal_entities (
        entity_id TEXT PRIMARY KEY,
        entity_name TEXT NOT NULL,
        country TEXT NOT NULL,
        base_currency TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS bank_accounts (
        account_id TEXT PRIMARY KEY,
        entity_id TEXT NOT NULL,
        bank_name TEXT NOT NULL,
        account_number TEXT NOT NULL,
        currency TEXT NOT NULL,
        opening_balance REAL NOT NULL DEFAULT 0,
        closing_balance REAL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        FOREIGN KEY (entity_id) REFERENCES legal_entities(entity_id)
    );

    CREATE TABLE IF NOT EXISTS ledger_entries (
        ledger_id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        transaction_date TEXT NOT NULL,
        description TEXT,
        entry_type TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        FOREIGN KEY (account_id) REFERENCES bank_accounts(account_id)
    );

    CREATE TABLE IF NOT EXISTS receivables (
        receivable_id TEXT PRIMARY KEY,
        entity_id TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        due_date TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        FOREIGN KEY (entity_id) REFERENCES legal_entities(entity_id)
    );

    CREATE TABLE IF NOT EXISTS payables (
        payable_id TEXT PRIMARY KEY,
        entity_id TEXT NOT NULL,
        vendor_name TEXT NOT NULL,
        due_date TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        FOREIGN KEY (entity_id) REFERENCES legal_entities(entity_id)
    );

    CREATE TABLE IF NOT EXISTS currency_rates (
        rate_id TEXT PRIMARY KEY,
        from_currency TEXT NOT NULL,
        to_currency TEXT NOT NULL,
        exchange_rate REAL NOT NULL,
        effective_date TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS cash_flow_forecasts (
        forecast_id TEXT PRIMARY KEY,
        entity_id TEXT NOT NULL,
        forecast_date TEXT NOT NULL,
        forecast_type TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        source_type TEXT,
        source_id TEXT,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(entity_id)
    );

    CREATE TABLE IF NOT EXISTS liquidity_scenarios (
        scenario_id TEXT PRIMARY KEY,
        scenario_name TEXT NOT NULL,
        assumptions TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS forecast_runs (
        run_id TEXT PRIMARY KEY,
        scenario_id TEXT NOT NULL,
        run_date TEXT NOT NULL,
        cutoff_date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (scenario_id) REFERENCES liquidity_scenarios(scenario_id)
    );

    CREATE TABLE IF NOT EXISTS scenario_forecasts (
        forecast_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        forecast_date TEXT NOT NULL,
        currency TEXT NOT NULL,
        inflow REAL NOT NULL,
        outflow REAL NOT NULL,
        net_flow REAL NOT NULL,
        FOREIGN KEY (run_id) REFERENCES forecast_runs(run_id)
    );

    CREATE TABLE IF NOT EXISTS settlements (
        settlement_id TEXT PRIMARY KEY,
        forecast_id TEXT NOT NULL UNIQUE,
        settlement_date TEXT NOT NULL,
        amount REAL NOT NULL CHECK (amount > 0),
        FOREIGN KEY (forecast_id) REFERENCES cash_flow_forecasts(forecast_id)
    );
    """)

def create_tables():
    connection = get_connection()
    try:
        initialize_schema(connection)
    finally:
        connection.close()
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()

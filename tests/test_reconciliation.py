import os
import sqlite3
import pytest

DB_PATH = "database/liquidity.db"

def test_database_exists():
    assert os.path.exists(DB_PATH), "Database file liquidity.db does not exist."

def test_all_tables_exist():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    expected_tables = [
        "legal_entities", "bank_accounts", "ledger_entries", 
        "receivables", "payables", "currency_rates", 
        "cash_flow_forecasts", "liquidity_scenarios", 
        "forecast_runs", "scenario_forecasts"
    ]
    for tbl in expected_tables:
        assert tbl in tables, f"Expected table {tbl} is missing from database."

def test_orphan_bank_accounts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM bank_accounts 
        WHERE entity_id NOT IN (SELECT entity_id FROM legal_entities)
    """)
    orphan_count = cursor.fetchone()[0]
    conn.close()
    assert orphan_count == 0, f"Found {orphan_count} orphan bank accounts."
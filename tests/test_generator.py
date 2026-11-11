import sqlite3
from contextlib import closing

import pytest

from src.generate_dataset import SEED, generate


@pytest.mark.parametrize(
    "scale, entities, ledger, forecasts",
    [("starter", 5, 1000, 200), ("full", 30, 100000, 20000)],
)
def test_fresh_dataset(scale, entities, ledger, forecasts):
    with closing(sqlite3.connect(":memory:")) as db:
        generate(db, scale, SEED)
        for table, expected in (
            ("legal_entities", entities),
            ("bank_accounts", entities * 5),
            ("ledger_entries", ledger),
            ("cash_flow_forecasts", forecasts),
        ):
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == expected
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute("""
            SELECT COUNT(*) FROM (
                SELECT a.account_id
                FROM bank_accounts a
                JOIN ledger_entries l ON l.account_id = a.account_id
                GROUP BY a.account_id
                HAVING ABS(a.closing_balance - a.opening_balance -
                    SUM(CASE l.entry_type WHEN 'CREDIT' THEN l.amount ELSE -l.amount END)
                ) > 0.005
            )
        """).fetchone()[0] == 0
        assert db.execute("""
            SELECT COUNT(*) FROM cash_flow_forecasts f
            LEFT JOIN (
                SELECT receivable_id AS source_id, 'RECEIVABLE' AS source_type,
                       entity_id, due_date, amount, currency FROM receivables
                UNION ALL
                SELECT payable_id, 'PAYABLE', entity_id, due_date, amount, currency FROM payables
            ) s ON s.source_id = f.source_id AND s.source_type = f.source_type
            WHERE s.source_id IS NULL OR f.entity_id <> s.entity_id
                OR f.amount <> s.amount OR f.currency <> s.currency
                OR f.forecast_date <> s.due_date
        """).fetchone()[0] == 0
        assert db.execute("SELECT COUNT(DISTINCT currency) FROM cash_flow_forecasts").fetchone()[0] == 5

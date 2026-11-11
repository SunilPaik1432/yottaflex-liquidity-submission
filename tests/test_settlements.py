import sqlite3
from contextlib import closing

import pytest

from src.generate_dataset import CUTOFF, SEED, generate
from src.settlements import compare_settlements


def test_actuals_follow_cutoff_and_explain_variance(tmp_path):
    path = tmp_path / "starter.db"
    with closing(sqlite3.connect(path)) as db:
        generate(db, "starter", SEED)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()

    rows = compare_settlements(path, CUTOFF.isoformat())
    assert len(rows) == 200
    assert rows["forecast_id"].is_unique
    assert rows["settlement_date"].gt(CUTOFF.isoformat()).all()
    assert rows["days_late"].eq(5).any()
    assert rows["amount_effect_inr"].ne(0).any()
    assert rows["fx_effect_inr"].ne(0).any()
    assert rows["net_variance_inr"].tolist() == pytest.approx(
        (rows["amount_effect_inr"] + rows["fx_effect_inr"]).tolist(), abs=1e-7
    )


def test_legacy_database_without_settlements(tmp_path):
    path = tmp_path / "legacy.db"
    with closing(sqlite3.connect(path)):
        pass
    assert compare_settlements(path, CUTOFF.isoformat()).empty

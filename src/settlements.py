from contextlib import closing
import sqlite3

import pandas as pd


def compare_settlements(db_path, cutoff):
    with closing(sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)) as db:
        if not db.execute("""
            SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'settlements'
        """).fetchone():
            return pd.DataFrame()
        rows = pd.read_sql_query("""
            SELECT f.forecast_id, f.source_id, f.forecast_date, f.forecast_type, f.currency,
                   f.amount AS forecast_amount, s.settlement_id, s.settlement_date,
                   s.amount AS actual_amount,
                   CASE WHEN f.currency = 'INR' THEN 1.0 ELSE (
                       SELECT exchange_rate FROM currency_rates
                       WHERE from_currency = f.currency AND to_currency = 'INR'
                         AND effective_date <= ?
                       ORDER BY effective_date DESC, rate_id LIMIT 1
                   ) END AS forecast_fx,
                   CASE WHEN f.currency = 'INR' THEN 1.0 ELSE (
                       SELECT exchange_rate FROM currency_rates
                       WHERE from_currency = f.currency AND to_currency = 'INR'
                         AND effective_date <= s.settlement_date
                       ORDER BY effective_date DESC, rate_id LIMIT 1
                   ) END AS actual_fx
            FROM settlements s JOIN cash_flow_forecasts f USING (forecast_id)
            WHERE s.settlement_date > ?
            ORDER BY f.forecast_date, f.forecast_id
        """, db, params=(cutoff, cutoff))
    if rows.empty:
        return rows

    sign = rows["forecast_type"].map({"INFLOW": 1, "OUTFLOW": -1})
    rows["days_late"] = (
        pd.to_datetime(rows["settlement_date"]) - pd.to_datetime(rows["forecast_date"])
    ).dt.days
    rows["forecast_net_inr"] = sign * rows["forecast_amount"] * rows["forecast_fx"]
    rows["actual_net_inr"] = sign * rows["actual_amount"] * rows["actual_fx"]
    rows["amount_effect_inr"] = (
        sign * (rows["actual_amount"] - rows["forecast_amount"]) * rows["forecast_fx"]
    )
    rows["fx_effect_inr"] = (
        sign * rows["actual_amount"] * (rows["actual_fx"] - rows["forecast_fx"])
    )
    rows["net_variance_inr"] = rows["actual_net_inr"] - rows["forecast_net_inr"]
    return rows

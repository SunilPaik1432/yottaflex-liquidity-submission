import pandas as pd
import pytest

from src.scenarios import daily_scenario


@pytest.fixture
def forecast():
    return pd.DataFrame({
        "forecast_date": ["2026-11-10", "2026-11-11", "2026-11-11"],
        "inflow_inr": [100.0, 150.0, 50.0],
        "outflow_inr": [50.0, 25.0, 75.0],
    })


def test_delayed_receipts_keep_total_and_original_payment_dates(forecast):
    result = daily_scenario(forecast, 1, 1, 7).set_index("forecast_date")
    assert result.loc["2026-11-10", "outflow_inr"] == 50
    assert result.loc["2026-11-11", "outflow_inr"] == 100
    assert result.loc["2026-11-10":"2026-11-16", "inflow_inr"].sum() == 0
    assert result.loc["2026-11-17", "inflow_inr"] == 100
    assert result.loc["2026-11-18", "inflow_inr"] == 200
    assert result["net_flow_inr"].sum() == 150


def test_stress_scales_flows_without_changing_dates(forecast):
    result = daily_scenario(forecast, 0.9, 1.2, 0)
    assert result["forecast_date"].tolist() == ["2026-11-10", "2026-11-11"]
    assert result["inflow_inr"].tolist() == [90, 180]
    assert result["outflow_inr"].tolist() == [60, 120]
    assert result["net_flow_inr"].tolist() == [30, 60]

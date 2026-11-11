import pandas as pd


def daily_scenario(forecast, inflow_factor, outflow_factor, receipt_delay_days):
    dates = pd.to_datetime(forecast["forecast_date"])
    inflows = pd.DataFrame({
        "forecast_date": dates + pd.to_timedelta(receipt_delay_days, unit="D"),
        "inflow_inr": forecast["inflow_inr"] * inflow_factor,
    })
    outflows = pd.DataFrame({
        "forecast_date": dates,
        "outflow_inr": forecast["outflow_inr"] * outflow_factor,
    })
    daily = pd.concat([inflows, outflows]).groupby("forecast_date").sum()
    daily = daily.reindex(
        pd.date_range(dates.min(), daily.index.max(), name="forecast_date"),
        fill_value=0,
    ).reset_index()
    daily["forecast_date"] = daily["forecast_date"].dt.strftime("%Y-%m-%d")
    daily["net_flow_inr"] = daily["inflow_inr"] - daily["outflow_inr"]
    return daily

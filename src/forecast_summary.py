import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "database" / "liquidity.db"


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    try:
        rows = connection.execute("""
            SELECT
                forecast_date,
                currency,
                SUM(CASE WHEN forecast_type = 'INFLOW' THEN amount ELSE 0 END) AS inflow,
                SUM(CASE WHEN forecast_type = 'OUTFLOW' THEN amount ELSE 0 END) AS outflow
            FROM cash_flow_forecasts
            GROUP BY forecast_date, currency
            ORDER BY forecast_date, currency
        """).fetchall()

        if not rows:
            print("No cash flow forecasts found. Run src\\generate_data.py first.")
            return

        print("DATE-WISE CASH FLOW FORECAST (grouped by currency)")
        print(f"{'Date':<12} {'Currency':<10} {'Inflow':>15} {'Outflow':>15} {'Net flow':>15}")
        print("-" * 72)
        for forecast_date, currency, inflow, outflow in rows:
            net_flow = inflow - outflow
            print(f"{forecast_date:<12} {currency:<10} {inflow:>15,.2f} {outflow:>15,.2f} {net_flow:>15,.2f}")

        totals = connection.execute("""
            SELECT
                currency,
                SUM(CASE WHEN forecast_type = 'INFLOW' THEN amount ELSE 0 END) AS inflow,
                SUM(CASE WHEN forecast_type = 'OUTFLOW' THEN amount ELSE 0 END) AS outflow
            FROM cash_flow_forecasts
            GROUP BY currency
            ORDER BY currency
        """).fetchall()

        print("\nTOTAL FORECAST BY CURRENCY")
        print(f"{'Currency':<10} {'Inflow':>15} {'Outflow':>15} {'Net flow':>15}")
        print("-" * 58)
        for currency, inflow, outflow in totals:
            print(f"{currency:<10} {inflow:>15,.2f} {outflow:>15,.2f} {inflow - outflow:>15,.2f}")
        print(f"\nForecast rows summarized: {len(rows)} date/currency groups")
    finally:
        connection.close()


if __name__ == "__main__":
    main()

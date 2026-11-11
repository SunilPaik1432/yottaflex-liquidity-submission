import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "database" / "liquidity.db"


def print_overdue_exposure(connection, table, label):
    rows = connection.execute(
        f"""
        SELECT currency, COUNT(*) AS item_count, SUM(amount) AS exposure
        FROM {table}
        WHERE status = 'OVERDUE'
        GROUP BY currency
        ORDER BY currency
        """
    ).fetchall()
    print(f"\n{label} OVERDUE EXPOSURE")
    print(f"{'Currency':<10} {'Items':>8} {'Amount':>18}")
    print("-" * 38)
    if not rows:
        print("No overdue items.")
    for currency, item_count, exposure in rows:
        print(f"{currency:<10} {item_count:>8} {exposure:>18,.2f}")


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    try:
        print("RISK ANALYTICS (synthetic demo data)")
        print_overdue_exposure(connection, "receivables", "RECEIVABLE")
        print_overdue_exposure(connection, "payables", "PAYABLE")

        rows = connection.execute("""
            SELECT currency,
                   COUNT(*) AS forecast_days,
                   SUM(CASE WHEN net_flow < 0 THEN 1 ELSE 0 END) AS shortfall_days,
                   SUM(CASE WHEN net_flow < 0 THEN -net_flow ELSE 0 END) AS total_daily_shortfalls
            FROM (
                SELECT forecast_date, currency,
                       SUM(CASE
                           WHEN forecast_type = 'INFLOW' THEN amount
                           WHEN forecast_type = 'OUTFLOW' THEN -amount
                           ELSE 0
                       END) AS net_flow
                FROM cash_flow_forecasts
                GROUP BY forecast_date, currency
            )
            GROUP BY currency
            ORDER BY currency
        """).fetchall()

        print("\nFORECAST SHORTFALL DAYS BY CURRENCY")
        print(f"{'Currency':<10} {'Days':>8} {'Negative days':>15} {'Shortfall total':>20}")
        print("-" * 57)
        if not rows:
            print("No forecast records found.")
        for currency, forecast_days, shortfall_days, shortfall_total in rows:
            print(f"{currency:<10} {forecast_days:>8} {shortfall_days:>15} {shortfall_total:>20,.2f}")

        print("\nA negative-flow day is a warning indicator, not proof of insolvency.")
        print("Amounts are reported separately by currency and are not combined.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()

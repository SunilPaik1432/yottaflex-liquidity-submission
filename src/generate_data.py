import random
import sqlite3
from pathlib import Path
from datetime import date, timedelta

SEED = 20261022
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "database" / "liquidity.db"
CURRENCIES = ["INR", "USD", "EUR", "GBP", "SGD"]
START_DATE = date(2026, 1, 1)
RECORDS_PER_ENTITY = 100


def main():
    rng = random.Random(SEED)
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()
        with connection:
            entities = []
            for number in range(1, 31):
                currency = CURRENCIES[(number - 1) % len(CURRENCIES)]
                entities.append((
                    f"ENT-{number:06d}", f"YottaFlex Entity {number:03d}",
                    "India", currency, "ACTIVE", START_DATE.isoformat()
                ))
            cursor.executemany("""
                INSERT OR IGNORE INTO legal_entities
                (entity_id, entity_name, country, base_currency, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, entities)

            accounts = []
            account_balances = {}
            for i in range(1, 151):
                entity_number = ((i - 1) % 30) + 1
                entity_id = f"ENT-{entity_number:06d}"
                account_number = ((i - 1) // 30) + 1
                account_id = f"BANKACC-{entity_id}-{account_number:03d}"
                currency = CURRENCIES[(entity_number - 1) % len(CURRENCIES)]
                opening_balance = round(rng.uniform(100000, 1000000), 2)
                accounts.append((
                    account_id, entity_id, f"Bank {i:03d}",
                    f"ACCT{i:010d}", currency, opening_balance,
                    opening_balance, "ACTIVE"
                ))
                account_balances[account_id] = opening_balance
            cursor.executemany("""
                INSERT OR IGNORE INTO bank_accounts
                (account_id, entity_id, bank_name, account_number, currency,
                 opening_balance, closing_balance, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, accounts)

            ledger_entries = []
            for i in range(1, 100001):
                entity_number = ((i - 1) % 30) + 1
                account_number = ((i - 1) // 30) % 5 + 1
                account_id = f"BANKACC-ENT-{entity_number:06d}-{account_number:03d}"
                transaction_date = START_DATE + timedelta(days=rng.randint(0, 364))
                entry_type = rng.choice(["CREDIT", "DEBIT"])
                amount = round(rng.uniform(100, 50000), 2)
                currency = CURRENCIES[(entity_number - 1) % len(CURRENCIES)]
                ledger_entries.append((
                    f"LED-2026-{i:08d}", account_id,
                    transaction_date.isoformat(), f"Transaction {i}",
                    entry_type, amount, currency
                ))
                account_balances[account_id] += amount if entry_type == "CREDIT" else -amount
            cursor.executemany("""
                INSERT OR IGNORE INTO ledger_entries
                (ledger_id, account_id, transaction_date, description,
                 entry_type, amount, currency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ledger_entries)
            cursor.executemany(
                "UPDATE bank_accounts SET closing_balance = ? WHERE account_id = ?",
                [(balance, account_id) for account_id, balance in account_balances.items()],
            )

            receivables = []
            payables = []
            for entity_number in range(1, 31):
                entity_id = f"ENT-{entity_number:06d}"
                currency = CURRENCIES[(entity_number - 1) % len(CURRENCIES)]
                for item_number in range(1, RECORDS_PER_ENTITY + 1):
                    due_date = START_DATE + timedelta(days=rng.randint(0, 364))
                    status = rng.choice(
                        ["PAID", "OVERDUE"] if due_date < date(2026, 11, 10)
                        else ["PAID", "PENDING"]
                    )
                    amount = round(rng.uniform(500, 250000), 2)
                    receivables.append((
                        f"REC-{entity_number:03d}-{item_number:04d}",
                        entity_id,
                        f"Customer {item_number:04d}",
                        due_date.isoformat(), amount, currency, status
                    ))

                    due_date = START_DATE + timedelta(days=rng.randint(0, 364))
                    status = rng.choice(
                        ["PAID", "OVERDUE"] if due_date < date(2026, 11, 10)
                        else ["PAID", "PENDING"]
                    )
                    amount = round(rng.uniform(500, 250000), 2)
                    payables.append((
                        f"PAY-{entity_number:03d}-{item_number:04d}",
                        entity_id,
                        f"Vendor {item_number:04d}",
                        due_date.isoformat(), amount, currency, status
                    ))

            cursor.executemany("""
                INSERT OR IGNORE INTO receivables
                (receivable_id, entity_id, customer_name, due_date, amount, currency, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, receivables)
            cursor.executemany("""
                INSERT OR IGNORE INTO payables
                (payable_id, entity_id, vendor_name, due_date, amount, currency, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, payables)

        # Synthetic demo FX rates: INR value of one unit of each currency.
        inr_value = {"INR": 1.0, "USD": 83.5, "EUR": 90.5, "GBP": 105.0, "SGD": 62.0}
        fx_rates = []
        for from_currency in CURRENCIES:
            for to_currency in CURRENCIES:
                if from_currency == to_currency:
                    continue
                exchange_rate = inr_value[from_currency] / inr_value[to_currency]
                fx_rates.append((
                    f"FX-2026-{from_currency}-{to_currency}",
                    from_currency, to_currency, exchange_rate, START_DATE.isoformat()
                ))
        with connection:
            cursor.executemany("""
                INSERT OR IGNORE INTO currency_rates
                (rate_id, from_currency, to_currency, exchange_rate, effective_date)
                VALUES (?, ?, ?, ?, ?)
            """, fx_rates)
        # Base-case forecast generated from unpaid items due on/after the cutoff.
        cutoff_date = date(2026, 11, 10)
        scenario_id = "SCN-BASE-2026"
        run_id = "RUN-BASE-2026-001"
        assumptions = (
            "Base case: unpaid receivables are inflows and unpaid payables are outflows "
            "on their due dates; synthetic demo data; cutoff 2026-11-10."
        )
        with connection:
            cursor.execute("""
                INSERT OR IGNORE INTO liquidity_scenarios
                (scenario_id, scenario_name, assumptions, created_at)
                VALUES (?, ?, ?, ?)
            """, (scenario_id, "Base Case", assumptions, cutoff_date.isoformat()))
            cursor.execute("""
                INSERT OR IGNORE INTO forecast_runs
                (run_id, scenario_id, run_date, cutoff_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (run_id, scenario_id, cutoff_date.isoformat(), cutoff_date.isoformat(), "COMPLETED"))

            forecasts = []
            for row in cursor.execute("""
                SELECT receivable_id, entity_id, due_date, amount, currency
                FROM receivables
                WHERE status IN ('PENDING', 'OVERDUE') AND due_date >= ?
            """, (cutoff_date.isoformat(),)).fetchall():
                source_id, entity_id, due_date, amount, currency = row
                forecasts.append((
                    f"FC-{source_id}", entity_id, due_date, "INFLOW",
                    amount, currency, "RECEIVABLE", source_id
                ))
            for row in cursor.execute("""
                SELECT payable_id, entity_id, due_date, amount, currency
                FROM payables
                WHERE status IN ('PENDING', 'OVERDUE') AND due_date >= ?
            """, (cutoff_date.isoformat(),)).fetchall():
                source_id, entity_id, due_date, amount, currency = row
                forecasts.append((
                    f"FC-{source_id}", entity_id, due_date, "OUTFLOW",
                    amount, currency, "PAYABLE", source_id
                ))
            cursor.executemany("""
                INSERT OR IGNORE INTO cash_flow_forecasts
                (forecast_id, entity_id, forecast_date, forecast_type,
                 amount, currency, source_type, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, forecasts)
        print(f"Legal entities prepared: {len(entities)}")
        print(f"Bank accounts prepared: {len(accounts)}")
        print(f"Ledger entries prepared: {len(ledger_entries)}")
        print(f"Receivables prepared: {len(receivables)}")
        print(f"Payables prepared: {len(payables)}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()



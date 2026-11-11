import argparse
import random
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from datetime import date, timedelta

SEED = 20261022
ROOT = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from database.schema import initialize_schema
CURRENCIES = ["INR", "USD", "EUR", "GBP", "SGD"]
START_DATE = date(2026, 1, 1)
CUTOFF = date(2026, 11, 10)
SCALES = {
    "starter": (5, 1000, 200),
    "full": (30, 100000, 20000),
}


def generate(connection, scale, seed):
    entity_count, ledger_count, forecast_count = SCALES[scale]
    rng = random.Random(seed)
    connection.execute("PRAGMA foreign_keys = ON")
    initialize_schema(connection)
    with connection:
        cursor = connection.cursor()
        entities = []
        for number in range(1, entity_count + 1):
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
        for i in range(1, entity_count * 5 + 1):
            entity_number = ((i - 1) % entity_count) + 1
            entity_id = f"ENT-{entity_number:06d}"
            account_number = ((i - 1) // entity_count) + 1
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
        for i in range(1, ledger_count + 1):
            entity_number = ((i - 1) % entity_count) + 1
            account_number = ((i - 1) // entity_count) % 5 + 1
            account_id = f"BANKACC-ENT-{entity_number:06d}-{account_number:03d}"
            transaction_date = START_DATE + timedelta(days=rng.randrange((CUTOFF - START_DATE).days))
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
            [(round(balance, 2), account_id) for account_id, balance in account_balances.items()],
        )

        receivables = []
        payables = []
        forecasts = []
        for index in range(forecast_count):
            entity_number = (index // 2) % entity_count + 1
            entity_id = f"ENT-{entity_number:06d}"
            currency = CURRENCIES[(entity_number - 1) % len(CURRENCIES)]
            item_number = index // (entity_count * 2) + 1
            due_date = CUTOFF + timedelta(days=rng.randrange(52))
            amount = round(rng.uniform(500, 250000), 2)
            if index % 2 == 0:
                source_type = "RECEIVABLE"
                flow_type = "INFLOW"
                source_id = f"REC-{entity_number:03d}-{item_number:04d}"
                receivables.append((source_id, entity_id, f"Customer {item_number:04d}",
                                    due_date.isoformat(), amount, currency, "PENDING"))
            else:
                source_type = "PAYABLE"
                flow_type = "OUTFLOW"
                source_id = f"PAY-{entity_number:03d}-{item_number:04d}"
                if index == 1:
                    amount = 2_500_000.0
                payables.append((source_id, entity_id, f"Vendor {item_number:04d}",
                                 due_date.isoformat(), amount, currency, "PENDING"))
            forecasts.append((f"CF-2026-{index + 1:06d}", entity_id, due_date.isoformat(),
                              flow_type, amount, currency, source_type, source_id))

        for entity_number in range(1, entity_count + 1):
            entity_id = f"ENT-{entity_number:06d}"
            currency = CURRENCIES[(entity_number - 1) % len(CURRENCIES)]
            due_date = (CUTOFF - timedelta(days=rng.randint(1, 30))).isoformat()
            receivables.append((f"REC-{entity_number:03d}-OVERDUE", entity_id,
                                "Overdue customer", due_date, 5000.0, currency, "OVERDUE"))
            payables.append((f"PAY-{entity_number:03d}-OVERDUE", entity_id,
                             "Overdue vendor", due_date, 4000.0, currency, "OVERDUE"))

        cursor.executemany("INSERT INTO receivables VALUES (?, ?, ?, ?, ?, ?, ?)", receivables)
        cursor.executemany("INSERT INTO payables VALUES (?, ?, ?, ?, ?, ?, ?)", payables)
        cursor.executemany("INSERT INTO cash_flow_forecasts VALUES (?, ?, ?, ?, ?, ?, ?, ?)", forecasts)

        settlements = []
        for index, (forecast_id, _, due_date, flow_type, amount, _, _, _) in enumerate(forecasts, 1):
            delay = 5 if flow_type == "INFLOW" and index % 4 == 1 else 0
            settlement_date = max(CUTOFF + timedelta(days=1),
                                  date.fromisoformat(due_date) + timedelta(days=delay))
            actual_amount = round(amount * 0.95, 2) if index % 11 == 0 else amount
            settlements.append((f"SET-2026-{index:06d}", forecast_id,
                                settlement_date.isoformat(), actual_amount))
        cursor.executemany("INSERT INTO settlements VALUES (?, ?, ?, ?)", settlements)

        inr_values = dict(zip(CURRENCIES, (1.0, 83.5, 90.5, 105.0, 62.0)))
        rates = []
        for effective_date, movement in (
            (START_DATE, 0.0), (CUTOFF, 0.02), (CUTOFF + timedelta(days=21), 0.03)
        ):
            dated_values = {
                currency: value if currency == "INR" else value * (1 + movement)
                for currency, value in inr_values.items()
            }
            for source_currency in CURRENCIES:
                for target_currency in CURRENCIES:
                    if source_currency != target_currency:
                        rates.append((
                            f"FX-{effective_date}-{source_currency}-{target_currency}",
                            source_currency, target_currency,
                            dated_values[source_currency] / dated_values[target_currency],
                            effective_date.isoformat(),
                        ))
        cursor.executemany("INSERT INTO currency_rates VALUES (?, ?, ?, ?, ?)", rates)

        cutoff = CUTOFF.isoformat()
        cursor.execute(
            "INSERT INTO liquidity_scenarios VALUES (?, ?, ?, ?)",
            ("SCN-BASE-2026", "Base Case", "Pending items flow on their due dates. "
             "Overdue items are reported separately.", cutoff),
        )
        cursor.execute(
            "INSERT INTO forecast_runs VALUES (?, ?, ?, ?, ?)",
            (f"FCAST-{cutoff}-001", "SCN-BASE-2026", cutoff, cutoff, "COMPLETED"),
        )


def main():
    parser = argparse.ArgumentParser(description="Generate a fresh synthetic liquidity database.")
    parser.add_argument("--db", required=True, type=Path, help="New SQLite database path")
    parser.add_argument("--scale", choices=SCALES, default="full")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    try:
        with args.db.open("xb"):
            pass
    except FileExistsError:
        parser.error(f"Database already exists: {args.db}. Choose a new path.")
    except OSError as error:
        parser.error(str(error))

    try:
        with closing(sqlite3.connect(args.db)) as connection:
            generate(connection, args.scale, args.seed)
    except BaseException:
        args.db.unlink(missing_ok=True)
        raise
    print(f"Generated {SCALES[args.scale][2]:,} forecast items in {args.db}")


if __name__ == "__main__":
    main()

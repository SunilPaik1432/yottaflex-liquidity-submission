import argparse
from contextlib import closing
import csv
import hashlib
import json
from pathlib import Path
import sqlite3

from .generate_dataset import CUTOFF, SCALES, SEED, generate
from .validation_cases import GROUND_TRUTH, detect_issue, exception_cases


def validate_dataset(db):
    checks = {
        "foreign_keys": len(db.execute("PRAGMA foreign_key_check").fetchall()),
        "integrity": int(db.execute("PRAGMA integrity_check").fetchone()[0] != "ok"),
    }
    queries = {
        "closing_balances": """
            SELECT COUNT(*) FROM bank_accounts a
            LEFT JOIN (
                SELECT account_id, SUM(CASE entry_type WHEN 'CREDIT' THEN amount ELSE -amount END) AS net
                FROM ledger_entries GROUP BY account_id
            ) m USING (account_id)
            WHERE ABS(a.opening_balance + COALESCE(m.net, 0) - a.closing_balance) > 0.005
        """,
        "ledger_rules": """
            SELECT COUNT(*) FROM ledger_entries l JOIN bank_accounts a USING (account_id)
            WHERE l.currency <> a.currency OR l.entry_type NOT IN ('CREDIT', 'DEBIT')
                OR l.amount <= 0 OR l.transaction_date >= :cutoff
        """,
        "forecast_rules": """
            SELECT COUNT(*) FROM cash_flow_forecasts
            WHERE forecast_type NOT IN ('INFLOW', 'OUTFLOW') OR amount <= 0
                OR forecast_date < :cutoff
        """,
        "forecast_sources": """
            WITH sources AS (
                SELECT receivable_id AS id, entity_id, due_date, amount, currency,
                       'RECEIVABLE' AS source_type, 'INFLOW' AS direction, status FROM receivables
                UNION ALL
                SELECT payable_id, entity_id, due_date, amount, currency,
                       'PAYABLE', 'OUTFLOW', status FROM payables
            )
            SELECT COUNT(*) FROM cash_flow_forecasts f
            LEFT JOIN sources s ON s.id = f.source_id AND s.source_type = f.source_type
            WHERE s.id IS NULL OR s.entity_id <> f.entity_id OR s.amount <> f.amount
                OR s.currency <> f.currency OR s.due_date <> f.forecast_date
                OR s.direction <> f.forecast_type OR s.status <> 'PENDING'
        """,
        "duplicate_flows": """
            SELECT COUNT(*) FROM (
                SELECT source_type, source_id FROM cash_flow_forecasts
                GROUP BY source_type, source_id HAVING COUNT(*) > 1
            )
        """,
        "settlement_dates": """
            SELECT COUNT(*) FROM settlements WHERE settlement_date <= :cutoff OR amount <= 0
        """,
        "missing_forecast_fx": """
            SELECT COUNT(*) FROM cash_flow_forecasts f
            WHERE currency <> 'INR' AND NOT EXISTS (
                SELECT 1 FROM currency_rates r
                WHERE r.from_currency = f.currency AND r.to_currency = 'INR'
                    AND r.exchange_rate > 0 AND r.effective_date <= :cutoff
            )
        """,
    }
    for name, query in queries.items():
        checks[name] = db.execute(query, {"cutoff": CUTOFF.isoformat()}).fetchone()[0]
    return checks


def snapshot(db, destination=None):
    tables = db.execute("""
        SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name
    """).fetchall()
    manifest = {}
    for name, in tables:
        rows = db.execute(f'SELECT * FROM "{name}" ORDER BY 1')
        header = [column[0] for column in rows.description]
        digest = hashlib.sha256()
        count = 0
        output = (destination / f"{name}.csv").open("w", newline="", encoding="utf-8") if destination else None
        try:
            writer = csv.writer(output) if output else None
            if writer:
                writer.writerow(header)
            for row in rows:
                digest.update((json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8"))
                if writer:
                    writer.writerow(row)
                count += 1
        finally:
            if output:
                output.close()
        manifest[name] = {"rows": count, "sha256_ordered_rows": digest.hexdigest()}
    return manifest


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def export_submission(destination, scale, seed):
    destination.mkdir()
    csv_dir = destination / "seed_csv"
    csv_dir.mkdir()
    with closing(sqlite3.connect(":memory:")) as first, closing(sqlite3.connect(":memory:")) as second:
        generate(first, scale, seed)
        generate(second, scale, seed)
        tables = snapshot(first, csv_dir)
        repeat_matches = tables == snapshot(second)
        checks = validate_dataset(first)
    cases = exception_cases()
    detected = {case["id"]: detect_issue(case) for case in cases}
    expected = {
        "legal_entities": SCALES[scale][0],
        "bank_accounts": SCALES[scale][0] * 5,
        "ledger_entries": SCALES[scale][1],
        "cash_flow_forecasts": SCALES[scale][2],
        "settlements": SCALES[scale][2],
    }
    counts_match = all(tables[name]["rows"] == count for name, count in expected.items())
    summary = {
        "failed_rows_by_check": checks,
        "expected_counts_match": counts_match,
        "same_seed_counts_and_checksums_match": repeat_matches,
        "exception_results": detected,
        "exception_labels_match": detected == GROUND_TRUTH,
    }
    write_json(destination / "exception_cases.json", cases)
    write_json(destination / "ground_truth.json", GROUND_TRUTH)
    write_json(destination / "validation_summary.json", summary)
    write_json(destination / "source_manifest.json", {
        "source": "Synthetic records generated locally. No external dataset.",
        "generator": "src/generate_dataset.py",
        "scale": scale, "seed": seed, "cutoff": CUTOFF.isoformat(), "tables": tables,
    })
    if any(checks.values()) or not (repeat_matches and counts_match and detected == GROUND_TRUTH):
        raise RuntimeError(f"Validation failed. See {destination / 'validation_summary.json'}.")


def main():
    parser = argparse.ArgumentParser(description="Export and validate synthetic submission data.")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--scale", choices=SCALES, default="full")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    export_submission(args.output, args.scale, args.seed)
    print(f"Validation passed. Submission data saved to {args.output}")


if __name__ == "__main__":
    main()

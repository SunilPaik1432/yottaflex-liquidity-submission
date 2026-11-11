import json

import pytest

from src.export_submission import export_submission
from src.validation_cases import GROUND_TRUTH, detect_issue, exception_cases


@pytest.mark.parametrize("case", exception_cases(), ids=lambda case: case["id"])
def test_labelled_exceptions(case):
    assert detect_issue(case) == GROUND_TRUTH[case["id"]]


@pytest.mark.parametrize("case", [
    {"opening": 100, "ledger_net": 25, "closing": 125},
    {"currency": "USD", "reporting_currency": "INR", "fx_rate": 84},
    {"source_ids": ["REC-001-0001", "REC-001-0002"]},
    {"cutoff": "2026-11-10", "actual_date": "2026-11-10"},
    {"currencies": ["INR", "USD"], "converted_to": "INR"},
])
def test_valid_cases_are_not_flagged(case):
    assert detect_issue(case) is None


def test_submission_export(tmp_path):
    destination = tmp_path / "submission"
    export_submission(destination, "starter", 20261022)
    summary = json.loads((destination / "validation_summary.json").read_text())
    assert not any(summary["failed_rows_by_check"].values())
    assert summary["same_seed_counts_and_checksums_match"]
    assert summary["exception_labels_match"]
    assert (destination / "seed_csv" / "settlements.csv").exists()
    with pytest.raises(FileExistsError):
        export_submission(destination, "starter", 20261022)

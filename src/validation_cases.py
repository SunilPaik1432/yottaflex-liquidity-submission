def exception_cases():
    return [
        {"id": "CASE-001", "opening": 100, "ledger_net": 25, "closing": 130},
        {"id": "CASE-002", "currency": "USD", "reporting_currency": "INR", "fx_rate": None},
        {"id": "CASE-003", "source_ids": ["REC-001-0001", "REC-001-0001"]},
        {"id": "CASE-004", "cutoff": "2026-11-10", "actual_date": "2026-11-12"},
        {"id": "CASE-005", "currencies": ["INR", "USD"], "converted_to": None},
    ]


GROUND_TRUTH = {
    "CASE-001": "BALANCE_MISMATCH",
    "CASE-002": "MISSING_FX",
    "CASE-003": "DUPLICATE_CASH_FLOW",
    "CASE-004": "ACTUAL_AFTER_CUTOFF",
    "CASE-005": "MIXED_CURRENCIES",
}


def detect_issue(case):
    if "closing" in case and abs(case["opening"] + case["ledger_net"] - case["closing"]) > 0.005:
        return "BALANCE_MISMATCH"
    if "fx_rate" in case and case["currency"] != case["reporting_currency"] and not case["fx_rate"]:
        return "MISSING_FX"
    if "source_ids" in case and len(case["source_ids"]) != len(set(case["source_ids"])):
        return "DUPLICATE_CASH_FLOW"
    if "actual_date" in case and case["actual_date"] > case["cutoff"]:
        return "ACTUAL_AFTER_CUTOFF"
    if "currencies" in case and len(set(case["currencies"])) > 1 and not case["converted_to"]:
        return "MIXED_CURRENCIES"
    return None

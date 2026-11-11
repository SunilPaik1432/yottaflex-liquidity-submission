# Design and validation

## Forecast model

The opening cash position uses each account's opening balance plus ledger
movements dated before the cutoff. The base forecast puts pending receivables
and payables on their due dates. It reports overdue obligations separately.
Balances are kept in their source currency until they are converted to INR
using the latest rate effective at the cutoff.

The delayed-receipt scenario shifts inflows by seven calendar days and keeps
payment dates fixed. Stress reduces inflows by 10% and raises outflows by 20%.
These are demo assumptions. Forecast Lab keeps delayed receipts visible even
when they fall beyond the selected horizon. It uses the same starting cash
across scenarios and records assumptions when a run is saved.

## Settlement comparison

The synthetic generator adds one settlement per forecast item. Settlements
occur after the cutoff and do not modify the original forecast. The comparison
applies cutoff FX to the forecast and settlement-date FX to the actual. The
amount and FX effects sum to the signed net variance. The daily chart shows the
cash timing effect by placing the two flows on their respective dates.

## Verification and limitations

Run `python -m pytest` from the repository root. The tests cover source joins,
balance reconciliation, scenario rules, settlement variance and the five
negative cases. The [validation summary](../submission/validation_summary.json)
records the full dataset checks. Two independent runs used the same seed and
produced matching table row counts and checksums.

The demo uses synthetic FX and a due-date forecast. It models one settlement
per forecast item. Partial settlements and transaction-level lifecycle events
are outside this model. The public demo stores scenario runs in a temporary
database. The [source manifest](../submission/source_manifest.json) describes
how to reproduce the data.

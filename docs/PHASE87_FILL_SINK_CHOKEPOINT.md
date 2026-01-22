# Phase 87 - FillSink choke point

## Goal
Route all fills through a single method to ensure canonical tables and live gates remain consistent.

## Added
- `services/journal/fill_sink.py`: CanonicalFillSink, AccountingFillSink, CompositeFillSink
- Executor patch:
  - `self.fill_sink = CompositeFillSink(...)`
  - `_on_fill(fill, ...)` helper
  - Replaced direct `self.accounting.*fill*` calls

## Verification
- CLI: `python3 scripts/inject_test_fill.py`
- Dashboard: "Inject synthetic test fill" button

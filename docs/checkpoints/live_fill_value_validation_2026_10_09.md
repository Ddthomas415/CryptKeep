# Live fill ingestion: finite Decimal validation (2026-10-09) - READY_FOR_INDEPENDENT_REVIEW

Claude (cloud session); operator decision: Decimal for live/shadow paths only (paper accounting unchanged).
Change: services/execution/live_reconciler.py adds _validated_trade_values(): venue trade qty and price must parse as
finite Decimals and be > 0; a USD/USDT/USDC fee cost and any reported realized PnL must be finite (rebates allowed).
Before: qty/price defaulted to 0.0 when missing ("amount or qty or 0.0"), NaN/inf passed through float(), and a
garbage fee string silently became 0.0. After: an invalid matched trade is NOT inserted, NOT emitted to canonical
accounting, a warning is logged, and the trade cursor is held (same fail-closed path as an unaccounted fill), so it
is retried and visible instead of booked wrong. Valid trades are recorded exactly as before.
Not touched (mid-edit by the integrating session): storage/execution_store_sqlite.py, services/execution/_executor_reconcile.py.

Tests: tests/test_live_reconciler_trade_value_validation.py (12, incl. a positive control proving the matched path runs).
Verification under Python 3.12 + requirements.txt in a VM venv outside the repo: every test touching live_reconciler,
exchange_reconciler, position_truth, kill switch, intent_reconciler, paper_engine, journal/fill identity and the gate report:
815 passed. CMC/rerun/calibration/quote suites: 219 passed. (Earlier Python 3.10 errors were environment-only.)

## October10 bounded corrections (READY_FOR_INDEPENDENT_REVIEW)

Finite Decimal input is insufficient when storage still uses float: overflowing or nonzero-underflowing converted quantities, prices, USD-like fees and reported PnL are now refused before insertion/emission. Explicitly reported USD/USDT/USDC fees require a cost; missing cost no longer defaults to zero. Legitimate zero costs and negative rebates remain allowed.

This is finite-value validation, not exact Decimal storage/accounting. An entirely absent fee record and non-USD conversion still follow inherited behavior; zero fee_usd in those cases is not evidence of measured zero total costs. Separate fee-asset/evidence treatment remains open. Paper accounting and scheduling are unchanged.

Local targeted live-fill/position-truth/authority verification:41 passed, including matched-loop overflow/underflow refusal and preservation of the operator's3-observation/15-minute confirmation minimum. Full-suite, venue integration and deployment proof not run.

# Phase 87 - FillSink choke point

## Goal
Route all fills through a single method to ensure canonical tables and live gates remain consistent.

## Added
- `services/journal/fill_sink.py`: CanonicalFillSink, AccountingFillSink, CompositeFillSink
- `services/execution/live_executor.py`:
  - `_on_fill(fill, exec_db=...)` canonical fill hook
- `services/fills/user_stream_router.py`:
  - `route_ccxt_trade(...)` and `route_fill_event(...)` helpers for user-stream adapters
- `services/fills/fills_poller.py`:
  - routes fills via live-executor hook first, then safe fallback to CanonicalFillSink
- `services/fills/user_stream_ws.py` + `scripts/run_user_stream_fills.py`:
  - optional authenticated user-stream WS service that routes trade events through the same choke point

## Verification
- CLI: `python3 scripts/inject_test_fill.py`
- CLI: `python3 scripts/run_user_stream_fills.py --exchange coinbase --symbol BTC/USD`
- Dashboard: "Inject synthetic test fill" button

# Phase 83 — Deterministic LIVE gate inputs from exec_db

## What changed
- Adds `services/risk/journal_introspection_phase83.py`:
  - realized_pnl_today_usd(): prefers Phase 82 daily_limits, else sums fills-like tables if they have ts+pnl cols
  - trades_today(): prefers daily_limits.trades, else counts rows in orders/fills with timestamp cols

- Adds CLI:
  - `python3 scripts/show_live_gate_inputs.py`
  - reads merged runtime trading config for `execution.db_path` and displayed live risk limits

- Patches executor (only if Phase 82 marker exists):
  - if accounting doesn't expose realized pnl today, uses JournalSignals fallback

- Adds helper:
  - phase83_incr_trade_counter(exec_db): increment daily_limits.trades
  - Call this ONLY after a confirmed LIVE submit success.

## Safety behavior
- LIVE remains blocked if daily PnL cannot be determined (fail-closed).
- Trade counter should only be incremented after a confirmed LIVE submit; this phase provides the helper.

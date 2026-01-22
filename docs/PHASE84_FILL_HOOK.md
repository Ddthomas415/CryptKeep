# Phase 84 - Fill hook into fills_ledger (updates risk_daily deterministically)

## What this adds
- services/risk/fill_hook.py
  - record_fill(exec_db, fill): inserts a canonical fill into fills_ledger and updates risk_daily.
- scripts/record_dummy_fill.py
  - smoke test to confirm the rollup updates.

## How to use
Wherever your code processes fills, call:
  self._phase84_record_fill(fill_obj)

## Smoke test
python3 scripts/record_dummy_fill.py --symbol BTC-USD --pnl 3.5 --fee 0.2

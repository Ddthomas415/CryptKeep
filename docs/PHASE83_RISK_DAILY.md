# Phase 83 - Deterministic daily counters (risk_daily)

Adds a deterministic daily rollup table in exec_db:
- risk_daily(day, trades, realized_pnl_usd, fees_usd, updated_at)

Phase 82 LIVE gates can now read realized PnL from risk_daily.

Smoke test:
  python3 scripts/risk_daily_demo.py --pnl 10 --fee 0.5 --trades 1

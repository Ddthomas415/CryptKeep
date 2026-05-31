# Phase 82 — Mandatory LIVE Risk Gates (hard blocks)

Enforced before any LIVE submit:
- Kill switch (DB flag + optional kill-switch file)
- Max daily loss (uses pnl.sqlite realized_day)
- Max notional per trade
- Max trades per day (counts live submits)
- (Best-effort) position notional guard (future)

Config:
- config/trading.yaml -> risk.live.*
- config/trading.yaml -> paths.kill_switch_file

Implementation:
- `services/risk/live_risk_gates.py`
- `LiveRiskLimits.from_trading_yaml()` loads the canonical runtime trading
  config and returns no limits when `risk.live.*` is missing or invalid, causing
  live risk evaluation to fail closed.

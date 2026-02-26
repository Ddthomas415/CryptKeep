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

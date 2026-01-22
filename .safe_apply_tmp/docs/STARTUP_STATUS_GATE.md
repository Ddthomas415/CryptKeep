# Startup Status Gate (Phase 217)

File:
- data/startup_status.json

Recorded by:
- services/execution/startup_reconcile.py (records success/failure)

Gate:
- scripts/run_bot_safe.py refuses live start when startup reconcile is not fresh (if enabled)

Config:
startup_reconciliation:
  require_fresh_for_live: true
  fresh_within_hours: 24

UI:
- Dashboard -> Startup Status

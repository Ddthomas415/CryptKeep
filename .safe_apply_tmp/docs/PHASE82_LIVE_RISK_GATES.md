# Phase 82 - LIVE risk gates + kill switch

Adds:
- services/risk/live_risk_gates_phase82.py
- services/risk/killswitch_phase82.py
- scripts/killswitch.py

Enforces gates before LIVE submit in services/execution/live_executor.py (if present).

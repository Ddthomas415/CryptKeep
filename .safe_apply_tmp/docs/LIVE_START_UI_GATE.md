# Live Start UI Gate (Phase 219)

The Dashboard Start button refuses LIVE starts unless:

- Startup reconciliation status is fresh (startup_status.json)
- live_safety.live_enabled is true
- all selected symbols are confirmed for that venue (live_safety.confirmations[venue])
- user explicitly ARMS LIVE and types `LIVE`

Safety:
- If gating code errors, LIVE start fails closed.

Auto-disarm:
- After Start and after Stop, ARM LIVE and phrase fields reset.

# Startup Status Gate

Status: recorded reconciliation evidence, not a currently shown canonical launch gate

## File

- `data/startup_status.json`

## Writers

- `services/execution/startup_status.py`
- `services/execution/startup_reconcile.py`

## Current repo truth

- The current supervised startup wrappers shown in source are `scripts/run_intent_consumer_safe.py` and `scripts/run_live_reconciler_safe.py`.
- Those wrappers currently gate managed startup on `runtime_trading_config_available()`, not on `startup_status.json`.
- `scripts/run_bot_runner.py` also fails closed on missing runtime config and converges managed services without reading `startup_status.json`.
- No current in-repo caller was shown enforcing `startup_status.is_fresh(...)` on the canonical supervised startup path.

## Interpretation

- `startup_status.json` is current reconciliation evidence that can be recorded and inspected.
- Older docs tied startup-status freshness to launch gating, but the current visible supervised startup path does not show that enforcement.
- Treat this file as evidence, not as an active canonical launch gate, unless a current caller is wired and documented.

## UI

- Dashboard → Startup Status

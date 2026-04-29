# Bot Control Topology

## Canonical operator control plane
- `scripts/start_bot.py`
- `scripts/stop_bot.py`
- `scripts/bot_status.py`
- managed-service startup through supervisor / `service_ctl`

This is the operator-facing startup and stop path for current runtime control.

## Canonical runtime truth
- process-supervisor service state
- `runtime/flags/*.status.json`
- `runtime/health/*.json`

## Compatibility-only legacy plane
- `scripts/bot_ctl.py`
- `services.process.bot_process`
- `scripts/run_bot_safe.py`
- `data/bot_process.json`
- `data/bot_heartbeat.json`

These legacy surfaces remain only for compatibility with older callers. They are not the canonical startup or stop path.

## Decision-only compatibility surface
- `services.bot.start_manager.decide_start(...)`

This surface is still used for start/readiness decision messaging, but it is not the runtime process owner.

## Live confirmations
Real live start still requires:
- `ENABLE_LIVE_TRADING=YES`
- `CONFIRM_LIVE=YES`

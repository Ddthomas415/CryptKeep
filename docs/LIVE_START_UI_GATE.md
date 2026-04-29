# Live Start UI Gate

The visible live-start decision layers currently shown in source are:

- `services.bot.start_manager.decide_start(...)`
- `services.diagnostics.ui_live_gate.evaluate_live_ui_gate(...)`

## Current visible gate checks

`services.bot.start_manager.decide_start(...)` blocks live start when:

- `execution.live_enabled` is false
- the UI gate returns `BLOCK`
- live risk configuration is invalid
- real-live confirmation envs are missing:
  - `ENABLE_LIVE_TRADING=YES`
  - `CONFIRM_LIVE=YES`

`services.diagnostics.ui_live_gate.evaluate_live_ui_gate(...)` blocks when:

- the collector is not running
- a configured feed is missing
- a configured feed is in `BLOCK`
- the WS gate blocks

## Current repo truth

- The visible current UI gate code does not read `startup_status.json`.
- If gate code errors, the visible decision path fails closed.

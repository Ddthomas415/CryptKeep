# Live Mode Contract

This repo is strongest as a crypto-first, safety-aware execution and strategy-evaluation platform.

Current proven modes:

- `paper`
- `sandbox live`
- `real live` exists, but must be treated cautiously

This note describes how the repo currently decides between those modes.

## Canonical Operator Model

| Mode | Purpose | Exchange connectivity | Real funds risk | Current status |
| --- | --- | --- | --- | --- |
| `paper` | Strategy evaluation and dry execution behavior | No real exchange order placement | None | Supported |
| `sandbox live` | End-to-end live-stack exercise against exchange sandbox/test endpoints | Live API stack, sandbox where supported | Low, but still operational risk | Supported |
| `real live` | Actual live exchange order placement | Real exchange APIs | Real funds risk | Exists, high caution |

## Current Runtime Contract

### 1. Paper

Intended meaning:

- `execution.executor_mode = paper` or top-level runner `mode = paper`
- `execution.live_enabled = false`
- no explicit live arming env required

Where enforced:

- `/Users/baitus/Downloads/crypto-bot-pro/services/preflight/preflight.py`
  - treats `paper` as safe default
- `/Users/baitus/Downloads/crypto-bot-pro/services/bot/start_manager.py`
  - `paper` start allowed without live keys
- `/Users/baitus/Downloads/crypto-bot-pro/services/trading_runner/run_trader.py`
  - currently `paper` only

Operational meaning:

- paper execution venues and paper storage are allowed
- no live exchange order should be created

### 2. Sandbox Live

Intended meaning:

- config says live mode
- live enablement contract is true
- exchange client is constructed with `sandbox=True`
- launcher/operator checks pass

Key config/runtime signals:

- `/Users/baitus/Downloads/crypto-bot-pro/services/execution/live_arming.py::is_live_enabled(...)`
  normalizes these persisted flags:
  - `live.enabled`
  - `live_trading.enabled`
  - `risk.enable_live`
  - `execution.live_enabled`
- `/Users/baitus/Downloads/crypto-bot-pro/services/bot/start_manager.py`
  - reads `live.sandbox`
  - if `live.sandbox == true`, live start does not require the extra real-live confirmation envs

Operational meaning:

- the live stack is allowed to run
- exchange clients can still use sandbox endpoints where the venue supports them
- final order safety still applies at `/Users/baitus/Downloads/crypto-bot-pro/services/execution/place_order.py`

### 3. Real Live

Intended meaning:

- config says live mode
- normalized live enablement is true
- live arming is true
- `live.sandbox == false`
- operator/start gates pass

Additional real-live requirements today:

- `/Users/baitus/Downloads/crypto-bot-pro/services/bot/start_manager.py`
  requires:
  - `ENABLE_LIVE_TRADING=YES`
  - `CONFIRM_LIVE=YES`

Final-order arming requirements today:

- `/Users/baitus/Downloads/crypto-bot-pro/services/execution/place_order.py::_is_armed()`
  accepts:
  - `CBP_EXECUTION_ARMED`
  - `CBP_LIVE_ENABLED`
  - `CBP_EXECUTION_LIVE_ENABLED`

Operational meaning:

- a raw exchange order may still only be created if the final chokepoint allows it
- real-live remains explicitly separate from merely “live stack enabled”

## Current Knobs By Layer

### Persisted config knobs

Primary normalized live-enable inputs:

- `live.enabled`
- `live_trading.enabled`
- `risk.enable_live`
- `execution.live_enabled`

Mode/sandbox selectors:

- `execution.executor_mode`
- `live.sandbox`
- top-level `mode` in some runner flows

### Environment knobs

Operator/start gating:

- `ENABLE_LIVE_TRADING`
- `CONFIRM_LIVE`

Live arming compatibility envs:

- `CBP_LIVE_ARMED`
- `CBP_EXECUTION_ARMED`
- `CBP_LIVE_ENABLED`
- `CBP_EXECUTION_LIVE_ENABLED`
- `LIVE_TRADING`

Final-order boundary envs:

- `CBP_EXECUTION_ARMED`
- `CBP_LIVE_ENABLED`
- `CBP_EXECUTION_LIVE_ENABLED`
- `CBP_KILL_SWITCH`
- required live risk limits such as:
  - `CBP_MAX_TRADES_PER_DAY`
  - `CBP_MAX_DAILY_LOSS`
  - `CBP_MAX_DAILY_NOTIONAL`
  - `CBP_MAX_ORDER_NOTIONAL`

## What Is Canonical Right Now

If you need one practical operator reading of the current code, use this:

1. Persisted live enablement:
   - `execution.live_enabled` is the most practical canonical persisted flag
   - compatibility helpers still mirror it into `live.enabled`, `live_trading.enabled`, and `risk.enable_live`
2. Sandbox selector:
   - `live.sandbox`
3. Final order arming:
   - `CBP_EXECUTION_ARMED`
4. Final live-order authority:
   - `/Users/baitus/Downloads/crypto-bot-pro/services/execution/place_order.py::_enforce_fail_closed(...)`

## Safe Defaults

The repo currently defaults toward safety when:

- live config is absent or false
- arming env is absent
- real-live confirmation envs are absent
- kill switch is active
- required risk-limit envs are absent or invalid

That bias should remain.

## Current Ambiguities

These are real and should be treated as unresolved contract debt, not hidden features:

1. Multiple persisted live-enable flags exist.
   - `is_live_enabled(...)` intentionally normalizes them, but that also means there is not yet one exclusive persisted source of truth.
2. Outer arming helpers and the final boundary do not use exactly the same env list.
   - `/Users/baitus/Downloads/crypto-bot-pro/services/execution/live_arming.py::live_enabled_and_armed()` accepts `CBP_LIVE_ARMED` and `LIVE_TRADING`
   - `/Users/baitus/Downloads/crypto-bot-pro/services/execution/place_order.py::_is_armed()` does not
3. Some legacy/live-runtime flows still reason from top-level `mode`, others from `execution.executor_mode`, others from normalized `live_enabled`.

## Recommended Cleanup Direction

This is documentation only. No behavior changes are made here.

If Phase 3 cleanup is taken further, the safest target contract is:

- persisted live-enable source of truth:
  - `execution.live_enabled`
- sandbox vs real-live selector:
  - `live.sandbox`
- final-order arming env:
  - `CBP_EXECUTION_ARMED`
- operator real-live confirmation envs:
  - `ENABLE_LIVE_TRADING=YES`
  - `CONFIRM_LIVE=YES`

Anything else should be treated as compatibility input until explicitly removed with tests.

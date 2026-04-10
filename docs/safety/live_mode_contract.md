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
  reads:
  - `execution.live_enabled`
- `/Users/baitus/Downloads/crypto-bot-pro/services/bot/start_manager.py`
  - reads merged runtime config, `execution.live_enabled`, and `live.sandbox`
  - blocks live start if `execution.live_enabled` is false
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

- `CBP_EXECUTION_ARMED`
- `CBP_LIVE_ENABLED`
- `CBP_EXECUTION_LIVE_ENABLED`

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
   - `execution.live_enabled` is the canonical persisted flag on the active root-runtime path
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

1. Some legacy/live-runtime flows still reason from top-level `mode`, others from `execution.executor_mode`, others from normalized `live_enabled`.
2. Sandbox intent is still separate from persisted live-enable truth.
   - `live.sandbox` remains a distinct selector and should stay explicit in operator-facing flows.

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

## Related Operator Note

For review-stage criteria from `paper` to `sandbox live` to `tiny live`, see:

- `/Users/baitus/Downloads/crypto-bot-pro/docs/safety/strategy_promotion_ladder.md`

That note is intentionally operator-facing and conservative. It does not change the final order authority documented here.

# Safety Surface Classification

Date: 2026-07-04

## Purpose

This document classifies duplicate-looking safety, order identity, risk-gate,
and live-trader modules so future work does not accidentally build on the wrong
surface.

This is a documentation-only disposition. It does not change runtime behavior.

## Classification

| Surface | Status | Evidence | Rule |
|---|---|---|---|
| `services/admin/kill_switch.py` | Canonical operator kill-switch state | SHOWN: used by `scripts/killswitch.py`, onboarding/preflight, dashboard/admin flows, watchdog stale-heartbeat action, and paper evidence collector status. The module itself declares it as canonical runtime flag-file state. | New operator kill-switch state reads/writes should use this surface. |
| `scripts/killswitch.py` | Operator CLI wrapper | SHOWN: imports `get_state` and `set_armed` from `services.admin.kill_switch`. | Keep as the CLI entry point; do not add independent state here. |
| `services/execution/kill_switch.py` | Compatibility wrapper | SHOWN: delegates to `services.admin.kill_switch`; current visible production use is `scripts/run_bot_safe.py` preflight failure arming. | New code should import `services.admin.kill_switch` directly unless preserving a legacy import contract. |
| `services/risk/killswitch.py` | Live-order safety probe | SHOWN: imported by `services/execution/place_order.py` through `_load_killswitch_module()` and by `services/risk/live_safety_state.py`. It combines the canonical admin switch with `LiveGateDB` kill-switch state. | Do not delete as dormant. If consolidated, preserve the live `place_order` fail-closed contract first. |
| `services/risk/kill_conditions.py` | Strategy-runner risk-block cooldown logic | SHOWN: imported by `services/execution/strategy_runner.py`; it manages per-symbol cooldown after repeated risk blocks, not the global operator kill switch. | Keep conceptually separate from operator/live kill-switch state. |
| `services/risk/live_risk_gates.py` | Canonical live hard-limit gate | SHOWN: defines `LiveRiskLimits`, `LiveGateDB`, and `LiveRiskGates`; imported by executor shared/reconcile/submit paths, live executor, and live gate input scripts. | New live hard-limit enforcement should flow through this gate or an explicit wrapper around it. |
| `services/execution/risk_gates.py` | Executor adapter/wrapper | SHOWN: wraps `LiveRiskGates` via `evaluate_live_intent()` and exposes Binance venue guard import. | Keep as an executor-facing adapter; do not add separate policy here. |
| `services/ops/risk_gate_engine.py` and `services/ops/risk_gate_service.py` | Operational telemetry gate | SHOWN: classify raw telemetry into risk gate signals, store operational risk state, and are supervised as `ops_risk_gate`. | Treat as an ops-signal service, not a replacement for `LiveRiskGates`. |
| `services/execution/client_order_id.py` | Canonical live client-order-id builder | SHOWN: imported by live executor, `_executor_submit`, `_executor_shared`, `_executor_reconcile`, and `exchange_client`; venue-specific formats are encoded here. | New governed live/order paths should use this module. |
| `services/execution/client_oid.py` | Legacy/compat client OID builder | SHOWN: imported by `services/execution/intent_executor.py` and `services/execution/compat/intent_executor.py`; returns <=32 char IDs. | Keep only for compatibility executors until those paths are retired or migrated. Do not use for new governed live order paths. |
| `services/live_trader_multi/main.py` and `services/live_trader_fleet/main.py` | Duplicate dry-run legacy live runner stubs | SHOWN: files are effectively identical apart from `SERVICE_NAME` and log text; both simulate orders and record fills under live-mode guard checks. | Do not add features here. Any active live trading path should use the governed executor/intent pipeline, not these stubs. |

## Implementation Consequence

Future consolidation should be separate from this classification and must carry
targeted runtime tests before any safety surface is deleted or rewired.

The safest near-term policy is:

- Use `services/admin/kill_switch.py` for operator kill-switch state.
- Preserve `services/risk/killswitch.py` until the live `place_order` probe is
  replaced with a tested equivalent.
- Use `services/risk/live_risk_gates.py` for hard live risk limits.
- Use `services/ops/risk_gate_*` only for telemetry/ops risk signals.
- Use `services/execution/client_order_id.py` for new governed client order IDs.
- Treat `live_trader_multi` and `live_trader_fleet` as legacy stubs, not
  production execution surfaces.

## Remaining Risk

- UNVERIFIED: external consumers outside this repository were not audited.
- UNVERIFIED: no deletion or consolidation proof exists for the compatibility
  wrappers.
- SHOWN: visible source references support this classification at the time of
  writing.

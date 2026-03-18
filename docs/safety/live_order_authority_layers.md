# Live Order Authority Layers

This repo has multiple live-trading checks, but they do not all have the same authority.

The practical rule is:

- helper and operator layers may block early
- the final live-order permission still lives in `/Users/baitus/Downloads/crypto-bot-pro/services/execution/place_order.py::_enforce_fail_closed(...)`

No raw exchange order creation should bypass that function.

## Authority Stack

| Layer | File | Role | Authority level |
| --- | --- | --- | --- |
| State/helper layer | `/Users/baitus/Downloads/crypto-bot-pro/services/execution/live_arming.py` | Normalizes persisted live-enable flags and exposes compatibility arming helpers | Advisory/helper |
| Outer/operator gate | `/Users/baitus/Downloads/crypto-bot-pro/services/admin/live_guard.py` | Blocks live mode when kill switch is armed or normalized config says live is disabled | Early block, not final authority |
| Execution precheck | `/Users/baitus/Downloads/crypto-bot-pro/services/execution/intent_executor.py::_live_allowed()` | Live-intent precheck before an intent is sent to the adapter | Early block, not final authority |
| Final authority | `/Users/baitus/Downloads/crypto-bot-pro/services/execution/place_order.py::_enforce_fail_closed(...)` | Enforces kill switch, explicit arming, ops risk gate, env risk limits, daily-state limits, and market-rules checks before `create_order(...)` | Final live-order authority |

## What Each Layer Can Do

### 1. State/helper layer

`/Users/baitus/Downloads/crypto-bot-pro/services/execution/live_arming.py` answers questions like:

- is live enabled in persisted config?
- is some arming env present?

It is useful for UI, orchestration, and compatibility behavior.

It is not enough to make a live order safe by itself.

### 2. Outer/operator gate

`/Users/baitus/Downloads/crypto-bot-pro/services/admin/live_guard.py` is the operator-facing guardrail.

It can stop live mode early when:

- kill switch is armed
- normalized live enablement is false

It is still an outer gate. If this layer is bypassed or stale, the final order boundary must still block unsafe live order creation.

### 3. Execution precheck

`/Users/baitus/Downloads/crypto-bot-pro/services/execution/intent_executor.py::_live_allowed()` is an intent-time precheck.

It helps fail earlier in the intent pipeline, but it is not the final authority because:

- it reuses the same kill/cooldown probe contract as the final order boundary
- helper failure here must not be treated as permission to submit a live order

This layer should be read as an early filter, not the ultimate decision maker.

### 4. Final authority

`/Users/baitus/Downloads/crypto-bot-pro/services/execution/place_order.py::_enforce_fail_closed(...)` is the only layer that matters for raw order submission safety.

This is the layer that must block before any raw exchange `create_order(...)`.

Today it enforces:

- kill switch / cooldown
- explicit live arming
- optional ops risk gate
- required live env limits
- daily trade/loss/notional limits
- market-rules prerequisites and validation

If there is any conflict between an outer helper and this chokepoint, the chokepoint wins.

## Practical Contributor Rule

If you are changing live-order behavior:

1. you may add earlier blocks in helper, operator, or intent layers
2. you must not weaken `/Users/baitus/Downloads/crypto-bot-pro/services/execution/place_order.py::_enforce_fail_closed(...)`
3. you must not add any new direct `create_order(...)` path outside `/Users/baitus/Downloads/crypto-bot-pro/services/execution/place_order.py`

## Related Notes

- `/Users/baitus/Downloads/crypto-bot-pro/docs/safety/phase1_live_order_boundary.md`
- `/Users/baitus/Downloads/crypto-bot-pro/docs/safety/live_mode_contract.md`

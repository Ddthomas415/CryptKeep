# Live Mode Source-of-Truth Note

Status: LANDED

## Objective
Record the canonical live-mode source-of-truth contract for the root runtime path after the runtime/helpers were aligned.

## Confirmed repo truth
The current live-mode contract says the intended direction is:

- persisted live-enable source: `execution.live_enabled`
- sandbox selector: `live.sandbox`
- operator real-live confirmation envs:
  - `ENABLE_LIVE_TRADING=YES`
  - `CONFIRM_LIVE=YES`

## Confirmed code behavior
From `services/execution/live_arming.py`:

- `is_live_enabled(...)` now reads only:
  - `execution.live_enabled`
- `set_live_enabled(...)` now writes only:
  - `execution.live_enabled`
- `live_enabled_and_armed()` accepts multiple arming env vars:
  - `CBP_EXECUTION_ARMED`
  - `CBP_LIVE_ENABLED`
  - `CBP_EXECUTION_LIVE_ENABLED`

## Confirmed current state
The canonical root-runtime contract is now singular on the active helper and final-boundary path:

- persisted live-enable source:
  - `execution.live_enabled`
- runtime arming env contract:
  - `CBP_EXECUTION_ARMED`
  - `CBP_LIVE_ENABLED`
  - `CBP_EXECUTION_LIVE_ENABLED`
- final submit boundary:
  - `services/execution/place_order.py::_is_armed()`
  - uses the same runtime arming env list
- docs/tests:
  - updated to the canonical persisted flag on the active root-runtime path

## Current control surfaces
Persisted/config surfaces:
- `execution.live_enabled`
- `live.sandbox`

Arming env surfaces:
- `CBP_EXECUTION_ARMED`
- `CBP_LIVE_ENABLED`
- `CBP_EXECUTION_LIVE_ENABLED`

Compatibility/legacy arming surfaces mentioned in the contract:
- persisted `live_arming.json` state

## Remaining non-blocking ambiguity
The broader repo still contains other mode-selection surfaces that are separate from this landed fix:

- some flows still reason from top-level `mode`
- some flows still reason from `execution.executor_mode`
- sandbox intent is still represented separately by `live.sandbox`

Those are real contract-shaping concerns, but they are not the same blocker as persisted live-enable truth on the canonical root-runtime path.

## Landed evidence
- `services/execution/live_arming.py`
- `services/execution/place_order.py`
- `services/admin/live_enable_wizard.py`
- `services/admin/live_disable_wizard.py`
- `services/admin/resume_gate.py`
- `tests/test_live_arming_contract.py`
- `tests/test_live_mode_contracts.py`
- commit landed:
  - `49dd99c` — `execution: persist canonical live enable contract`

## Risk
High

## Review lane
Closed by independent review and publication

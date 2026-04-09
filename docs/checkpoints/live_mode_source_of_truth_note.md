# Live Mode Source-of-Truth Note

Status: OPEN

## Objective
Record the current live-mode source-of-truth ambiguity for the root runtime path without changing runtime behavior.

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

## Confirmed ambiguity
The repo documentation also explicitly records that live-mode truth is not yet singular:

- `docs/safety/live_mode_contract.md:177`
  - older config layers and historical docs still mention legacy flags, so singular persisted truth still requires cleanup outside the canonical runtime helpers
- `docs/safety/live_mode_contract.md:178`
  - outer arming helpers and the final boundary do not use exactly the same env list
- `docs/safety/live_mode_contract.md:181`
  - some flows still reason from top-level `mode`, others from `execution.executor_mode`, others from normalized `live_enabled`

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

## Why this is still a blocker
Different runtime layers can still reason from different live-mode knobs.
That means operator intent, sandbox intent, and final order authorization are not yet represented by one singular, consistent contract.

## Close condition
All of the following must be true:

1. One exclusive persisted live-enable source is defined and used.
2. One sandbox selector is defined and used.
3. One final arming contract is defined and used.
4. Docs and tests match the implemented contract.
5. Compatibility inputs, if retained temporarily, are explicitly secondary and cannot redefine canonical truth.

## Risk
High

## Review lane
READY_FOR_INDEPENDENT_REVIEW

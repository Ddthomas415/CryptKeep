# System Guard State Model

Status: design only  
Scope: halt-governance contract for live watchdog, executor, and reconciler surfaces  
Date: 2026-04-02

## Purpose

The repo currently has three independent fail-closed control surfaces:

- [watchdog.py](/Users/baitus/Downloads/crypto-bot-pro/services/process/watchdog.py)
- [live_executor.py](/Users/baitus/Downloads/crypto-bot-pro/services/execution/live_executor.py)
- [live_reconciler.py](/Users/baitus/Downloads/crypto-bot-pro/services/execution/live_reconciler.py)

They each make local safety decisions, but they do not currently share one authoritative halt state. This design defines that state model before any runtime implementation.

## Current Fragmentation

Current behavior is split across:

- watchdog:
  - stale heartbeat detection in [watchdog.py:55](/Users/baitus/Downloads/crypto-bot-pro/services/process/watchdog.py#L55)
  - kill switch arming in [watchdog.py:119](/Users/baitus/Downloads/crypto-bot-pro/services/process/watchdog.py#L119)
- executor:
  - market freshness and execution-safety gating in [live_executor.py:212](/Users/baitus/Downloads/crypto-bot-pro/services/execution/live_executor.py#L212)
  - kill-switch read in [live_executor.py:516](/Users/baitus/Downloads/crypto-bot-pro/services/execution/live_executor.py#L516)
- reconciler:
  - independent loop control, stop file, lock file, and status file in [live_reconciler.py:63](/Users/baitus/Downloads/crypto-bot-pro/services/execution/live_reconciler.py#L63)

This means the system can be "blocked" in one surface while another surface keeps running under a different local rule.

## Shared State

The authoritative guard state should live in one runtime file:

- proposed path: `.cbp_state/runtime/system_guard.json`

Why a new file instead of reusing `kill_switch.json`:

- existing [kill_switch.py](/Users/baitus/Downloads/crypto-bot-pro/services/admin/kill_switch.py) is binary and does not encode lifecycle stage, writer, or transition reason
- the guard needs to represent cooperative shutdown semantics, not just "armed true/false"

Required fields:

```json
{
  "state": "RUNNING",
  "ts": "2026-04-02T14:00:00Z",
  "writer": "watchdog",
  "reason": "heartbeat_ok",
  "epoch": 12,
  "cancel_requested": false
}
```

Field meanings:

- `state`: authoritative lifecycle state
- `ts`: last transition timestamp
- `writer`: component or operator that last wrote the state
- `reason`: human-readable transition reason
- `epoch`: monotonic transition number to prevent stale overwrites
- `cancel_requested`: explicit instruction for cancel-sweep behavior during halt

## States

### `RUNNING`

Meaning:

- new live submits are allowed if all existing local gates also pass
- reconciler is allowed to poll and update state
- watchdog observes only

### `HALTING`

Meaning:

- new live submits must stop immediately
- reconciler may continue in read-only / cleanup mode
- optional cancel sweep may begin if `cancel_requested=true`
- supervisor/operator surfaces should show degraded state, not normal running

### `HALTED`

Meaning:

- new live submits remain blocked
- no new cancel sweep should start automatically
- background loops may either stop or remain read-only, but they may not re-enable trading
- return to `RUNNING` requires an explicit operator or approved recovery action

## Transition Table

| From | To | Allowed Writer | Trigger | Required Effect |
| --- | --- | --- | --- | --- |
| `RUNNING` | `HALTING` | watchdog | stale heartbeat, process liveness failure | arm binary kill switch, block submits immediately |
| `RUNNING` | `HALTING` | executor | execution-safety breach, stale market data, unrecoverable pre-submit safety failure | block submits immediately, preserve reason |
| `RUNNING` | `HALTING` | operator/admin surface | manual halt request | block submits immediately |
| `HALTING` | `HALTED` | reconciler or supervisor | cleanup complete, cancel sweep complete, or operator forced halt | keep submits blocked, finalize degraded state |
| `HALTING` | `RUNNING` | operator/admin surface only | explicit manual recovery after review | clear halt only after operator signoff |
| `HALTED` | `RUNNING` | operator/admin surface only | explicit manual recovery after review | resume normal live processing |
| `HALTED` | `HALTING` | operator/admin surface only | restart cleanup/cancel process | re-enter cooperative halt path |

Disallowed transitions:

- watchdog may not clear `HALTING` or `HALTED`
- executor may not clear `HALTING` or `HALTED`
- reconciler may not move directly from `HALTED` to `RUNNING`

## Ownership Rules

### Writers

- watchdog:
  - may escalate to `HALTING`
  - may never clear a halt
- executor:
  - may escalate to `HALTING`
  - may never clear a halt
- reconciler:
  - may only move `HALTING -> HALTED` after cleanup work is complete
  - may never move to `RUNNING`
- operator/admin surface:
  - only surface allowed to restore `RUNNING`
  - may also force `HALTING` or `HALTED`

### Readers

- executor:
  - must treat `HALTING` and `HALTED` as hard block for new submits
- reconciler:
  - must continue only with allowed cleanup/read-only behavior during `HALTING`
  - must not reopen trading during `HALTING` or `HALTED`
- watchdog:
  - may still observe and persist diagnostics in any state
  - must not downgrade the guard state on its own

## Compatibility With Existing Kill Switch

During migration:

- `system_guard.state in {"HALTING", "HALTED"}` must imply `kill_switch.armed = true`
- `RUNNING` does not automatically imply `kill_switch.armed = false`
  - clearing the binary kill switch remains an explicit recovery action

This prevents accidental live re-enable during partial migration.

## Operator Semantics

`HALTING` means:

- block new live orders now
- optionally cancel open orders if explicitly requested
- allow cleanup and state capture

`HALTED` means:

- cleanup phase is over, or the system is intentionally frozen
- no new live orders
- no automatic return to service

This distinction matters because "stop new orders" and "cancel/flatten exposure" are different operational actions.

## Persistence Rules

- writes must be atomic: write temp file then rename
- the newest valid `epoch` wins
- unreadable or missing state must fail closed for submit paths
- unreadable state may still allow watchdog diagnostics to continue

If the guard file is corrupt or unavailable:

- executor behavior: treat as `HALTED` for live submit purposes
- reconciler behavior: read-only only, no state-clearing actions
- watchdog behavior: persist diagnostics and attempt to escalate via binary kill switch

## Non-Goals

This note does not define:

- exact cancel-all implementation details
- position-flattening strategy
- process-supervisor restart policy
- dashboard UX
- migration off the existing `kill_switch.json`
- how paper mode consumes this state

Those are follow-on implementation or operator-policy tasks.

## Implementation Consequence

The next runtime change after this document should be small and mechanical:

1. add a `system_guard` read/write module around `.cbp_state/runtime/system_guard.json`
2. make executor read that state before submit
3. make watchdog write `RUNNING -> HALTING`
4. make reconciler honor `HALTING` and optionally finalize `HALTED`

No component should invent its own new halt file after this spec is accepted.

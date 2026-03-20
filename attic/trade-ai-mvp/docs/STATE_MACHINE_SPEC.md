# State Machine Spec (v1)

This spec defines the core lifecycle rules shared by UI, API, risk, terminal, and audit.

## Required Machines
- System mode: `research_only`, `paper`, `live_approval`, `live_auto`
- Recommendation lifecycle
- Approval lifecycle
- Order lifecycle
- Position lifecycle
- Kill-switch lifecycle
- Safety status lifecycle

## System Mode
- Allowed transitions:
  - `research_only -> paper | live_approval`
  - `paper -> research_only | live_approval`
  - `live_approval -> research_only | paper | live_auto`
  - `live_auto -> live_approval | paper | research_only`
- Guards:
  - to live modes requires valid tradable connection + configured risk + user confirmation.
  - `research_only` always allowed.
- Audit on every change: `from`, `to`, `actor`, `reason`, `request_id`, `timestamp`.

## Recommendation States
- `draft -> ready -> pending_review -> approved -> converted_to_order`
- Alternate exits: `rejected`, `expired`, `cancelled`.
- Guarded approval requires mode/risk freshness checks and kill-switch off.

## Approval States
- `pending -> approved|rejected|expired|cancelled`
- `approved -> cancelled` if invalidated before order submission.
- Guards enforce actor permission, recommendation validity, risk pass, kill-switch off.

## Order States
- `created -> submitted -> acknowledged -> partially_filled -> filled`
- Cancellation path: `acknowledged|partially_filled -> cancel_requested -> cancelled`
- Error exits: `rejected`, `failed`, `expired`
- Keep `rejected` (known refusal) distinct from `failed` (system/transport uncertainty).

## Position States
- `opening -> open -> reducing|closing -> closed`
- Alternate exits: `liquidated`, `error_state`
- `error_state` requires explicit reconciliation workflow; never self-resolve silently.

## Kill Switch
- `off -> arming -> on -> releasing -> off`
- `releasing -> on` if validation fails.
- When `on`, block new execution paths globally; research can continue.

## Safety Status
- `safe`, `warning`, `restricted`, `paused`, `blocked`
- Computed from drawdown, slippage, connectivity, exchange health, kill-switch, policy flags.
- Can block execution independently of mode state.

## Composite Rules
- Approved recommendation can still be blocked by kill-switch, risk state, or mode regression.
- Mode switch to `research_only` cancels pending live execution paths and logs affected entities.
- Mode changes do not delete historical recommendations/orders/positions.

## Implementation Contract
- Centralize rules in `domain/state_machines/`.
- Each machine exports:
  - enum states
  - explicit transition map
  - guard functions
  - transition result:
    - `allowed`
    - `from`
    - `to`
    - `reason`
    - `side_effects`
  - audit payload builder

## Minimum Audit Fields per Transition
- `entity_type`, `entity_id`
- `previous_state`, `next_state`
- `actor_type`, `actor_id`
- `reason`, `request_id`, `timestamp`
- context payload (policy/risk/connection facts used by guard)


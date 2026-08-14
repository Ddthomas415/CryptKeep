# Paper Gate Velocity Checkpoint - 2026-08-14

## Scope

Read-only checkpoint for the canonical `es_daily_trend_v1` paper promotion gate.
This records the current velocity artifact and does not change campaign
configuration, promotion policy, provenance requirements, or gate logic.

## Command

```bash
make record-paper-gate-velocity
```

## Artifact

- `.cbp_state/data/paper_gate_velocity/paper_gate_velocity.20260814T051531Z.json`
- `.cbp_state/data/paper_gate_velocity/paper_gate_velocity.latest.json`

## Result

- `ok=true`
- `strategy_id=es_daily_trend_v1`
- `target_strategy=sma_200_trend`
- `policy_id=slow_daily_single_symbol_v1`
- `policy_valid=true`
- `thresholds_ready=false`

## Gate Position

- Qualified round trips: `3/5`
- Remaining qualified round trips: `2`
- Qualified bars: `53/60`
- Remaining qualified bars: `7`
- Calendar days: `101/45`
- All-history round trips: `10`
- Legacy/all-history round trips excluded by provenance/cohort policy: `7`

## Velocity

- Round-trip cadence: `10.5` days per qualified round trip.
- Qualified-bar cadence: `1.13` days per qualified bar.
- Round-trip projected completion: `2026-09-04T05:15:31.343677+00:00`.
- Qualified-bar projected completion: `2026-08-22T05:15:31.343880+00:00`.
- Overall active blocker: `round_trips`.

## Interpretation

The current gate is not stuck on calendar days or bar count alone. It is gated
by two remaining provenance-qualified round trips. Legacy fills remain
diagnostic only and should not be counted toward promotion under the current
policy.

## Boundaries

- No campaign restart.
- No promotion policy change.
- No provenance weakening.
- No legacy fill backfill.
- No live/shadow authorization.

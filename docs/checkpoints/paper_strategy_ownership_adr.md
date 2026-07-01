# Paper / Strategy ownership ADR

## Status
Draft

## Problem
The repo contains overlapping active families:
- `services/paper_trader`
- `services/strategies`
- `services/strategy_runner`

These overlaps create unclear ownership boundaries between:
- strategy definition
- runtime execution
- paper trading execution venues
- legacy compatibility layers

## Proven current state
- `services/strategies` = active canonical strategy-definition package
- `services/execution/strategy_runner.py` = active strategy runtime module
- `services/strategy_runner` = frozen compatibility wrapper package
- `services/strategy` = retired compatibility family as of 2026-07-01
- `services/paper` = retired compatibility family as of 2026-07-01
- `services/paper_trader` = active paper execution package

## Decision to make
Define explicit ownership boundaries for:
1. strategy definitions
2. strategy runtime/execution
3. remaining paper execution surfaces
4. compatibility layers slated for retirement later

## Constraints
- no deletions without import/reference proof
- no behavior changes in this ADR step
- compat layers remain until explicitly retired

## Proposed boundary questions
1. Should `services/strategies` remain the sole definitions layer?
2. Should `services/execution/strategy_runner.py` remain the sole runtime layer?
3. Which remaining paper execution surfaces should be consolidated next?
4. Which modules are compat-only and candidates for later retirement?

## Current decision
- `services/strategies` is the canonical owner of strategy definitions.
- `services/execution/strategy_runner.py` is the canonical owner of strategy
  runtime/execution.
- `services/strategy_runner` remains a frozen compatibility wrapper until the
  2026-08-01 transitional-family deadline.
- `services/strategy` is retired; do not reintroduce it.
- `services/paper` is retired; do not reintroduce it.
- `services/paper_trader` remains the active paper execution package.
- Remaining paper execution consolidation is outside this ADR update.

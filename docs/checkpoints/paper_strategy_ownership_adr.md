# Paper / Strategy ownership ADR

## Status
Draft

## Problem
The repo contains overlapping active families:
- `services/paper`
- `services/paper_trader`
- `services/strategies`
- `services/strategy_runner`
- `services/strategy`

These overlaps create unclear ownership boundaries between:
- strategy definition
- runtime execution
- paper trading execution venues
- legacy compatibility layers

## Proven current state
- `services/strategies` = active canonical strategy-definition package
- `services/strategy_runner` = active runner/runtime package
- `services/strategy` = legacy/compat/parallel overlap debt
- `services/paper` = active legacy/current paper-engine path
- `services/paper_trader` = active parallel execution-venue path

## Decision to make
Define explicit ownership boundaries for:
1. strategy definitions
2. strategy runtime/execution
3. paper trading engine
4. paper execution venue
5. compatibility layers slated for retirement later

## Constraints
- no deletions without import/reference proof
- no behavior changes in this ADR step
- compat layers remain until explicitly retired

## Proposed boundary questions
1. Should `services/strategies` remain the sole definitions layer?
2. Should `services/strategy_runner` remain the sole runtime layer?
3. Should `services/paper` or `services/paper_trader` be the long-term paper execution owner?
4. Which modules are compat-only and candidates for later retirement?

## Current decision
Pending

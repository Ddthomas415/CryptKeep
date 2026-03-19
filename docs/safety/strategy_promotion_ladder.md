# Strategy Promotion Ladder

This note is operator-facing. It does not change runtime behavior and it does not weaken the final live-order boundary.

The repo remains:

- crypto-first
- paper-heavy by default
- guarded and fail-closed for live order creation
- not validated for stocks
- not fully validated for shorting
- not proven profitable

Promotion here means "eligible for the next review stage", not "approved for unattended live trading".

## Ladder

### 1. Paper

Purpose:

- strategy research
- scorecard and leaderboard review
- hypothesis refinement

Promotion target:

- `sandbox live`

Minimum pass criteria:

- Phase 1 safety pack is green
- top strategy is still `keep`
- top strategy has at least `3` closed trades in the current decision cycle
- top strategy stays positive after fees and slippage
- collector/runtime freshness is not stale or missing
- kill switch is disarmed before any sandbox enablement
- `execution.live_enabled` and sandbox config are changed deliberately, not implicitly

Rollback criteria:

- return to `paper` immediately if the kill switch arms
- return to `paper` immediately if collector/runtime freshness degrades to stale or missing
- return to `paper` immediately if the promoted strategy flips away from `keep`
- return to `paper` immediately if operator telemetry is degraded or unknown

### 2. Sandbox Live

Purpose:

- exercise the live stack against sandbox/test endpoints
- observe operational behavior with guarded submission paths

Promotion target:

- `tiny live`

Minimum pass criteria:

- sandbox stage has already run cleanly with no active safety blockers
- top strategy remains `keep`
- top strategy has at least `5` closed trades across current evidence
- top strategy max drawdown stays at or below `8.0%`
- paper/live drift is measured and not high
- `ENABLE_LIVE_TRADING=YES` and `CONFIRM_LIVE=YES` are set deliberately for any tiny-live review
- `CBP_EXECUTION_ARMED` is set only for the reviewed trial window

Rollback criteria:

- return to `sandbox live` or `paper` immediately if the kill switch arms
- return to `sandbox live` or `paper` immediately if post-cost performance turns negative
- return to `sandbox live` or `paper` immediately if drawdown breaches the reviewed trial limit
- return to `sandbox live` or `paper` immediately if collector/runtime freshness degrades

### 3. Tiny Live

Purpose:

- tightly reviewed real-live trial with minimal size and explicit rollback posture

Current repo truth:

- real live exists
- it is guarded
- it must remain cautious and operator-driven

This ladder does not approve broad live deployment. It only describes when a tiny-live review is eligible.

## Current State On 2026-03-19

Based on the current strategy decision cycle and digest rules:

- current effective stage is still `paper`
- the next review target is `sandbox live`
- current promotion readiness is not yet sufficient because strategy evidence is still thin

Current evidence gap:

- the leading active strategies still only show `1` closed trade each in the latest synthetic cycle
- `mean_reversion_rsi` remains frozen due to `0` closed trades

That means the ladder should be read as a conservative review contract, not as a launch checklist that is already satisfied.

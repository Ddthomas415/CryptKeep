# RFC: Configurable Paper Promotion Gate Policies

**Status:** PROPOSED - design review only.

**Date:** 2026-07-18

**Active role:** DIRECTOR

**Implementation authorization:** Not granted. This document proposes a gate
model for review. The current `es_daily_trend_v1` gate remains unchanged until
this RFC is accepted and separately implemented.

## Problem

The current paper promotion threshold is universal:

- `PAPER_MIN_DAYS = 30`
- `PAPER_MIN_ROUND_TRIPS = 10`

This treats a single-symbol daily trend strategy and a 5-minute intraday
strategy as if they should produce evidence at comparable speed. They should
not. For slow daily systems, ten paper round trips can take months while still
not providing statistical proof of edge. For faster systems, ten round trips may
arrive quickly but still say little about regime coverage.

The result is a gate that mixes two responsibilities:

- operational validation: the live-data paper path runs correctly and produces
  provenance-qualified evidence;
- statistical validation: the strategy has a positive post-cost edge across
  enough independent history.

Paper trading is better suited to the first responsibility. Archive-backed
walk-forward evidence is better suited to the second.

## Evidence Behind This RFC

- SHOWN: `services/control/promotion_thresholds.py` currently defines a global
  `PAPER_MIN_DAYS = 30` and `PAPER_MIN_ROUND_TRIPS = 10`.
- SHOWN: `es_daily_trend_v1` has 10 all-history closed round trips, but only 3
  provenance-qualified round trips; 9 of 16 evidence fills lack required
  source/timeframe/venue/symbol/sample-mode provenance and remain diagnostic
  only.
- SHOWN: local evidence contains 45 qualified public daily signal dates for
  `es_daily_trend_v1` from 2026-05-26 through 2026-07-11.
- SHOWN: current strategy configs for `ema_cross_default`,
  `breakout_donchian_default`, and `pullback_recovery_default` also specify
  `promotion.paper.min_round_trips: 10` despite different horizons.
- SHOWN: recent laptop campaign status shows `no_public_ohlcv` failures for the
  configured Coinbase OHLCV source. That is a separate reliability issue, not a
  promotion-threshold issue.

## Goals

- Preserve strict provenance qualification.
- Keep current behavior as the default for strategies without an explicit gate
  policy.
- Allow strategy-class-specific paper gates that match strategy horizon.
- Add cohort filtering so legacy or pre-policy evidence remains auditable but
  does not count toward the active promotion cohort.
- Make qualified bar counting explicit, bounded, and resistant to repeated-loop
  inflation.
- Keep statistical edge validation in archive/walk-forward evidence, not paper
  round-trip count alone.

## Non-Goals

- Do not count legacy fills that lack required provenance.
- Do not change the current `es_daily_trend_v1` machine gate as part of this
  RFC.
- Do not widen the canonical paper universe.
- Do not treat five round trips as profitability proof.
- Do not mask OHLCV source failures by relaxing promotion gates.

## Proposed Policy Model

Add a policy object under `promotion.paper`. Missing policy fields preserve the
legacy global behavior.

```yaml
promotion:
  paper:
    policy:
      id: slow_daily_single_symbol_v1
      cohort_start: "2026-06-16T00:00:00Z"
      min_calendar_days: 45
      min_qualified_bars: 60
      min_qualified_round_trips: 5
      qualified_bar:
        source: public_ohlcv
        timeframe: 1d
        venue: coinbase
        symbol: BTC/USDT
        count: unique_source_bar
      require_archive_walk_forward: true
      require_manual_review: true
      legacy_evidence_policy: diagnostic_only
```

### Policy IDs

`legacy_round_trip_v1`

- Default when no explicit policy exists.
- Equivalent to the current machine behavior: 30 days and 10 qualified round
  trips.
- No `cohort_start` unless configured.

`slow_daily_single_symbol_v1`

- For single-symbol daily or multi-day holding-period strategies.
- Proposed minimums: 45 calendar days, 60 qualified daily bars, 5 complete
  qualified round trips.
- Requires archive-backed walk-forward evidence before promotion.
- Requires manual review even when machine thresholds pass.

`intraday_single_symbol_v1`

- For 1m/5m/15m OHLCV strategies such as EMA crossover, breakout, or pullback
  variants.
- Keeps at least 30 days and 10 qualified round trips by default.
- May add a qualified bar floor, but should not reduce round trips without a
  separate strategy decision record.

`context_edge_v1`

- For funding/open-interest/order-book strategies.
- Requires fresh strategy-context provenance in addition to any paired OHLCV
  source.
- Does not reuse OHLCV-only qualified bar semantics.
- Must be implemented only after the relevant context qualification branch is
  reviewed.

## Qualified Bar Definition

A qualified bar is one unique source-data decision bucket, not one runner loop.

For OHLCV-backed policies, count a bar only when the signal evidence record:

- belongs to the target `session_strategy_id`;
- is at or after `promotion.paper.policy.cohort_start`, if configured;
- has `market_data_source` equal to the configured source;
- has `ohlcv_sample_mode` explicitly false;
- has no `ohlcv_source_mismatch`;
- matches configured `ohlcv_timeframe`, `ohlcv_venue`, and `ohlcv_symbol`;
- includes the source bar timestamp or an accepted legacy fallback;
- is the first counted record for that source bar key.

The preferred source bar key is:

```text
(session_strategy_id, source, timeframe, venue, symbol, ohlcv_bar_ts)
```

Implementation should add or require `ohlcv_bar_ts` or `ohlcv_last_bar_ts` from
the last OHLCV candle. This prevents a 5-minute poll loop from inflating a
daily strategy's bar count.

Legacy compatibility:

- For daily OHLCV records already written without `ohlcv_bar_ts`, a temporary
  fallback may count at most one qualified signal per UTC date.
- The report must label this as `bar_count_source=legacy_signal_date`.
- Do not allow this fallback for intraday policies; intraday policies require
  explicit source candle timestamps.

## Cohort Start Semantics

`promotion.paper.policy.cohort_start` is a read-time filter. It must not delete,
rewrite, or hide older evidence.

Reports should show:

- active cohort start timestamp;
- qualified fills/signals inside the cohort;
- excluded fills/signals before the cohort;
- rejected fills due to missing or mismatched provenance;
- incomplete qualified fills;
- all-history diagnostic totals.

This preserves auditability while preventing legacy evidence from making the
current promotion state ambiguous.

## Migration Plan

1. Add the policy loader with default `legacy_round_trip_v1`.
2. Keep current gate output unchanged for all configs without
   `promotion.paper.policy`.
3. Add policy fields to reports as additive JSON keys only.
4. Add `slow_daily_single_symbol_v1` to `es_daily_trend_v1` only after this RFC
   is accepted.
5. Keep historical April/May ES fills diagnostic-only.
6. Require a fresh gate output before and after any policy activation.
7. Update operator docs to state that paper validates operational behavior and
   archive/walk-forward validates statistical edge.

## Backward Compatibility

- Existing `promotion.paper.min_days` and `promotion.paper.min_round_trips`
  remain supported.
- If no explicit policy exists, the gate resolves to the current global
  constants.
- Existing reports keep current keys such as `round_trips_recorded`,
  `round_trips_required`, and `round_trips_remaining`.
- New fields are additive:
  - `policy_id`
  - `cohort_start`
  - `qualified_bars_recorded`
  - `qualified_bars_required`
  - `bar_count_source`
  - `excluded_before_cohort`
  - `legacy_evidence_policy`

## Test Coverage

Required tests before implementation acceptance:

- Missing policy preserves current 30-day/10-round-trip behavior.
- Explicit `legacy_round_trip_v1` matches current behavior.
- Slow-daily policy requires both qualified bars and qualified round trips.
- Repeated runner loops on the same daily source bar count once.
- Intraday policies reject legacy date-only bar counting.
- `cohort_start` excludes older evidence from active counts while reports still
  surface all-history totals.
- Provenance rejection rules remain unchanged.
- A missing or malformed policy fails closed to the legacy policy or reports an
  invalid-policy blocker; it must not silently weaken thresholds.
- Existing `es_daily_trend_v1` remains on the current gate until its config is
  deliberately changed.

## Risks And Mitigations

Risk: fewer paper round trips could miss order-cycle defects.

Mitigation: keep at least 5 full cycles for slow daily systems, preserve strict
provenance, require manual review, and require shadow would-be-fill evidence
before live stages.

Risk: bar counting can be gamed by frequent polling.

Mitigation: count unique source candle timestamps, not signal events. Daily
legacy fallback is capped at one record per UTC date and must be labeled.

Risk: policy exceptions become one-off shortcuts.

Mitigation: policies are named, versioned, and strategy-class-based. Any
strategy-specific deviation needs a decision record.

Risk: archive/walk-forward assumptions diverge from paper costs.

Mitigation: promotion review must include cost-assumption validation for both
paper-fill and backtest/walk-forward surfaces.

Risk: OHLCV outages look like slow strategy behavior.

Mitigation: handle OHLCV source failures as a separate blocked-state reliability
item. Do not relax gate thresholds to compensate for source unavailability.

## Rollout Plan

Phase 0 - design review:

- Review this RFC.
- Decide whether `slow_daily_single_symbol_v1` is acceptable.
- Confirm whether ES should use `cohort_start=2026-06-16T00:00:00Z` or a later
  policy-activation timestamp.

Phase 1 - implementation:

- Add policy loader and additive report fields.
- Add qualified bar counter.
- Add tests for default behavior and slow-daily behavior.
- Do not change ES config yet.

Phase 2 - activation:

- After implementation is accepted, update `es_daily_trend_v1` config in a
  separate reviewed change.
- Record before/after gate output.
- Keep legacy fills diagnostic-only.

Phase 3 - future strategies:

- Require every new persistent paper campaign to declare a policy ID or accept
  the legacy default explicitly.
- Require context strategies to use `context_edge_v1` or a successor policy.

## Open Decisions

1. Should the slow-daily bar floor be 45 or 60?
   - Recommendation: 60, because the local evidence already has 45 qualified
     daily dates and the new policy should require additional post-review
     runtime exposure rather than pass immediately.
2. Should ES cohort start be 2026-06-16 or the date the policy is activated?
   - Recommendation: 2026-06-16 for fills, because that is the first complete
     qualified cycle start; label qualified bar fallback separately.
3. Should policy activation require archive walk-forward already accepted?
   - Recommendation: yes. Lower paper cycle count is acceptable only if
     statistical validation is supplied by archive/walk-forward evidence.

## Acceptance Criteria For This RFC

- Reviewer agrees the paper gate is operational validation, not profitability
  proof.
- Reviewer agrees missing policy preserves current behavior.
- Reviewer agrees provenance requirements and legacy-fill exclusion remain
  unchanged.
- Reviewer agrees OHLCV reliability is handled separately from gate policy.
- Reviewer chooses or rejects the slow-daily thresholds before implementation.

## Executable Guard

`tests/test_paper_promotion_gate_policy_rfc_guard.py` pins the RFC scope,
policy classes/defaults, qualified-bar definition, cohort/migration boundaries,
OHLCV reliability separation, and backlog link so configurable gate-policy work
cannot silently become a provenance waiver, ES one-off exception, or replacement
for archive/walk-forward statistical validation.

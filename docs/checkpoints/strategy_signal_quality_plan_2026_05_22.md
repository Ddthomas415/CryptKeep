# Strategy Signal-Quality Plan

Status: IMPLEMENTED; provenance qualification corrected 2026-06-15

## Purpose
Capture the next repo-side strategy-evaluation build so it is explicit, durable, and separate from the frozen canonical launch blocker list.

This plan answers the question:
- did the strategy identify the move early enough to trade it profitably?

It does not change launch scope by itself.

## Current implementation

- Analytics core: `services/analytics/signal_quality.py`
- CLI: `scripts/run_signal_quality_report.py`
- Focused tests:
  - `tests/test_signal_quality.py`
  - `tests/test_run_signal_quality_report.py`
- Canonical reports require matching, non-sample `public_ohlcv` provenance for
  the requested venue, symbol, and timeframe.
- Historical research can opt in to unqualified non-sample evidence only with
  `--allow-unqualified-evidence`.
- Reports expose qualified and excluded signal counts plus exclusion reasons.

## Current truth
- The paper monitor / evidence / dashboard path on `review-stabilized` is materially in place.
- The current paper promotion blocker is evidence, not repo correctness:
  - `19` days recorded
  - `4` completed round trips
  - expectancy still `UNKNOWN`
- The canonical live-launch blocker is still external sandbox/testnet venue proof or an explicit human exception decision.

## What already exists
- Signal outcome scoring:
  - `services/signals/reliability.py`
  - `scripts/recompute_signal_reliability.py`
- Forward-return primitive:
  - `services/backtest/forward_returns.py`
- Signal monetization replay:
  - `services/backtest/signal_replay.py`
- Structured evidence logs:
  - `services/strategies/evidence_logger.py`
- Campaign evidence summary:
  - `services/strategies/campaign_summary.py`
- Paper / synthetic scorecards:
  - `services/backtest/scorecard.py`
  - `services/backtest/evidence_run.py`

## Delivered report
The repo exposes one first-class report for:
- signal lead time
- late-hit classification
- capture ratio
- missed-mover rate
- max favorable excursion (MFE)
- max adverse excursion (MAE)
- false-positive cost

The remaining limitation is qualified actionable-signal coverage, not report
implementation.

## V1 contract
Start with one explicit evaluation target:

1. target move:
   - `+10% within 24h`
   - `+20% within 72h`
2. early-enough rule:
   - if more than `25%` of the eventual move already happened before the signal entry, classify as `late_hit`
3. first classifications:
   - `hit`
   - `late_hit`
   - `false_positive`
   - `missed_mover`

## Planned build sequence

### Phase 1: analytics core
Add:
- `services/analytics/signal_quality.py`

Responsibilities:
- read strategy evidence signals
- read matching OHLCV
- define target move windows
- score signals against those windows
- compute:
  - `lead_bars`
  - `capture_ratio`
  - `forward_return_pct`
  - `max_favorable_excursion_pct`
  - `max_adverse_excursion_pct`

Build on existing primitives:
- `services/signals/reliability.py`
- `services/backtest/forward_returns.py`
- `services/backtest/signal_replay.py`

### Phase 2: CLI and persisted artifact
Add:
- `scripts/run_signal_quality_report.py`

Outputs:
- JSON report to stdout
- persisted artifact under:
  - `.cbp_state/data/signal_quality/`

Suggested artifact names:
- `signal_quality.latest.json`
- `signal_quality_<strategy>_<date>.json`

### Phase 3: tests
Add targeted coverage:
- `tests/test_signal_quality.py`
- `tests/test_run_signal_quality_report.py`

Minimum cases:
1. hit classification
2. late-hit classification
3. false-positive classification
4. missed-mover classification
5. capture-ratio math
6. MFE / MAE math
7. artifact write path

### Phase 4: read-only operator surface
After CLI proof, surface summary in read-only operator paths.

Likely files:
- `dashboard/services/strategy_evaluation.py`
- `dashboard/services/digest/builders.py`
- `dashboard/components/summary_panels.py`

Goal:
- show signal-quality summary
- do not rewire promotion gates yet

### Phase 5: strategy decision use
Use the new report to decide:
- `keep`
- `freeze`
- `retire`

Decision focus:
- directionally right but too late
- early enough and monetizable
- noisy and false-positive-prone
- insufficient sample

## V1 metrics

### Summary metrics
- `signals_total`
- `signals_scored`
- `target_move_hits`
- `late_hits`
- `false_positives`
- `missed_movers`
- `hit_rate`
- `late_hit_rate`
- `false_positive_rate`
- `avg_lead_bars`
- `median_lead_bars`
- `avg_capture_ratio`
- `median_capture_ratio`
- `avg_mfe_pct`
- `avg_mae_pct`

### Per-signal row fields
- `signal_ts`
- `symbol`
- `strategy_id`
- `action`
- `entry_price`
- `target_move_pct`
- `target_horizon_bars`
- `move_start_ts`
- `move_peak_ts`
- `lead_bars`
- `late_hit`
- `capture_ratio`
- `forward_return_pct`
- `mfe_pct`
- `mae_pct`
- `classification`

## Parallel tracks

### A. Ongoing paper evidence
Keep daily paper evidence accumulation going and continue checking:
- `python scripts/check_promotion_gates.py --json`

Reopen audit when:
- expectancy becomes calculable
- completed round trips materially increase
- target strategy decision changes from `freeze` to `keep`

### B. Canonical live-launch blocker
Keep this separate from the signal-quality work:
- obtain one reachable supported sandbox/testnet venue
- prove place / fetch / cancel / post-cancel verification
- or make an explicit human exception decision

Canonical blocker record:
- `docs/checkpoints/launch_blockers_root_runtime.md`

## Non-goals for V1
- do not change promotion-gate policy yet
- do not broaden canonical launch scope
- do not claim profitability from prediction metrics alone

## Exit criteria
This plan is complete enough to advance when:
1. the repo can generate one stable signal-quality artifact for `es_daily_trend_v1`
2. that artifact is decision-useful for `keep / freeze / retire`
3. the result is visible without having to reverse-engineer raw logs manually

## Review rule
If implementation later touches:
- promotion gating
- live launch authority
- execution behavior
- background-job control flow

then stop at:
- `READY_FOR_INDEPENDENT_REVIEW`

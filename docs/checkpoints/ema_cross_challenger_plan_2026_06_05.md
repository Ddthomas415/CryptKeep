# EMA Cross Paper Challenger Plan (2026-06-05)

## Purpose

Create a paper-only challenger path for a higher-turnover strategy without
disturbing the active `sma_200_trend` evidence campaign.

This plan answers a different question than the current paper gate:

- Current campaign: has `es_daily_trend_v1` validated its own execution path?
- Challenger campaign: can a faster strategy identify tradable moves early
  enough to justify a separate paper evidence track?

The challenger must not contaminate canonical `es_daily_trend_v1` evidence.

## Visible Evidence

- SHOWN: `sma_200_trend` is a slow-turnover daily strategy and the active
  campaign is currently flat while price remains below SMA-200.
- SHOWN: `services/strategies/presets.py` defines `ema_cross_default` with
  `ema_fast=12`, `ema_slow=26`, and post-cross filters.
- SHOWN: `docs/strategies/ema_cross_research_note_2026-03-26.md` found no
  evidence strong enough to shorten the EMA pair; deterministic windows favored
  the default `12/26` preset over `9/21`.
- SHOWN: `scripts/run_paper_strategy_evidence_collector.py --help` exposes
  `--strategies`, `--session-strategy-id`, `--symbol`, `--venue`,
  `--signal-source`, `--runtime-sec`, `--daily-loop`, and `--status`.
- SHOWN: the collector accepts explicit signal sources such as
  `public_ohlcv_1m` and `public_ohlcv_5m`.
- SHOWN: `services/os/app_paths.py` supports `CBP_STATE_DIR`, and evidence
  artifact routing honors `CBP_STATE_DIR` for isolated temp or alternate state.

## Candidate

Use:

- Strategy: `ema_cross`
- Evidence strategy ID: `ema_cross_default`
- Preset: existing `12/26` default
- Side: long/flat only
- Initial symbol: `BTC/USDT`
- Initial venue: `coinbase`
- Initial signal source: `public_ohlcv_5m`

Do not change:

- `ema_fast`
- `ema_slow`
- filter thresholds
- canonical `es_daily_trend_v1` gate thresholds
- canonical `.cbp_state` paper history

Reason:

- `ema_cross` has shorter warmup and should produce more signal opportunities
  than a daily SMA-200 strategy.
- Existing research did not justify tuning the default preset yet.
- A 5-minute public OHLCV proof targets higher turnover while retaining a
  reproducible OHLCV provenance path.

## Isolation Rules

The first proof must run in a separate state directory:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/ema_cross_default" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py \
    --strategies ema_cross \
    --session-strategy-id ema_cross_default \
    --symbol BTC/USDT \
    --venue coinbase \
    --signal-source public_ohlcv_5m \
    --runtime-sec 900 \
    --strategy-drain-sec 2
```

After the run:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/ema_cross_default" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
```

Required isolation checks:

- The canonical `.cbp_state/data/trade_journal.sqlite` fill count for
  `sma_200_trend` must not change because of this challenger proof.
- Challenger artifacts must write under
  `.cbp_state_challengers/ema_cross_default`, not `docs/strategies/`.
- Any `ema_cross_default` fills must remain separate from
  `es_daily_trend_v1` promotion-gate evidence.
- Do not run the challenger as `--daily-loop` until the one-shot proof shows
  clean startup, status, artifact routing, and stop behavior.

## Evidence Gate

Stage 0: wiring proof

- One isolated one-shot run completes without runtime errors.
- Public OHLCV provenance is present in the signal/session artifacts.
- No canonical campaign state is modified.
- If no signal fires, the result is still acceptable if the reason is visible
  and the process exits cleanly.

Stage 1: paper challenger evidence

- At least 10 closed round trips for `ema_cross_default`.
- At least 20 calendar days or trading sessions of observation.
- Positive realized expectancy after fees/slippage assumptions used by the
  paper engine.
- No unresolved runtime failures, duplicate-close behavior, or state-routing
  issues.
- Backtest baseline populated before any operator promotion review:
  `win_rate`, `avg_win`, `avg_loss`, and expectancy.

Stage 2: research-confidence floor

- At least 50 closed round trips before any live-capital confidence claim.
- Performance remains positive across multiple regimes.
- Comparison against `sma_200_trend`, `breakout_donchian`, and
  `pullback_recovery` uses the same paper accounting rules.

## Risk Caps

- Paper-only until a separate review accepts the challenger evidence.
- No short-side behavior in this plan.
- One symbol for the first proof.
- No preset tuning during the first proof.
- No changes to live trading, order routing, risk gates, or branch protection.
- No use of challenger evidence to advance `es_daily_trend_v1`.

## Decision Rules

Continue if:

- The isolated run is operationally clean.
- Signals/fills appear with clear reasons and expected provenance.
- Evidence accumulates materially faster than `sma_200_trend`.

Investigate if:

- No actionable signal appears after 7 isolated sessions.
- Public OHLCV fetches are stale or missing.
- Fills appear in the canonical `sma_200_trend` journal.
- The monitor cannot distinguish `ema_cross_default` from `es_daily_trend_v1`.

Reject or pause if:

- Expectancy is negative after 10+ closed round trips.
- The strategy only trades because filters were weakened without a new baseline.
- Any live/paper state boundary is ambiguous.

## Next Action

Run only the Stage 0 isolated one-shot proof after this plan is independently
accepted. If Stage 0 passes, convert the proof into a separate monitored
paper-only daily campaign.

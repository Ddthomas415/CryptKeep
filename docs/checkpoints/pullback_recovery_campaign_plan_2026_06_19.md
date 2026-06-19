# Pullback Recovery Paper Campaign Plan - 2026-06-19

## Purpose

Create a paper-only campaign path for `pullback_recovery` without disturbing the
active `es_daily_trend_v1`, `ema_cross_default`, or `breakout_default`
campaigns.

This plan answers a different question than the canonical paper gate:

- Canonical campaign: has `es_daily_trend_v1` produced enough
  provenance-qualified paper evidence for its own promotion review?
- Pullback campaign: can an existing pattern-style strategy identify
  trend-pullback recoveries early enough to justify a separate paper evidence
  track?

The pullback campaign must not contaminate canonical `es_daily_trend_v1`
promotion evidence.

## Visible Evidence

- SHOWN: `services/strategies/pullback_recovery.py` exists and emits `buy`,
  `sell`, or `hold` from OHLCV using trend, pullback, rebound, and RSI
  conditions.
- SHOWN: `services/strategies/presets.py` defines
  `pullback_recovery_default`.
- SHOWN: `services/strategies/validation.py` supports `pullback_recovery`
  fields and validates typed numeric/bool parameters.
- SHOWN: `services/backtest/leaderboard.py` includes
  `pullback_recovery_default` in the default aggregate candidate set.
- SHOWN: `configs/paper_evidence_campaigns.json` currently manages exactly
  three enabled campaigns: `es_daily_trend_v1`, `ema_cross_default`, and
  `breakout_default`.
- SHOWN: `scripts/run_paper_strategy_evidence_collector.py` supports explicit
  strategy, session strategy ID, symbol, venue, signal source, runtime duration,
  drain duration, status, and daily-loop flags.
- SHOWN: `CBP_STATE_DIR` routes evidence artifacts into isolated state
  directories when set.

UNVERIFIED:
- No backtest baseline has been accepted for `pullback_recovery_default`.
- No isolated paper campaign has been started for `pullback_recovery_default`.
- No turnover estimate has been accepted for `pullback_recovery_default` under
  public Coinbase `BTC/USDT` OHLCV.

## Candidate

Use:

- Strategy: `pullback_recovery`
- Evidence strategy ID: `pullback_recovery_default`
- Preset: existing `pullback_recovery_default`
- Side: long/flat only
- Initial symbol: `BTC/USDT`
- Initial venue: `coinbase`
- Initial signal source: `public_ohlcv_5m`

Do not change:

- `pullback_recovery_default` preset values
- canonical `es_daily_trend_v1` paper gate thresholds
- canonical `.cbp_state` paper history
- active `ema_cross_default` or `breakout_default` campaign state
- live trading, order routing, risk gates, branch protection, or auth behavior

Reason:

- `pullback_recovery` is the lowest-infrastructure pattern-style strategy
  already present in the repo.
- It is a better fit than SMA-200 for testing whether the system can identify
  move entries earlier during trend pullbacks.
- A 5-minute public OHLCV proof keeps the first campaign reproducible and
  provenance-checkable without requiring order book, funding, open interest, or
  derivatives plumbing.

## Stage 0 - Isolated One-Shot Proof

Run only after this plan is independently accepted:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/pullback_recovery_default" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py \
    --strategies pullback_recovery \
    --session-strategy-id pullback_recovery_default \
    --symbol BTC/USDT \
    --venue coinbase \
    --signal-source public_ohlcv_5m \
    --runtime-sec 900 \
    --strategy-drain-sec 2
```

After the run:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/pullback_recovery_default" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
```

Required checks:

- Canonical `.cbp_state/data/trade_journal.sqlite` fill count for
  `sma_200_trend` does not change because of this proof.
- Pullback evidence writes under
  `.cbp_state_challengers/pullback_recovery_default`, not `docs/strategies/`
  and not canonical `.cbp_state`.
- Signal/session artifacts carry public OHLCV provenance.
- A no-trade result is acceptable only if the session completes cleanly and the
  no-edge reason is visible.
- The proof is not converted to `--daily-loop` until startup, status, artifact
  routing, and state isolation are shown.

## Stage 1 - Paper Campaign Evidence

Only after Stage 0 passes:

- Add a disabled manifest entry first, review it, then enable it in a separate
  accepted change.
- Use a dedicated state directory:
  `.cbp_state_challengers/pullback_recovery_default_daily`.
- Observe at least 20 sessions.
- Require at least 10 closed round trips before any paper-stage review.
- Populate a backtest baseline before comparing performance:
  `win_rate`, `avg_win_return_pct`, `avg_loss_return_pct`, and expectancy.
- Track whether the strategy produces materially earlier entries than
  `sma_200_trend`, `ema_cross_default`, and `breakout_default` on the same
  symbol/source family.

## Stage 2 - Research-Confidence Floor

Before any live-capital confidence claim:

- At least 50 closed round trips.
- Positive net realized expectancy after fees/slippage assumptions.
- Performance is not concentrated in one isolated regime.
- Comparison uses the same provenance qualification and paper accounting rules
  as other strategies.

## Risk Caps

- Paper-only until separate evidence is accepted.
- Long/flat only.
- One symbol and one venue for the first proof.
- No preset tuning during Stage 0.
- No use of pullback evidence to advance `es_daily_trend_v1`.
- No derivatives, leverage, margin, short-side execution, order-book, funding,
  or open-interest dependencies.

## Decision Rules

Continue if:

- Stage 0 is operationally clean.
- Evidence and status remain isolated.
- Signals/fills carry public OHLCV provenance.
- It produces useful signal opportunities without weakening the preset.

Investigate if:

- No actionable signal appears after 7 isolated sessions.
- Public OHLCV data is missing or stale.
- Fill artifacts appear in canonical `es_daily_trend_v1` state.
- The paper monitor cannot distinguish `pullback_recovery_default` from other
  campaigns.

Reject or pause if:

- State routing is ambiguous.
- The strategy requires preset weakening before any baseline exists.
- Expectancy is negative after 10+ closed round trips.
- Any live or short-side behavior is required to make the strategy work.

## Next Action

Independently review this plan. If accepted, run only the Stage 0 isolated
one-shot proof and stop before enabling any persistent daily campaign.

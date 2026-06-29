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
- SHOWN: the first accepted Stage 0 run completed in
  `.cbp_state_challengers/pullback_recovery_default` with no fills and no
  canonical `sma_200_trend` fill-count change.
- SHOWN: that first run exposed an attribution bug: runtime status reported
  `strategy_preset=ema_cross_default` while session evidence wrote under
  `pullback_recovery_default`.
- SHOWN: PR #68 fixed and merged the attribution path so future
  `pullback_recovery` runs report `strategy_preset=pullback_recovery_default`.

UNVERIFIED:
- No backtest baseline has been accepted for `pullback_recovery_default`.
- No full 900-second post-fix Stage 0 proof has been rerun for
  `pullback_recovery_default`.
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

Status:

- The plan was independently accepted and the first isolated run completed.
- That run is not sufficient as final Stage 0 proof because it exposed the
  pre-fix `ema_cross_default` attribution defect.
- PR #68 fixed the attribution defect and was merged before a full post-fix
  Stage 0 rerun.
- `scripts/check_pullback_stage0_readiness.py` now provides a read-only
  readiness report for the post-fix Stage 0 proof. It validates strategy,
  preset, collector-session, state-isolation, and campaign-manifest ownership
  checks, writes only readiness artifacts, and prints the exact 15-minute proof
  command for the operator.
- PR #139 independently accepted and merged the readiness report. The readiness
  review step is closed; the actual full post-fix Stage 0 run is still pending.
- `scripts/verify_pullback_stage0_proof.py` now provides a read-only
  baseline/verifier for the full Stage 0 proof. The baseline captures the
  canonical paper-history fill count before the long run; the verifier checks
  the completed pullback session after the run and confirms canonical fill-count
  isolation.

Immediately before the full post-fix Stage 0 proof, record the baseline:

```bash
make pullback-stage0-baseline
```

Then run the full post-fix Stage 0 proof only when the operator is ready for a
15-minute command:

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

Then verify the proof:

```bash
make pullback-stage0-verify
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

Run the full post-fix Stage 0 isolated one-shot proof when the operator is
ready for a 15-minute command. Stop before enabling any persistent daily
campaign.

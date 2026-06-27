# Composite Hybrid Leaderboard Comparison - 2026-06-27

## Scope

Active role: ENGINEER

Objective:
- Generate read-only leaderboard comparison evidence for the accepted
  `composite_hybrid_v1_breakout_sma200_research` candidate.
- Do not add a paper campaign, runtime registry entry, promotion behavior, or
  order-routing path.

## Evidence Command

Environment: VERIFIED_ENV

The comparison was generated with `run_strategy_evidence_cycle(...)` and written
to a temp artifact only:

- `/private/tmp/composite_hybrid_leaderboard_comparison_20260627.json`

No canonical `.cbp_state` strategy-evidence artifact was written.

Parameters:
- symbol: `BTC/USDT`
- source: `multi_window_synthetic`
- initial cash: `10000.0`
- fee bps: `10.0`
- slippage bps: `5.0`
- as_of: `2026-06-27T23:51:14Z`

## Aggregate Result

Candidate count: `10`

| Rank | Candidate | Strategy | Decision | Evidence | Score | Net Return After Costs | Max DD | Closed Trades |
|---:|---|---|---|---|---:|---:|---:|---:|
| 1 | `breakout_default` | `breakout_donchian` | `improve` | `synthetic_only` | `0.741007` | `15.4740%` | `8.4781%` | `5` |
| 2 | `ema_cross_default` | `ema_cross` | `improve` | `synthetic_only` | `0.594687` | `6.8263%` | `6.2510%` | `2` |
| 3 | `mean_reversion_default` | `mean_reversion_rsi` | `freeze` | `insufficient` | `0.145834` | `0.0017%` | `0.1945%` | `0` |
| 4 | `momentum_default` | `momentum` | `retire` | `synthetic_only` | `0.145493` | `-3.7723%` | `31.0268%` | `15` |
| 5 | `composite_hybrid_v1_breakout_sma200_research` | `composite_hybrid_v1` | `freeze` | `insufficient` | `0.132800` | `0.0000%` | `0.0000%` | `0` |
| 6 | `sma_200_trend_default` | `sma_200_trend` | `freeze` | `insufficient` | `0.132800` | `0.0000%` | `0.0000%` | `0` |
| 7 | `volatility_reversal_default` | `volatility_reversal` | `freeze` | `insufficient` | `0.132800` | `0.0000%` | `0.0000%` | `0` |
| 8 | `gap_fill_default` | `gap_fill` | `freeze` | `insufficient` | `0.132800` | `0.0000%` | `0.0000%` | `0` |
| 9 | `breakout_volume_default` | `breakout_volume` | `freeze` | `insufficient` | `0.132800` | `0.0000%` | `0.0000%` | `0` |
| 10 | `pullback_recovery_default` | `pullback_recovery` | `freeze` | `insufficient` | `0.004119` | `-2.0023%` | `16.1717%` | `0` |

## Composite Row Detail

SHOWN:
- Rank: `5/10`
- Decision: `freeze`
- Evidence status: `insufficient`
- Confidence: `low`
- Leaderboard score: `0.132800`
- Net return after costs: `0.0000%`
- Slippage sensitivity: `0.0000%`
- Max drawdown: `0.0000%`
- Closed trades: `0`
- Closed-trade window count: `0`
- Active window count: `0`

Research acceptance:
- accepted: `false`
- status: `not_accepted`

Blockers:
- Persisted paper history only has `0` closed trades; current research floor
  requires `30`.
- Only `0` represented windows produced realized closed trades; current
  research floor requires `3`.
- Post-cost return is not positive.
- Stressed slippage turns the current post-cost result non-positive.
- Evidence status is `insufficient`; current research floor requires
  `paper_supported`.
- Confidence is `low`; current research floor requires at least `medium`.

## Window Participation

The composite candidate produced no trades in any default evidence window.

| Window | Bars | Warmup | Rank | Trades | Closed Trades | Exposure |
|---|---:|---:|---:|---:|---:|---:|
| `synthetic_default` | `180` | `50` | `4` | `0` | `0` | `0.0` |
| `trend_reversal` | `140` | `20` | `4` | `0` | `0` | `0.0` |
| `breakout_pulse` | `120` | `20` | `4` | `0` | `0` | `0.0` |
| `double_reversal` | `125` | `15` | `4` | `0` | `0` | `0.0` |
| `range_snapback` | `144` | `15` | `3` | `0` | `0` | `0.0` |
| `false_breakout_whipsaw` | `108` | `20` | `3` | `0` | `0` | `0.0` |
| `event_trend_grind` | `104` | `20` | `4` | `0` | `0` | `0.0` |
| `low_vol_fee_bleed` | `108` | `20` | `4` | `0` | `0` | `0.0` |

## Interpretation

SHOWN:
- `services/strategies/es_daily_trend.py` returns `hold` with reason
  `insufficient_history` when `len(ohlcv) < sma_period`.
- The composite candidate uses `sma_200_trend` as confirmer.
- The default evidence windows have `104` to `180` bars, below the confirmer's
  `200` bar default.
- The composite candidate produced no trades across the evidence pack.

INFERENCE:
- The current comparison pack is too short for a 200-SMA confirmer to participate.
- The current composite candidate is not rejected for bad realized PnL; it is
  rejected because it produced no realized participation.

## Recommendation

Do not advance `composite_hybrid_v1_breakout_sma200_research` to paper.

The next coherent engineering task is one of:
- Add a longer research-only evidence window with at least `220` bars so the
  `sma_200_trend` confirmer can warm up and the composite can be compared
  fairly.
- Define a separate versioned composite candidate with a shorter confirmer, for
  example a 50-SMA trend confirmer, and run it through the same research-only
  comparison path.

Do not start a persistent paper campaign until one of those comparison paths
produces accepted evidence with realized participation.

## Acceptance State

Risk: HIGH

Reason:
- This is financial strategy comparison evidence that can influence future
  campaign selection.

Acceptance state: READY_FOR_INDEPENDENT_REVIEW


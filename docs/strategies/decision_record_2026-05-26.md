# Strategy Decision Record — 2026-05-26

## Scope

This record reflects the current repo state on 2026-05-26.

Guardrails:
- crypto-first scope
- paper-heavy defaults remain active
- live trading is guarded and fail-closed
- stock support is not proven
- shorting is not fully validated
- this is not a profitability claim

## Safety Gate

Phase 1 safety pack should be rerun before relying on this record.

## Evaluation Inputs

- symbol: `BTC/USDT`
- windows: `8` deterministic synthetic windows
- initial cash: `10000`
- fees: `10 bps`
- slippage: `5 bps`
- paper-history source: `trade_journal_sqlite`
- paper-history status: `available`
- paper-history journal: `/Users/baitus/Downloads/crypto-bot-pro/.cbp_state/data/trade_journal.sqlite`
- paper-history fills: `14`
- strategy-feedback source: `trade_journal_sqlite`
- strategy-feedback status: `available`
- strategy-feedback journal: `/Users/baitus/Downloads/crypto-bot-pro/.cbp_state/data/trade_journal.sqlite`
- strategy-feedback strategies: `1`
- evidence artifact: `/Users/baitus/Downloads/crypto-bot-pro/.cbp_state/data/strategy_evidence/strategy_evidence.latest.json`

Window set:
- `synthetic_default`: Synthetic Default Benchmark (180 bars)
- `trend_reversal`: Trend Reversal (140 bars)
- `breakout_pulse`: Breakout Pulse (120 bars)
- `double_reversal`: Double Reversal (125 bars)
- `range_snapback`: Range Snapback (144 bars)
- `false_breakout_whipsaw`: False Breakout Whipsaw (108 bars)
- `event_trend_grind`: Event Trend Grind (104 bars)
- `low_vol_fee_bleed`: Low-Vol Fee Bleed (108 bars)

Important limitation:
- these windows are deterministic synthetic benchmarks, not live or market-history proof
- this cycle is stronger than a single-window pass, but it still does not prove profitability or promotion readiness by itself
- persisted paper-history status for this run is `available`

## Run-to-Run Comparison

- previous run: `2026-05-18T19:03:12Z`
- current run: `2026-05-26T00:00:31Z`
- top strategy previous: `breakout_donchian`
- top strategy current: `breakout_donchian`
- top strategy changed: `no`
- improved comparisons: `1`
- degraded comparisons: `3`
- unchanged comparisons: `4`
- new comparisons: `0`

Summary: 1 strategy comparison(s) improved and 3 degraded versus the prior persisted evidence run.

- recent persisted runs considered: `5`
- distinct recent top strategies: `1`
- current top streak: `5`

Recent trend: Top strategy has remained breakout_donchian across the last 5 persisted evidence runs.

Comparison detail:
- `breakout_donchian` moved `unchanged`; rank `1` -> `1`, decision `improve` -> `improve`.
- `ema_cross` moved `unchanged`; rank `2` -> `2`, decision `improve` -> `improve`.
- `mean_reversion_rsi` moved `unchanged`; rank `3` -> `3`, decision `freeze` -> `freeze`.
- `momentum` moved `unchanged`; rank `4` -> `4`, decision `retire` -> `retire`.
- `sma_200_trend` moved `improved`; rank `8` -> `5`, decision `freeze` -> `freeze`.

## Results

### `breakout_donchian`
- candidate: `breakout_default`
- rank: `1`
- aggregate leaderboard score: `0.741007`
- base leaderboard score: `0.741007`
- average net return after costs: `+15.47%`
- worst-window return: `+0.00%`
- worst drawdown: `8.48%`
- closed trades: `5`
- active windows: `6` / `8`
- positive windows: `6` / `8`
- best window: `trend_reversal`
- worst window: `range_snapback`
- evidence status: `synthetic_only`
- confidence: `low`
- paper-history: No strategy-attributed persisted paper-history fills are available yet.
- strategy feedback: No persisted strategy feedback summary recorded.
- feedback weighting: `missing`
- research acceptance: `not_accepted`
- research summary: `breakout_donchian` does not meet the current research-acceptance floor yet.
- walk-forward: `ok`
- walk-forward windows: `5`

Decision: `improve`

Reason:
- It remains the strongest aggregate candidate, but the evidence is still not strong enough for a stronger decision.
- Evidence note: Persisted paper-history exists, but this strategy has no attributed paper fills yet, so the decision still relies on synthetic windows.
- Feedback weighting: No persisted strategy feedback row is available yet.
- Biggest weakness: Expected failure regimes are still concentrated in chop, low vol.

Next work:
- Test false-breakout handling and exit discipline over a longer multi-window pack.

- Research blocker: Persisted paper history only has 0 closed trade(s); the current research floor requires 30.
- Research blocker: Evidence status is synthetic_only; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.
- Walk-forward summary: +4.44% average test return, 0.94% average test drawdown, 80% non-negative test windows, 1 closed test trade(s).

### `ema_cross`
- candidate: `ema_cross_default`
- rank: `2`
- aggregate leaderboard score: `0.594687`
- base leaderboard score: `0.594687`
- average net return after costs: `+6.83%`
- worst-window return: `-3.55%`
- worst drawdown: `6.25%`
- closed trades: `2`
- active windows: `4` / `8`
- positive windows: `3` / `8`
- best window: `trend_reversal`
- worst window: `range_snapback`
- evidence status: `synthetic_only`
- confidence: `low`
- paper-history: No strategy-attributed persisted paper-history fills are available yet.
- strategy feedback: No persisted strategy feedback summary recorded.
- feedback weighting: `missing`
- research acceptance: `not_accepted`
- research summary: `ema_cross` does not meet the current research-acceptance floor yet.
- walk-forward: `ok`
- walk-forward windows: `5`

Decision: `improve`

Reason:
- It remains viable, but the evidence is still weaker than the top aggregate candidate.
- Evidence note: Persisted paper-history exists, but this strategy has no attributed paper fills yet, so the decision still relies on synthetic windows.
- Feedback weighting: No persisted strategy feedback row is available yet.
- Biggest weakness: Performance is fragile across windows, not just thin in sample size.

Next work:
- Tighten chop and low-vol invalidation behavior, then rerun the same window set.

- Research blocker: Persisted paper history only has 0 closed trade(s); the current research floor requires 30.
- Research blocker: Only 2 represented window(s) produced realized closed trades; the current research floor requires 3.
- Research blocker: Evidence status is synthetic_only; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.
- Walk-forward summary: -2.86% average test return, 2.86% average test drawdown, 60% non-negative test windows, 2 closed test trade(s).

### `mean_reversion_rsi`
- candidate: `mean_reversion_default`
- rank: `3`
- aggregate leaderboard score: `0.145834`
- base leaderboard score: `0.145834`
- average net return after costs: `+0.00%`
- worst-window return: `-0.06%`
- worst drawdown: `0.19%`
- closed trades: `0`
- active windows: `2` / `8`
- positive windows: `1` / `8`
- best window: `low_vol_fee_bleed`
- worst window: `false_breakout_whipsaw`
- evidence status: `insufficient`
- confidence: `low`
- paper-history: No strategy-attributed persisted paper-history fills are available yet.
- strategy feedback: No persisted strategy feedback summary recorded.
- feedback weighting: `missing`
- research acceptance: `not_accepted`
- research summary: `mean_reversion_rsi` does not meet the current research-acceptance floor yet.
- walk-forward: `ok`
- walk-forward windows: `5`

Decision: `freeze`

Reason:
- No realized closed-trade evidence exists across the current window set.
- Evidence note: No realized closed-trade participation exists across the current evidence windows.
- Feedback weighting: No persisted strategy feedback row is available yet.
- Biggest weakness: No realized trading participation across the current evidence windows.

Next work:
- Review entry filters and regime assumptions before spending more effort on tuning.

- Research blocker: Persisted paper history only has 0 closed trade(s); the current research floor requires 30.
- Research blocker: Only 0 represented window(s) produced realized closed trades; the current research floor requires 3.
- Research blocker: Stressed slippage turns the current post-cost result non-positive.
- Research blocker: Evidence status is insufficient; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.
- Walk-forward summary: +0.00% average test return, 0.00% average test drawdown, 100% non-negative test windows, 0 closed test trade(s).

### `momentum`
- candidate: `momentum_default`
- rank: `4`
- aggregate leaderboard score: `0.145493`
- base leaderboard score: `0.145493`
- average net return after costs: `-3.77%`
- worst-window return: `-30.18%`
- worst drawdown: `31.03%`
- closed trades: `15`
- active windows: `1` / `8`
- positive windows: `0` / `8`
- best window: `synthetic_default`
- worst window: `range_snapback`
- evidence status: `synthetic_only`
- confidence: `low`
- paper-history: No strategy-attributed persisted paper-history fills are available yet.
- strategy feedback: No persisted strategy feedback summary recorded.
- feedback weighting: `missing`
- research acceptance: `not_accepted`
- research summary: `momentum` does not meet the current research-acceptance floor yet.
- walk-forward: `ok`
- walk-forward windows: `5`

Decision: `retire`

Reason:
- Aggregate post-cost return is negative and the strategy is not robust across windows.
- Evidence note: Persisted paper-history exists, but this strategy has no attributed paper fills yet, so the decision still relies on synthetic windows.
- Feedback weighting: No persisted strategy feedback row is available yet.
- Biggest weakness: Performance is fragile across windows, not just thin in sample size.

Next work:
- Rerun the same evidence pack after the next smallest strategy rule adjustment.

- Research blocker: Persisted paper history only has 0 closed trade(s); the current research floor requires 30.
- Research blocker: Only 1 represented window(s) produced realized closed trades; the current research floor requires 3.
- Research blocker: Post-cost return is not positive.
- Research blocker: Stressed slippage turns the current post-cost result non-positive.
- Research blocker: Max drawdown is 31.03%; the current research floor requires 10.00% or less.
- Research blocker: Evidence status is synthetic_only; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.
- Walk-forward summary: -1.32% average test return, 1.32% average test drawdown, 80% non-negative test windows, 1 closed test trade(s).

### `sma_200_trend`
- candidate: `sma_200_trend_default`
- rank: `5`
- aggregate leaderboard score: `0.132800`
- base leaderboard score: `0.132800`
- average net return after costs: `+0.00%`
- worst-window return: `+0.00%`
- worst drawdown: `0.00%`
- closed trades: `0`
- active windows: `0` / `8`
- positive windows: `0` / `8`
- best window: `synthetic_default`
- worst window: `synthetic_default`
- evidence status: `insufficient`
- confidence: `low`
- paper-history: 7 closed trade(s), +35.75 net realized PnL, 28.6% win rate across 14 fill(s).
- strategy feedback: 7 closed trade(s), +35.75 net realized PnL, +5.11 expectancy per closed trade, 28.6% win rate.
- feedback weighting: `neutral`
- research acceptance: `not_accepted`
- research summary: `sma_200_trend` does not meet the current research-acceptance floor yet.
- walk-forward: `ok`
- walk-forward windows: `5`

Decision: `freeze`

Reason:
- No realized closed-trade evidence exists across the current window set. Supplemental paper-history evidence is positive across 7 closed trade(s), but it is still not enough to justify promotion.
- Evidence note: No realized closed-trade participation exists across the current evidence windows.
- Feedback weighting: Persisted paper feedback is mixed, so no leaderboard weighting adjustment is applied.
- Biggest weakness: No realized trading participation across the current evidence windows.

Next work:
- Review entry filters and regime assumptions before spending more effort on tuning.

- Research blocker: Persisted paper history only has 7 closed trade(s); the current research floor requires 30.
- Research blocker: Only 0 represented window(s) produced realized closed trades; the current research floor requires 3.
- Research blocker: Post-cost return is not positive.
- Research blocker: Stressed slippage turns the current post-cost result non-positive.
- Research blocker: Evidence status is insufficient; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.
- Walk-forward summary: +4.27% average test return, 0.03% average test drawdown, 100% non-negative test windows, 0 closed test trade(s).

### `volatility_reversal`
- candidate: `volatility_reversal_default`
- rank: `6`
- aggregate leaderboard score: `0.132800`
- base leaderboard score: `0.132800`
- average net return after costs: `+0.00%`
- worst-window return: `+0.00%`
- worst drawdown: `0.00%`
- closed trades: `0`
- active windows: `0` / `8`
- positive windows: `0` / `8`
- best window: `synthetic_default`
- worst window: `synthetic_default`
- evidence status: `insufficient`
- confidence: `low`
- paper-history: No strategy-attributed persisted paper-history fills are available yet.
- strategy feedback: No persisted strategy feedback summary recorded.
- feedback weighting: `missing`
- research acceptance: `not_accepted`
- research summary: `volatility_reversal` does not meet the current research-acceptance floor yet.
- walk-forward: `ok`
- walk-forward windows: `5`

Decision: `freeze`

Reason:
- No realized closed-trade evidence exists across the current window set.
- Evidence note: No realized closed-trade participation exists across the current evidence windows.
- Feedback weighting: No persisted strategy feedback row is available yet.
- Biggest weakness: No realized trading participation across the current evidence windows.

Next work:
- Review entry filters and regime assumptions before spending more effort on tuning.

- Research blocker: Persisted paper history only has 0 closed trade(s); the current research floor requires 30.
- Research blocker: Only 0 represented window(s) produced realized closed trades; the current research floor requires 3.
- Research blocker: Post-cost return is not positive.
- Research blocker: Stressed slippage turns the current post-cost result non-positive.
- Research blocker: Evidence status is insufficient; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.
- Walk-forward summary: +0.00% average test return, 0.00% average test drawdown, 100% non-negative test windows, 0 closed test trade(s).

### `gap_fill`
- candidate: `gap_fill_default`
- rank: `7`
- aggregate leaderboard score: `0.132800`
- base leaderboard score: `0.132800`
- average net return after costs: `+0.00%`
- worst-window return: `+0.00%`
- worst drawdown: `0.00%`
- closed trades: `0`
- active windows: `0` / `8`
- positive windows: `0` / `8`
- best window: `synthetic_default`
- worst window: `synthetic_default`
- evidence status: `insufficient`
- confidence: `low`
- paper-history: No strategy-attributed persisted paper-history fills are available yet.
- strategy feedback: No persisted strategy feedback summary recorded.
- feedback weighting: `missing`
- research acceptance: `not_accepted`
- research summary: `gap_fill` does not meet the current research-acceptance floor yet.
- walk-forward: `ok`
- walk-forward windows: `5`

Decision: `freeze`

Reason:
- No realized closed-trade evidence exists across the current window set.
- Evidence note: No realized closed-trade participation exists across the current evidence windows.
- Feedback weighting: No persisted strategy feedback row is available yet.
- Biggest weakness: No realized trading participation across the current evidence windows.

Next work:
- Review entry filters and regime assumptions before spending more effort on tuning.

- Research blocker: Persisted paper history only has 0 closed trade(s); the current research floor requires 30.
- Research blocker: Only 0 represented window(s) produced realized closed trades; the current research floor requires 3.
- Research blocker: Post-cost return is not positive.
- Research blocker: Stressed slippage turns the current post-cost result non-positive.
- Research blocker: Evidence status is insufficient; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.
- Walk-forward summary: +0.00% average test return, 0.00% average test drawdown, 100% non-negative test windows, 0 closed test trade(s).

### `breakout_volume`
- candidate: `breakout_volume_default`
- rank: `8`
- aggregate leaderboard score: `0.132800`
- base leaderboard score: `0.132800`
- average net return after costs: `+0.00%`
- worst-window return: `+0.00%`
- worst drawdown: `0.00%`
- closed trades: `0`
- active windows: `0` / `8`
- positive windows: `0` / `8`
- best window: `synthetic_default`
- worst window: `synthetic_default`
- evidence status: `insufficient`
- confidence: `low`
- paper-history: No strategy-attributed persisted paper-history fills are available yet.
- strategy feedback: No persisted strategy feedback summary recorded.
- feedback weighting: `missing`
- research acceptance: `not_accepted`
- research summary: `breakout_volume` does not meet the current research-acceptance floor yet.
- walk-forward: `ok`
- walk-forward windows: `5`

Decision: `freeze`

Reason:
- No realized closed-trade evidence exists across the current window set.
- Evidence note: No realized closed-trade participation exists across the current evidence windows.
- Feedback weighting: No persisted strategy feedback row is available yet.
- Biggest weakness: No realized trading participation across the current evidence windows.

Next work:
- Review entry filters and regime assumptions before spending more effort on tuning.

- Research blocker: Persisted paper history only has 0 closed trade(s); the current research floor requires 30.
- Research blocker: Only 0 represented window(s) produced realized closed trades; the current research floor requires 3.
- Research blocker: Post-cost return is not positive.
- Research blocker: Stressed slippage turns the current post-cost result non-positive.
- Research blocker: Evidence status is insufficient; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.
- Walk-forward summary: +0.00% average test return, 0.00% average test drawdown, 100% non-negative test windows, 0 closed test trade(s).

## Forced Decision Set

Keep:
- none

Improve:
- `breakout_donchian`
- `ema_cross`

Freeze:
- `mean_reversion_rsi`
- `sma_200_trend`
- `volatility_reversal`
- `gap_fill`
- `breakout_volume`

Retire:
- `momentum`

## Operator Interpretation

What this does **not** mean:
- no strategy is proven profitable
- no strategy is approved for real-live promotion
- no claim is made about validated short support

What it **does** mean:
- the strategy ranking now reflects multiple deterministic windows instead of one benchmark pass
- inactive or low-participation candidates are easier to challenge with explicit evidence
- persisted paper-history evidence is included when available, but missing paper history is now explicit instead of silent
- promotion decisions should still remain conservative until broader paper or sandbox evidence exists

## Follow-up Gaps

The next improvement to the evaluation layer should be:
- extend persisted evidence comparison beyond the immediately previous artifact
- grow the trade journal so paper-history evidence is no longer missing or thin
- improve deterministic windows where strategies still show no realized closed-trade participation

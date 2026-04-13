# Strategy Decision Record — 2026-04-08

## Scope

This record reflects the current repo state on 2026-04-08.

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

- symbol: `BTC/USD`
- windows: `8` deterministic synthetic windows
- initial cash: `10000`
- fees: `10 bps`
- slippage: `5 bps`
- paper-history source: `trade_journal_sqlite`
- paper-history status: `available`
- paper-history journal: `<your-repo-path>/.cbp_state/data/trade_journal.sqlite`
- paper-history fills: `44`
- evidence artifact: `<your-repo-path>/.cbp_state/data/strategy_evidence/strategy_evidence.latest.json`

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

- previous run: `2026-04-07T17:49:33Z`
- current run: `2026-04-08T19:11:49Z`
- top strategy previous: `breakout_donchian`
- top strategy current: `breakout_donchian`
- top strategy changed: `no`
- improved comparisons: `0`
- degraded comparisons: `0`
- unchanged comparisons: `3`
- new comparisons: `0`

Summary: Current strategy evidence is unchanged versus the prior persisted evidence run.

- recent persisted runs considered: `5`
- distinct recent top strategies: `1`
- current top streak: `5`

Recent trend: Top strategy has remained breakout_donchian across the last 5 persisted evidence runs.

Comparison detail:
- `breakout_donchian` moved `unchanged`; rank `1` -> `1`, decision `improve` -> `improve`.
- `ema_cross` moved `unchanged`; rank `2` -> `2`, decision `improve` -> `improve`.
- `mean_reversion_rsi` moved `unchanged`; rank `3` -> `3`, decision `freeze` -> `freeze`.

## Results

### `breakout_donchian`
- candidate: `breakout_default`
- rank: `1`
- aggregate leaderboard score: `0.576000`
- average net return after costs: `+15.47%`
- worst-window return: `+0.00%`
- worst drawdown: `8.48%`
- closed trades: `5`
- active windows: `6` / `8`
- positive windows: `6` / `8`
- best window: `trend_reversal`
- worst window: `range_snapback`
- evidence status: `paper_thin`
- confidence: `low`
- paper-history: 1 closed trade(s), -0.19 net realized PnL, 0.0% win rate across 2 fill(s).
- research acceptance: `not_accepted`
- research summary: `breakout_donchian` does not meet the current research-acceptance floor yet.

Decision: `improve`

Reason:
- It remains the strongest aggregate candidate, but the evidence is still not strong enough for a stronger decision.
- Evidence note: Persisted paper-history exists, but the sample is still too thin to confirm the synthetic ranking.
- Biggest weakness: Expected failure regimes are still concentrated in chop, low vol.

Next work:
- Test false-breakout handling and exit discipline over a longer multi-window pack.

- Research blocker: Persisted paper history only has 1 closed trade(s); the current research floor requires 30.
- Research blocker: Evidence status is paper_thin; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.

### `ema_cross`
- candidate: `ema_cross_default`
- rank: `2`
- aggregate leaderboard score: `0.447904`
- average net return after costs: `+6.83%`
- worst-window return: `-3.55%`
- worst drawdown: `6.25%`
- closed trades: `2`
- active windows: `4` / `8`
- positive windows: `3` / `8`
- best window: `trend_reversal`
- worst window: `range_snapback`
- evidence status: `paper_thin`
- confidence: `low`
- paper-history: 0 closed trade(s), -0.05 net realized PnL, 0.0% win rate across 1 fill(s).
- research acceptance: `not_accepted`
- research summary: `ema_cross` does not meet the current research-acceptance floor yet.

Decision: `improve`

Reason:
- It remains viable, but the evidence is still weaker than the top aggregate candidate.
- Evidence note: Persisted paper-history exists, but the sample is still too thin to confirm the synthetic ranking.
- Biggest weakness: Performance is fragile across windows, not just thin in sample size.

Next work:
- Tighten chop and low-vol invalidation behavior, then rerun the same window set.

- Research blocker: Persisted paper history only has 0 closed trade(s); the current research floor requires 30.
- Research blocker: Only 2 represented window(s) produced realized closed trades; the current research floor requires 3.
- Research blocker: Evidence status is paper_thin; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.

### `mean_reversion_rsi`
- candidate: `mean_reversion_default`
- rank: `3`
- aggregate leaderboard score: `0.074000`
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
- paper-history: 20 closed trade(s), -3.50 net realized PnL, 0.0% win rate across 41 fill(s).
- research acceptance: `not_accepted`
- research summary: `mean_reversion_rsi` does not meet the current research-acceptance floor yet.

Decision: `freeze`

Reason:
- No realized closed-trade evidence exists across the current window set. Persisted paper-history evidence is negative after 20 closed trade(s), so the decision stays conservative.
- Evidence note: No realized closed-trade participation exists across the current evidence windows.
- Biggest weakness: No realized trading participation across the current evidence windows.

Next work:
- Review entry filters and regime assumptions before spending more effort on tuning.

- Research blocker: Persisted paper history only has 20 closed trade(s); the current research floor requires 30.
- Research blocker: Only 0 represented window(s) produced realized closed trades; the current research floor requires 3.
- Research blocker: Stressed slippage turns the current post-cost result non-positive.
- Research blocker: Evidence status is insufficient; the current research floor requires paper_supported.
- Research blocker: Confidence is low; the current research floor requires at least medium confidence.

## Forced Decision Set

Keep:
- none

Improve:
- `breakout_donchian`
- `ema_cross`

Freeze:
- `mean_reversion_rsi`

Retire:
- none

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

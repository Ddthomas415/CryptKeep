# Strategy Decision Record — 2026-03-26

## Scope

This record reflects the current repo state on 2026-03-26.

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

- symbol: `SOL/USD`
- windows: `5` deterministic synthetic windows
- initial cash: `10000`
- fees: `10 bps`
- slippage: `5 bps`
- paper-history source: `trade_journal_sqlite`
- paper-history status: `available`
- paper-history journal: `/Users/baitus/Downloads/crypto-bot-pro/.cbp_state/data/trade_journal.sqlite`
- paper-history fills: `101`
- evidence artifact: `/Users/baitus/Downloads/crypto-bot-pro/.cbp_state/data/strategy_evidence/strategy_evidence.latest.json`

Window set:
- `synthetic_default`: Synthetic Default Benchmark (180 bars)
- `trend_reversal`: Trend Reversal (140 bars)
- `breakout_pulse`: Breakout Pulse (120 bars)
- `double_reversal`: Double Reversal (125 bars)
- `range_snapback`: Range Snapback (144 bars)

Important limitation:
- these windows are deterministic synthetic benchmarks, not live or market-history proof
- this cycle is stronger than a single-window pass, but it still does not prove profitability or promotion readiness by itself
- persisted paper-history status for this run is `available`

## Run-to-Run Comparison

- previous run: `2026-03-26T11:15:41Z`
- current run: `2026-03-26T12:39:28Z`
- top strategy previous: `breakout_donchian`
- top strategy current: `breakout_donchian`
- top strategy changed: `no`
- improved comparisons: `0`
- degraded comparisons: `0`
- unchanged comparisons: `3`
- new comparisons: `0`

Summary: Current strategy evidence is unchanged versus the prior persisted evidence run.

Comparison detail:
- `breakout_donchian` moved `unchanged`; rank `1` -> `1`, decision `improve` -> `improve`.
- `ema_cross` moved `unchanged`; rank `2` -> `2`, decision `freeze` -> `freeze`.
- `mean_reversion_rsi` moved `unchanged`; rank `3` -> `3`, decision `freeze` -> `freeze`.

## Results

### `breakout_donchian`
- candidate: `breakout_default`
- rank: `1`
- aggregate leaderboard score: `0.578153`
- average net return after costs: `+19.01%`
- worst-window return: `+0.00%`
- worst drawdown: `7.83%`
- closed trades: `4`
- active windows: `4` / `5`
- positive windows: `4` / `5`
- best window: `trend_reversal`
- worst window: `range_snapback`
- evidence status: `paper_thin`
- confidence: `low`
- paper-history: 2 closed trade(s), -0.00 net realized PnL, 0.0% win rate across 4 fill(s).

Decision: `improve`

Reason:
- It is the strongest aggregate candidate with enough closed-trade evidence for continued research. Persisted paper-history evidence is negative after 2 closed trade(s), so the decision stays conservative.
- Evidence note: Persisted paper-history exists, but the sample is still too thin to confirm the synthetic ranking.
- Biggest weakness: Expected failure regimes are still concentrated in chop, low vol.

Next work:
- Test false-breakout handling and exit discipline over a longer multi-window pack.

### `ema_cross`
- candidate: `ema_cross_default`
- rank: `2`
- aggregate leaderboard score: `0.486666`
- average net return after costs: `+10.92%`
- worst-window return: `-3.55%`
- worst drawdown: `6.25%`
- closed trades: `2`
- active windows: `4` / `5`
- positive windows: `3` / `5`
- best window: `trend_reversal`
- worst window: `range_snapback`
- evidence status: `paper_thin`
- confidence: `low`
- paper-history: 2 closed trade(s), -0.00 net realized PnL, 0.0% win rate across 5 fill(s).

Decision: `freeze`

Reason:
- It remains viable, but the evidence is still weaker than the top aggregate candidate. Persisted paper-history evidence is negative after 2 closed trade(s), so the decision stays conservative.
- Evidence note: Persisted paper-history exists, but the sample is still too thin to confirm the synthetic ranking.
- Biggest weakness: The sample is still small relative to the confidence needed for promotion.

Next work:
- Tighten chop and low-vol invalidation behavior, then rerun the same window set.

### `mean_reversion_rsi`
- candidate: `mean_reversion_default`
- rank: `3`
- aggregate leaderboard score: `0.074000`
- average net return after costs: `+0.00%`
- worst-window return: `+0.00%`
- worst drawdown: `0.00%`
- closed trades: `0`
- active windows: `0` / `5`
- positive windows: `0` / `5`
- best window: `synthetic_default`
- worst window: `synthetic_default`
- evidence status: `insufficient`
- confidence: `low`
- paper-history: 46 closed trade(s), -2.55 net realized PnL, 2.2% win rate across 92 fill(s).

Decision: `freeze`

Reason:
- No realized closed-trade evidence exists across the current window set. Persisted paper-history evidence is negative after 46 closed trade(s), so the decision stays conservative.
- Evidence note: No realized closed-trade participation exists across the current evidence windows.
- Biggest weakness: No realized trading participation across the current evidence windows.

Next work:
- Review entry filters and regime assumptions before spending more effort on tuning.

## Forced Decision Set

Keep:
- none

Improve:
- `breakout_donchian`

Freeze:
- `ema_cross`
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
- persist multiple evidence runs and compare deltas over time
- grow the trade journal so paper-history evidence is no longer missing or thin
- feed the persisted evidence artifact into the Home Digest instead of rebuilding a single-window summary on demand

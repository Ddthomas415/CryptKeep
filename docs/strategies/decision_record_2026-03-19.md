# Strategy Decision Record — 2026-03-19

## Scope

This record reflects the current repo state on 2026-03-19.

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
- windows: `5` deterministic synthetic windows
- initial cash: `10000`
- fees: `10 bps`
- slippage: `5 bps`
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

Decision: `keep`

Reason:
- It is the strongest aggregate candidate with enough closed-trade evidence for continued research.
- Biggest weakness: The sample is still small relative to the confidence needed for promotion.

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

Decision: `improve`

Reason:
- It remains viable, but the evidence is still weaker than the top aggregate candidate.
- Biggest weakness: Expected failure regimes are still concentrated in chop, low vol.

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

Decision: `freeze`

Reason:
- No realized closed-trade evidence exists across the current window set.
- Biggest weakness: No realized trading participation across the current evidence windows.

Next work:
- Review entry filters and regime assumptions before spending more effort on tuning.

## Forced Decision Set

Keep:
- `breakout_donchian`

Improve:
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
- promotion decisions should still remain conservative until broader paper or sandbox evidence exists

## Follow-up Gaps

The next improvement to the evaluation layer should be:
- persist multiple evidence runs and compare deltas over time
- add broader paper-history inputs so the cycle is not purely synthetic
- feed the persisted evidence artifact into the Home Digest instead of rebuilding a single-window summary on demand

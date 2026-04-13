# Live Failure Regime Study (2026-03-26)

## Scope

Question:

- what failure regimes are actually showing up in the persisted paper losses for the currently active strategies?

Strategies reviewed:

- `mean_reversion_rsi`
- `breakout_donchian`

## Method

Inputs:

- persisted paper fills from `<your-repo-path>/.cbp_state/data/trade_journal.sqlite`
- closed trades reconstructed with `services.analytics.journal_analytics.fifo_pnl_from_fills`
- market context classified with `services.backtest.regimes.classify_market_regimes`

Market context source:

- public Coinbase `1m` OHLCV fetched around each closed trade entry/exit window

Important limitation:

- the managed paper campaigns that produced these fills mostly used the runner's default `synthetic_mid_ohlcv`, not public OHLCV directly
- this study therefore uses public `1m` candles as a **proxy** for market context around the real fills
- many paper trades opened and closed within seconds, so the dominant in-trade regime is often unavailable; entry/exit regime labels are more reliable than within-trade counts

## Mean Reversion RSI

Persisted paper summary:

- `46` closed trades
- `1` win / `45` losses
- `-2.552960689247996` net realized PnL

Per-symbol paper summary:

- `BTC/USD`: `14` closed trades, `0.0%` win rate, `-2.4390982508105` net realized PnL
- `ETH/USD`: `21` closed trades, `4.76%` win rate, `-0.11148818220062084` net realized PnL
- `SOL/USD`: `11` closed trades, `0.0%` win rate, `-0.0023742562368749285` net realized PnL

Regime mapping result:

- every sampled losing closed trade mapped to `low_vol` at entry
- exits also overwhelmingly mapped to `low_vol`
- the public-proxy study did **not** show these losses clustering in:
  - `bear`
  - `bull`
  - `high_vol`

Interpretation:

- the current live paper losses are behaving more like low-volatility fee bleed / micro-churn than like the currently documented mean-reversion failure regimes
- this does **not** prove the hypothesis is wrong
- it does show that the current hypothesis and deterministic evaluation pack are under-describing an observed failure mode

Implication:

- before any preset tuning, the mean-reversion hypothesis should be treated as missing an explicit low-vol / microstructure failure case

## Breakout Donchian

Persisted paper summary:

- `3` closed trades
- `0` wins / `3` losses
- `-0.18949904680330537` net realized PnL

Observed closed-trade symbols in the journal:

- `APR/USD`
- `2Z/USD`
- `BTC/USD`

Regime mapping result:

- `APR/USD`: entry/exit proxied as `bear`
- `2Z/USD`: entry/exit proxied as `low_vol`
- `BTC/USD`: entry/exit proxied as `low_vol`

Important qualification:

- the `BTC/USD` breakout loss on `2026-03-26T13:50:05Z -> 2026-03-26T13:50:12Z` happened before the runner fix in `dad0d94`
- that trade was contaminated by the old `buy -> hold -> forced exit` bug and should **not** be treated as clean breakout evidence

Interpretation:

- the clean breakout paper sample is still too small to support strong conclusions
- what exists currently looks more consistent with:
  - low-vol / thin-liquidity environments
  - possibly unsupported or questionable symbol scope
than with a validated continuation setup failing under healthy breakout conditions

Open question:

- `2Z/USD` appears in persisted breakout paper history; it is unclear from current repo truth whether that symbol should be considered an intended research symbol or a legacy artifact

## What This Changes

It is now safer to say:

- `mean_reversion_rsi` is not just "negative on paper"; its current losses cluster in low-vol micro conditions that the hypothesis/evaluation layer does not currently represent well
- `breakout_donchian` still lacks a clean enough paper sample to justify more preset tuning, especially after excluding the bug-contaminated `BTC/USD` loss

Update after the expanded evidence pack:

- the deterministic suite now includes `low_vol_fee_bleed`, so the evaluation layer does represent this failure mode better than it did when this note was first written
- that addition increased `mean_reversion_rsi` participation in deterministic windows, but it still did not create realized closed-trade evidence strong enough to change the strategy decision
- the repo truth therefore moved from "missing low-vol fee-bleed coverage" to "low-vol fee-bleed is partially represented, but still not diagnostic enough on its own"

It is **not** safe to say:

- that `mean_reversion_rsi` is disproven in all regimes
- that `breakout_donchian` has a validated false-breakout problem from current paper history alone

## Recommended Follow-up

Do next:

- strengthen the low-vol failure-regime pack so it produces more diagnostic realized participation, not just sparse entries
- keep the breakout strategy conservative until a cleaner post-fix paper sample exists
- confirm whether thin or unusual symbols such as `2Z/USD` should be part of the managed evidence universe at all

Do not do next:

- do not tune `mean_reversion_rsi` thresholds yet
- do not retune `breakout_donchian` again based on the current paper-history sample

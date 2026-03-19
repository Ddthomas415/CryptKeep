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

Phase 1 safety pack was rerun before evaluation.

Result:
- `make phase1-safety`
- `33 passed`
- direct raw order creation enforcement still passed

## Evaluation Inputs

Current evaluation cycle used:
- symbol: `BTC/USDT`
- candles: synthetic benchmark series from `dashboard.services.operator_tools.synthetic_ohlcv(180)`
- warmup: `50`
- initial cash: `10000`
- fees: `10 bps`
- slippage: `5 bps`
- leaderboard path: `services.backtest.leaderboard.run_strategy_leaderboard(...)`

Important limitation:
- the active strategies that traded only realized `1` closed trade each in this cycle
- `mean_reversion_rsi` realized `0` closed trades
- this is enough for a conservative ranking pass, not enough for promotion claims

## Results

### `breakout_donchian`
- candidate: `breakout_default`
- rank: `2`
- leaderboard score: `0.524056`
- net return after costs: `+18.68%`
- max drawdown: `4.56%`
- closed trades: `1`
- expectancy: `1867.88`
- slippage sensitivity: `0.24%`
- represented regimes: `bear`, `bull`, `chop`, `low_vol`

Decision: `keep`

Reason:
- best active post-cost performer in the current cycle
- acceptable drawdown relative to the other active strategies
- still only one realized trade, so `keep` here means keep in the active research set, not promote to live

Next work:
- extend the evaluation window
- require multi-trade evidence before any sandbox promotion decision
- test false-breakout handling more explicitly in chop / low-vol conditions

### `ema_cross`
- candidate: `ema_cross_default`
- rank: `3`
- leaderboard score: `0.418391`
- net return after costs: `+15.44%`
- max drawdown: `6.25%`
- closed trades: `1`
- expectancy: `1544.26`
- slippage sensitivity: `0.23%`
- represented regimes: `bear`, `bull`, `chop`, `low_vol`

Decision: `improve`

Reason:
- still positive after costs, but weaker than breakout on both return and drawdown
- current result is too thin to justify stronger confidence
- existing hypothesis already identifies likely failure in chop / low-vol conditions, which matches where more discipline is needed

Next work:
- tighten chop and low-vol invalidation behavior
- rerun over a broader synthetic and paper dataset
- compare directly against breakout under the same multi-window test pack

### `mean_reversion_rsi`
- candidate: `mean_reversion_default`
- rank: `1`
- leaderboard score: `0.530000`
- net return after costs: `0.00%`
- max drawdown: `0.00%`
- closed trades: `0`
- expectancy: `0.00`
- slippage sensitivity: `0.00%`
- represented regimes: `bear`, `bull`, `chop`, `low_vol`

Decision: `freeze`

Reason:
- the current rank is not trustworthy as a "best strategy" result because it came from inactivity, not realized edge
- zero closed trades means there is no meaningful execution evidence in this cycle
- this should not remain the apparent leader without a stronger participation penalty in the ranking logic

Next work:
- add a no-trade / low-activity penalty to the decision layer or leaderboard presentation
- only reopen active iteration if a regime-targeted test shows real participation and positive expectancy

## Forced Decision Set

Keep:
- `breakout_donchian`

Improve:
- `ema_cross`

Freeze:
- `mean_reversion_rsi`

Retire:
- none in this cycle

## Operator Interpretation

What this does **not** mean:
- no strategy is proven profitable
- no strategy is approved for real-live promotion
- no claim is made about validated short support

What it **does** mean:
- `breakout_donchian` is the strongest active research candidate in the current synthetic cycle
- `ema_cross` stays viable but needs more work before it competes with breakout
- `mean_reversion_rsi` should not absorb more attention until it produces actual trading evidence

## Follow-up Gaps

The next improvement to the evaluation layer should be:
- penalize zero-trade candidates in the decision layer so inactivity does not outrank active positive performers
- persist decision records or leaderboard deltas if historical comparison is needed later

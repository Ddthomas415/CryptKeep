# EMA Cross Research Note (2026-03-26)

## Scope

Question:

- should `ema_cross_default` be changed from `12/26` to a shorter pair based on current repo evidence?

Compared:

- `ema_cross_default` = `ema_fast=12`, `ema_slow=26`
- candidate variant = `ema_fast=9`, `ema_slow=21`

## Live Read

Live/public scans were run against:

- `BTC/USD`
- `ETH/USD`
- `SOL/USD`
- timeframes: `1m`, `5m`, `15m`

Observed current-bar decisions:

- default `12/26` produced no `buy` candidates across the scanned matrix
- most rows were `hold / no_cross`
- one live `ETH/USD 1m` read reached a crossover state but still returned `hold / low_volatility_filter`

Shorter EMA pairs were then probed without changing repo presets:

- `9/21`
- `6/18`

Result:

- shorter pairs did not unlock meaningful `5m` or `15m` trigger activity
- occasional `1m` crossover states still mostly failed low-volatility confirmation

## Managed Paper Run

Managed paper run:

- strategy: `ema_cross`
- symbol: `ETH/USD`
- signal source: `public_ohlcv_1m`
- runtime: `900s`

Result:

- `enqueued_total: 0`
- `fills_delta: 0`
- `closed_trades_delta: 0`
- `net_realized_pnl_delta: 0.0`

This did not create new paper-history evidence.

## Deterministic Window Comparison

The repo's built-in synthetic evidence windows were used for a deterministic comparison.

Summary:

- `12/26`: average return `+10.92%`, `2` closed trades, max drawdown `6.25%`
- `9/21`: average return `+8.01%`, `1` closed trade, max drawdown `8.38%`

Window-level read:

- `12/26` ranked higher in:
  - `synthetic_default`
  - `trend_reversal`
  - `double_reversal`
- `9/21` only increased participation slightly in `breakout_pulse`, but still ranked lower overall
- both behaved poorly in `range_snapback`

## Decision

No EMA preset change is justified from current evidence.

Keep:

- `services/strategies/presets.py -> ema_cross_default`

Do not change:

- `ema_fast`
- `ema_slow`
- post-trigger filters

Reason:

- current live conditions do not differentiate the candidates in a way that supports promotion of a shorter pair
- deterministic synthetic windows favor the default `12/26` pair overall
- paper evidence remains too thin to justify a tracked preset change

## Follow-up

If EMA work resumes later, the next useful step should be one of:

- a new deterministic comparison on a materially different window set
- a regime-specific hypothesis update that explains why a shorter pair should outperform `12/26`

Not recommended now:

- more unchanged short live probes
- committing a shorter EMA preset without stronger evidence

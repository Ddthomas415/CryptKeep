# ES Daily Trend Backtest Baseline Audit (2026-06-05)

## Purpose

Determine whether `configs/strategies/es_daily_trend_v1.yaml` can safely
populate `promotion.paper.backtest_expectations` for:

- `win_rate`
- `avg_win`
- `avg_loss`

These fields drive the paper gate's manual-review comparison. Filling them from
weak or synthetic evidence would make the promotion gate look more objective
than it is.

## Current Gate State

- SHOWN: `scripts/check_promotion_gates.py --json` reports
  `manual_review_required=true`.
- SHOWN: the outstanding manual item is
  `win_rate_avg_win_loss_vs_backtest`.
- SHOWN: observed paper-history metrics are:
  - `closed_trades=7`
  - `fills=14`
  - `win_rate=0.2857142857142857`
  - `avg_win=37.32868831567376`
  - `avg_loss=-0.2625865534513479`
  - `net_realized_pnl=35.75316899496567`
  - `expectancy_per_closed_trade=5.107595570709381`

## Candidate Sources Checked

### `sample_data/ohlcv/BTC_USDT_1d.json`

- SHOWN: 230 rows.
- SHOWN: parity run with `sma_period=200`, `atr_period=20`,
  `warmup_bars=210`, `initial_cash=1000.0`, `fee_bps=10.0`, and
  `slippage_bps=5.0` produced:
  - `buy_count=1`
  - `sell_count=0`
  - `closed_trades=0`

Verdict: not usable. It does not produce closed trades, so it cannot provide
`win_rate`, `avg_win`, or `avg_loss`.

### `.cbp_state/data/snapshots/ohlcv_coinbase_BTC_USDT_1d.json`

- SHOWN: 300 rows.
- SHOWN: parity run with the same strategy settings produced:
  - `buy_count=0`
  - `sell_count=0`
  - `closed_trades=0`

Verdict: not usable. It is local runtime state rather than a committed baseline
artifact, and it does not produce closed trades.

### `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json`

- SHOWN: 220 rows.
- SHOWN: parity run with the same strategy settings produced:
  - `buy_count=1`
  - `sell_count=1`
  - `closed_trades=1`
  - `win_rate_pct=0.0`
  - `avg_loss=-59.967190658987526`

Verdict: not usable for profitability expectations. This fixture exists to
prove CI mechanics for a deterministic buy-to-sell round trip. It is synthetic
and engineered for an exit, so using it as a paper-promotion baseline would
misrepresent strategy expectancy.

## Decision

Do not populate `promotion.paper.backtest_expectations` yet.

The correct state remains:

- `source: null`
- `win_rate: null`
- `avg_win: null`
- `avg_loss: null`

This keeps `manual_review_required=true`, which is the correct gate behavior
until an accepted closed-trade historical baseline exists.

## Required Baseline Before Filling Config

An acceptable baseline should be:

- SHOWN: produced by `services/backtest/parity_engine.py` or a documented
  wrapper using the same strategy registry path.
- SHOWN: sourced from committed or otherwise reproducible public historical
  OHLCV data.
- SHOWN: long enough to produce multiple closed `sma_200_trend` trades without
  engineered synthetic exits.
- SHOWN: recorded with the command, data source, strategy config, fee/slippage
  assumptions, output scorecard, and reviewer acceptance.

Until then, the machine gate may clear the path-validation count, but the
operator must still perform the strategy-performance review manually.

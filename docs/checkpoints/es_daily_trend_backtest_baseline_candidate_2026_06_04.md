# ES Daily Trend Backtest Baseline Candidate (through 2026-06-04)

## Status

Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`

This is a candidate baseline report only. It has not been copied into
`configs/strategies/es_daily_trend_v1.yaml`.

## Command

```bash
./.venv/bin/python scripts/research/run_es_daily_trend_backtest_baseline.py \
  --venue coinbase \
  --symbol BTC/USDT \
  --data-symbol BTC/USD \
  --timeframe 1d \
  --since 2018-01-01 \
  --until 2026-06-04 \
  --page-limit 300 \
  --max-pages 20 \
  --min-closed-trades 3 \
  --output /private/tmp/es_daily_trend_v1_baseline_candidate_20260604.json
```

## Source

- SHOWN: `venue=coinbase`
- SHOWN: strategy/report symbol `BTC/USDT`
- SHOWN: fetched OHLCV data symbol `BTC/USD`
- SHOWN: timeframe `1d`
- SHOWN: first bar `2018-01-01T00:00:00Z`
- SHOWN: last bar `2026-06-04T00:00:00Z`
- SHOWN: rows `3077`

The `BTC/USDT` versus `BTC/USD` basis difference is visible and must be
accepted or rejected during independent review before this candidate can become
the config baseline.

## Candidate Result

- SHOWN: `baseline_ready=true`
- SHOWN: `blocking_reasons=[]`
- SHOWN: `buy_count=31`
- SHOWN: `sell_count=31`
- SHOWN: `closed_trades=31`
- SHOWN: `trade_count=62`

## Candidate Backtest Expectations

```yaml
source: public_ohlcv:coinbase:BTC/USDT:data=BTC/USD:1d:2018-01-01:2026-06-04
tolerance_pct: 25.0
win_rate: 0.22580645161290325
avg_win: 1881.5222600358036
avg_loss: -198.91552614027037
```

## Scorecard

- SHOWN: expectancy `270.86074815755273`
- SHOWN: net return after costs `839.6683192884136%`
- SHOWN: max drawdown `64.46532339450837%`
- SHOWN: profit factor `2.758846111674519`
- SHOWN: exposure fraction `0.515112122196945`
- SHOWN: total fees `361.80643051424846`

## Review Questions

- Is Coinbase `BTC/USD` acceptable as the historical data source for a strategy
  whose paper evidence symbol is `BTC/USDT`?
- Is the 2018-01-01 through 2026-06-04 window acceptable as the first paper-gate
  comparison baseline?
- Are `fee_bps=10.0` and `slippage_bps=5.0` the right assumptions for this
  baseline?

Only after those questions are accepted should the YAML snippet above be copied
into `configs/strategies/es_daily_trend_v1.yaml`.

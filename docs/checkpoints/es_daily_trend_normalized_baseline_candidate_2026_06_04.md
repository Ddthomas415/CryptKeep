# ES Daily Trend Normalized Baseline Candidate (through 2026-06-04)

## Status

Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`

This candidate replaces raw-dollar average win/loss values with net trade
return percentages. It has not been copied into
`configs/strategies/es_daily_trend_v1.yaml`.

## Reason For Replacement

The previous candidate reported raw dollar `avg_win` and `avg_loss`. Those
values depended on the backtest's all-in `$1,000` sizing and were not comparable
to the paper campaign's small fixed quantities.

The replacement uses:

- `win_rate`
- `avg_win_return_pct`
- `avg_loss_return_pct`

Each closed-trade return is net PnL after allocated entry and exit fees divided
by entry notional.

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
  --output /private/tmp/es_daily_trend_v1_normalized_baseline_candidate_20260604.json
```

## Result

- SHOWN: `baseline_ready=true`
- SHOWN: `rows=3077`
- SHOWN: `buy_count=31`
- SHOWN: `sell_count=31`
- SHOWN: `closed_trades=31`
- SHOWN: `blocking_reasons=[]`

## Config Candidate

```yaml
source: public_ohlcv:coinbase:BTC/USDT:data=BTC/USD:1d:2018-01-01:2026-06-04
tolerance_pct: 25.0
metric_basis: net_return_pct
win_rate: 0.22580645161290325
avg_win_return_pct: 78.71095396512578
avg_loss_return_pct: -4.0629558060999225
```

## Current Paper Comparison

As of the verification run:

- SHOWN: closed trades `7`
- SHOWN: fills `14`
- SHOWN: net win rate `0.14285714285714285`
- SHOWN: average winning trade return `93.63856474626441%`
- SHOWN: average losing trade return `-0.34741823139579114%`
- SHOWN: expectancy return per closed trade `13.079150765412809%`

These figures remain thin evidence and are not a profitability endorsement.

## Remaining Review Questions

- Is Coinbase `BTC/USD` acceptable as the historical data source for the
  `BTC/USDT` paper strategy?
- Is entry-notional net return percentage the accepted basis for the paper
  promotion comparison?
- Should the current `25%` relative tolerance remain unchanged for the
  normalized metrics?

Only after independent acceptance should the config candidate be copied into
the strategy YAML.

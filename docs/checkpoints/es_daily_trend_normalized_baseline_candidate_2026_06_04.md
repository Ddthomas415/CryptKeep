# ES Daily Trend Normalized Baseline Candidate (through 2026-06-04)

## Status

Acceptance state: `ACCEPTED`

This candidate replaces raw-dollar average win/loss values with net trade
return percentages. The accepted values were copied into
`configs/strategies/es_daily_trend_v1.yaml` in the subsequent governed
implementation stage.

Acceptance reference: independently reviewed and accepted by the operator on
2026-06-06 after commit `0e81e0aad`, including:

- Coinbase `BTC/USD` as the disclosed historical data basis for the
  `BTC/USDT` strategy comparison.
- `net_return_pct` as the sizing-independent comparison basis.
- the existing `25%` relative tolerance.

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

## Accepted Review Decisions

- Coinbase `BTC/USD` is accepted as the historical source with the basis
  difference retained in the source label.
- Entry-notional net return percentage is accepted as the comparison basis.
- The `25%` relative tolerance remains unchanged.

The next governed step is to independently review the populated config and its
resulting gate output.

## Populated Gate Result

After copying the accepted values into the strategy config:

- SHOWN: comparison status is `machine_blocking`.
- SHOWN: paper win rate `0.14285714285714285` is below the accepted range
  `0.16935483870967744` to `0.28225806451612906`.
- SHOWN: paper average winning return `93.63856474626441%` is within the
  accepted range `59.033215473844336%` to `98.38869245640723%`.
- SHOWN: paper average losing return `-0.34741823139579114%` is outside the
  accepted range `-5.078694757624903%` to `-3.047216854574942%`.

The smaller paper loss magnitude is financially favorable, but it also shows
that paper exits differ materially from the backtest's SMA-flat exits. The gate
correctly surfaces that drift instead of treating it as silent equivalence.

# Price-Action Multi-Market Research Checkpoint - 2026-08-27

## Scope

Read-only local price-action research across already archived OHLCV windows.
This checkpoint records generated artifact paths, hashes, and interpretation
only.

No campaigns, promotion gates, strategy configs, live/shadow execution, order
routing, ingestion policy, or host services were changed.

## Commands

```bash
./.venv/bin/python scripts/research/run_price_action_research_pipeline.py --venue coinbase --symbol BTC/USD --timeframe 1d --limit 500 --window-bars 120 --output-dir .cbp_state/data/research/price_action_pipeline/20260827T1232_coinbase_btcusd_1d
./.venv/bin/python scripts/research/run_price_action_research_pipeline.py --venue coinbase --symbol BTC/USDT --timeframe 5m --limit 500 --window-bars 120 --output-dir .cbp_state/data/research/price_action_pipeline/20260827T1232_coinbase_btcusdt_5m
./.venv/bin/python scripts/research/run_price_action_research_pipeline.py --venue okx --symbol BTC/USDT --timeframe 5m --limit 500 --window-bars 120 --output-dir .cbp_state/data/research/price_action_pipeline/20260827T1232_okx_btcusdt_5m
./.venv/bin/python scripts/research/run_price_action_research_pipeline.py --venue okx --symbol ETH/USDT --timeframe 5m --limit 500 --window-bars 120 --output-dir .cbp_state/data/research/price_action_pipeline/20260827T1232_okx_ethusdt_5m
```

## Artifact Summary

| Run | Summary SHA-256 | Dataset hash | Manual-review candidates |
|---|---:|---:|---:|
| Coinbase `BTC/USD` `1d` | `e765812a9b6e4877f0b582367e06ee2e4821f880bd55d348b6183419e913814f` | `5eb09843b00397c7028bc16543e14c56f21861edf2dded118b4990e5135e2ab0` | `18` |
| Coinbase `BTC/USDT` `5m` | `58f240b6177d20ab5a4e2754112a06e90c8c0e25c6d90f8aa95bc8eaf19fea70` | `6342fc7e8e1d4bc902e49c6b68332edb3e21992dd0200a1088d9641da1cb1362` | `13` |
| OKX `BTC/USDT` `5m` | `2bb1fdbab61f8faef92bf9c2973a5d9206fc04c2829a6c70636507937e5715ef` | `3fc7359657278334f7fe9465ea298e01d372e91c7476448067b3d0cde0f677aa` | `13` |
| OKX `ETH/USDT` `5m` | `7f32bf485813fd6f6fdc0288eed8835ba9ee3ae75cc73cb0660cdc3673d3ec0c` | `b367dcc802e14e2911314babddacf41ae3b246babec9be344e050deaa3ca7b02` | `15` |

All four runs returned `ok=true` and completed the accepted sequence:
`context_labels`, `forward_returns`, `window_stability`, and
`candidate_triage`.

## Repeated Manual-Review Labels

The following label/side pairs appeared as manual-review candidates across
multiple venue/symbol/timeframe runs:

- `acceptance_rejection:acceptance_above_opening_range` short appeared in all
  five checked runs including the earlier Coinbase `BTC/USDT` `1h` refresh.
- `opening_range_state:accepted_above` short appeared in all five checked runs
  including the earlier Coinbase `BTC/USDT` `1h` refresh.
- `acceptance_rejection:acceptance_below_opening_range` long appeared in four
  checked runs.
- `opening_range_state:accepted_below` long appeared in four checked runs.
- `fair_value_gap:bearish` long appeared in three checked runs.
- `fair_value_gap:bullish` long appeared in three checked runs.
- `swing_failure:bullish` long appeared in three checked runs.

## Interpretation

- The strongest repeated family in this local archive slice is opening-range
  acceptance/rejection, not a single candlestick pattern.
- The `5m` runs show much smaller average deltas than the `1d` run; any future
  review should compare these after choosing horizon and cost assumptions per
  timeframe.
- The output remains descriptive research only. It is not strategy
  configuration, campaign evidence, promotion evidence, profitability evidence,
  or execution input.
- Any label used as a confirmation filter still requires separate review with
  explicit sample-size, stability, false-positive, and integration criteria.

## Verification

- Archive inventory showed existing stored rows for Coinbase `BTC/USD` `1d`,
  Coinbase `BTC/USDT` `5m`, OKX `BTC/USDT` `5m`, and OKX `ETH/USDT` `5m`.
- Each pipeline run completed with `ok=true`.
- Candidate extraction verified status counts rather than treating every
  candidate-triage row as a manual-review candidate.

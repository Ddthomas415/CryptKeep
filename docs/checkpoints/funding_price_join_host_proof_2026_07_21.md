# Funding Context Price Join Host Proof - 2026-07-21

## Scope

Research-only host proof for the accepted `funding_extreme` context research path.
This proof does not start a campaign, does not create strategy evidence, does not
change promotion gates, and does not touch live execution, routing, or risk gates.

## Environment

- Host: Hetzner over Tailscale (`100.86.128.9`)
- App checkout: `/srv/cryptkeep/app`
- Runtime state: `/var/lib/cbp`
- Accepted commit: `5eb36cbb5`
- Remote branch: `master`

## Commands

Sync checkout, no service restart:

```bash
tailscale ssh root@100.86.128.9 "su -s /bin/bash cryptkeep -c 'cd /srv/cryptkeep/app && git fetch origin master && git merge --ff-only origin/master && git rev-parse --short HEAD'"
```

OHLCV archive backfill:

```bash
tailscale ssh root@100.86.128.9 "su -s /bin/bash cbp -c 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/research/run_ohlcv_archive_backfill.py --venue okx --symbol BTC/USDT --timeframe 5m --since 2026-07-18T00:00:00Z --archive-db /var/lib/cbp/data/market_raw.sqlite --page-limit 100 --max-pages 30 --max-bars 3000 --output /var/lib/cbp/data/ohlcv_archive_backfill/okx_btc_usdt_5m.latest.json --fail-if-not-ok'"
```

Funding context price join:

```bash
tailscale ssh root@100.86.128.9 "su -s /bin/bash cbp -c 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/research/run_funding_context_price_join.py --edge-db /var/lib/cbp/data/crypto_edge_research.sqlite --archive-db /var/lib/cbp/data/market_raw.sqlite --context-source live_public --context-venue okx --context-symbol BTC/USDT:USDT --price-venue okx --price-symbol BTC/USDT --timeframe 5m --funding-limit 500 --ohlcv-limit 1000 --horizon-bars 1 --min-joined-rows 1 --output /var/lib/cbp/data/funding_context_price_join/funding_context_price_join.latest.json --fail-if-not-ok'"
```

Supplemental full-store refresh, no service restart:

```bash
tailscale ssh root@100.86.128.9 "su -s /bin/bash cbp -c 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/research/run_ohlcv_archive_backfill.py --venue okx --symbol BTC/USDT --timeframe 5m --since 2026-07-18T00:00:00Z --archive-db /var/lib/cbp/data/market_raw.sqlite --page-limit 100 --max-pages 50 --max-bars 5000 --output /var/lib/cbp/data/ohlcv_archive_backfill/okx_btc_usdt_5m_refresh_20260721.json --fail-if-not-ok'"
```

Supplemental full-store funding context price join:

```bash
tailscale ssh root@100.86.128.9 "su -s /bin/bash cbp -c 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/research/run_funding_context_price_join.py --edge-db /var/lib/cbp/data/crypto_edge_research.sqlite --archive-db /var/lib/cbp/data/market_raw.sqlite --context-source live_public --context-venue okx --context-symbol BTC/USDT:USDT --price-venue okx --price-symbol BTC/USDT --timeframe 5m --funding-limit 1000 --ohlcv-limit 1096 --horizon-bars 1 --min-joined-rows 1 --output /var/lib/cbp/data/funding_context_price_join/funding_context_price_join_refresh_20260721.json --fail-if-not-ok'"
```

## Results

### OHLCV Archive Backfill

- Artifact: `/var/lib/cbp/data/ohlcv_archive_backfill/okx_btc_usdt_5m.latest.json`
- `artifact_type`: `ohlcv_archive_backfill_v1`
- `ok`: `true`
- `exchange`: `okx`
- `symbol`: `BTC/USDT`
- `timeframe`: `5m`
- `rows_written`: `1021`
- `archive_path`: `/var/lib/cbp/data/market_raw.sqlite`
- `dataset_hash`: `d2a661e606423760075844b4e1df88bd0dca3161d89292e1187f3e13207e243b`
- Limits: `page_limit=100`, `max_pages=30`, `max_bars=3000`
- Source: `public_exchange_ohlcv`

### Funding Context Price Join

- Artifact: `/var/lib/cbp/data/funding_context_price_join/funding_context_price_join.latest.json`
- `artifact_type`: `funding_context_price_join_v1`
- `ok`: `true`
- `reason`: `ok`
- `dataset_hash`: `f01778c070ab4feaf6aa7f5271e5fd2ed95544a774e6ae0fa9f972e83986b51b`
- `funding_dataset_hash`: `21fb23bdfb4c78c21472bc423e49c4d1ae5654e28d0effaf17144dfe0476cd9c`
- `price_dataset_hash`: `cfff5daa4df55d433a970228a1c36d0d307a7db4bfc375fee4eb38418c4d96a3`
- `funding_row_count`: `500`
- `price_row_count`: `1000`
- `joined_rows`: `498`
- `action_counts`: `{"hold": 498}`
- `reason_counts`: `{"funding_neutral": 498}`
- Summary: `actionable_rows=0`, `avg_net_forward_return_pct=null`,
  `positive_actionable_ratio=null`, `positive_actionable_rows=0`
- Cost assumptions: `fee_bps=10.0`, `slippage_bps=5.0`

### Supplemental Full-Store Refresh

Funding store query before refresh:

- Source/venue/symbol: `live_public` / `okx` / `BTC/USDT:USDT`
- Stored funding rows: `788`
- Capture range: `2026-07-18T20:25:49+00:00` to
  `2026-07-21T19:10:50+00:00`
- Funding-rate percent range: `min=-0.0044772316875499995`,
  `p50=0.00139570845653`, `p95=0.00778673794423`,
  `max=0.008465613466180001`
- Threshold crossings under active `funding_extreme` defaults:
  `count_ge_0.05=0`, `count_le_-0.01=0`

OHLCV archive refresh:

- Artifact:
  `/var/lib/cbp/data/ohlcv_archive_backfill/okx_btc_usdt_5m_refresh_20260721.json`
- `artifact_type`: `ohlcv_archive_backfill_v1`
- `ok`: `true`
- `exchange`: `okx`
- `symbol`: `BTC/USDT`
- `timeframe`: `5m`
- `rows_written`: `1096`
- `archive_path`: `/var/lib/cbp/data/market_raw.sqlite`
- `dataset_hash`: `2a6640a4fe35b939d87e3fffe57f88c5a280d825b1b4560d139268bbb63d1563`
- Limits: `page_limit=100`, `max_pages=50`, `max_bars=5000`
- Source: `public_exchange_ohlcv`

Full-store funding context price join:

- Artifact:
  `/var/lib/cbp/data/funding_context_price_join/funding_context_price_join_refresh_20260721.json`
- `artifact_type`: `funding_context_price_join_v1`
- `ok`: `true`
- `reason`: `ok`
- `dataset_hash`: `3f244fbe0af5a515b2aa7c1495e643578e6c36f04337f68af7a502641f6a4542`
- `funding_dataset_hash`: `005f84d306d3446071ef1122d6d27a8614cacd97ebb378c425c793d9663be76d`
- `price_dataset_hash`: `2a6640a4fe35b939d87e3fffe57f88c5a280d825b1b4560d139268bbb63d1563`
- `funding_row_count`: `788`
- `price_row_count`: `1096`
- `joined_rows`: `787`
- `action_counts`: `{"hold": 787}`
- `reason_counts`: `{"funding_neutral": 787}`
- Summary: `actionable_rows=0`, `avg_net_forward_return_pct=null`,
  `positive_actionable_ratio=null`, `positive_actionable_rows=0`
- Joined funding-rate percent range: `min=-0.00447723`, `p50=0.00139571`,
  `p95=0.00778674`, `max=0.00846561`
- Active threshold crossings: `count_ge_0.05=0`, `count_le_-0.01=0`

## Post-Run Runtime Checks

Crypto-edge runtime:

- `status=hetzner_crypto_edge_runtime_ready`
- `ok=True`
- `remote_head=5eb36cbb5dea80bf735779681f6d8260cbcddb46`
- `blocking_checks=0`

Paper campaign:

- Campaigns: `1/1 running`
- `ema_cross_default`: `idle`, `waiting_for_next_day`
- Fills: `9`
- Closed: `4`
- PnL: `-2.3157`
- Latest fill: `2026-07-21T00:05:06.659382+00:00`

Edge cadence:

- `ok=true`
- Fresh families: `funding`, `open_interest`, `basis`
- Latest capture timestamp: `2026-07-21T13:00:48+00:00`
- Missing: `[]`
- Stale: `[]`

## Interpretation

The archive blocker for the funding context price-join report is closed for the
bounded OKX `BTC/USDT` 5m host window backfilled here. The report joined stored
funding context to archived prices successfully.

The result is not a profitability signal: every joined funding context row
resolved to `hold/funding_neutral`, so there are zero actionable forward-return
rows. This means the current stored funding sample did not contain qualifying
`funding_extreme` entries under the active strategy thresholds.

The supplemental full-store refresh confirms this is a quiet funding sample, not
an artifact of the original `funding-limit=500` run. Across all stored OKX
`BTC/USDT:USDT` funding rows available at the time of the refresh, maximum
funding was `0.00846561%` versus the configured long-crowded trigger
`0.05%`, and minimum funding was `-0.00447723%` versus the configured
short-crowded trigger `-0.01%`.

## Acceptance State

`READY_FOR_INDEPENDENT_REVIEW`

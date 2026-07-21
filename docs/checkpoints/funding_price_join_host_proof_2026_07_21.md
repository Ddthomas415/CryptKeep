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

## Acceptance State

`READY_FOR_INDEPENDENT_REVIEW`

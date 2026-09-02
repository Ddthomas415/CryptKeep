# Hetzner Multi-Venue Paper Research Proposals

Date: 2026-08-25

Status: proposal only; not an active campaign manifest.

## Purpose

`configs/paper_evidence_campaigns.hetzner.multi_venue_proposed.json` records
disabled Gate.io and Binance paper/research candidate rows for Hetzner. The
file is an implementation artifact for the paper-universe widening backlog
scope; it does not start campaigns, widen the canonical paper gate, add
credentials, or change live routing.

## Candidate Rows

- `ema_cross_gateio_btcusdt_paper_candidate`
  - venue: `gateio`
  - symbol: `BTC/USDT`
  - signal source: `public_ohlcv_5m`
  - state directory: `.cbp_state_challengers/ema_cross_gateio_btcusdt_daily`
- `ema_cross_binance_btcusdt_paper_candidate`
  - venue: `binance`
  - symbol: `BTC/USDT`
  - signal source: `public_ohlcv_5m`
  - state directory: `.cbp_state_challengers/ema_cross_binance_btcusdt_daily`

Both rows are `enabled: false` by design. The runtime campaign loader rejects a
manifest with no enabled rows, so this file should not be passed directly to
`scripts/restore_paper_campaigns.py` until a reviewed follow-up deliberately
promotes one candidate row into an active manifest.

## Read-Only Status

Use this structure-only check before any activation discussion:

```bash
make status-hetzner-multi-venue-proposals-json
```

To include public-OHLCV reachability probes without enabling campaigns:

```bash
make status-hetzner-multi-venue-proposals-json HETZNER_MULTI_VENUE_PROPOSAL_ARGS=--preflight
```

The preflight mode remains read-only. Binance still requires the existing guard
environment (`CBP_VENUE=binance CBP_ALLOW_BINANCE=1`) before it is probed.

## Required Preflight Before Any Activation

Gate.io candidate:

```bash
./.venv/bin/python scripts/check_ohlcv_preflight.py --venue gateio --symbol BTC/USDT --signal-source public_ohlcv_5m --json
```

Binance candidate:

```bash
CBP_VENUE=binance CBP_ALLOW_BINANCE=1 ./.venv/bin/python scripts/check_ohlcv_preflight.py --venue binance --symbol BTC/USDT --signal-source public_ohlcv_5m --json
```

If preflight returns exit code `2`, treat the result as an OHLCV source
reachability problem, not as strategy evidence.

## Boundaries

- Evidence from these rows must remain isolated under `.cbp_state_challengers`.
- Evidence from these rows must not count toward the canonical
  `es_daily_trend_v1` promotion gate.
- Binance must stay behind the existing explicit guard:
  `CBP_VENUE=binance*` and `CBP_ALLOW_BINANCE=1`.
- No exchange credentials, live routing, order submission, host package install,
  service mutation, or canonical gate-threshold change is authorized by this
  proposal file.

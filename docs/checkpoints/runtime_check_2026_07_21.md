# Runtime Check - 2026-07-21

Status: read-only operator evidence refresh.

Commands run from `/Users/baitus/Downloads/crypto-bot-pro` on local master
`ae4ce1046`, with host checks over the accepted Tailscale SSH path.

## Paper Campaigns

Command:

```bash
make status-paper-all
```

Result:

- SHOWN: laptop paper campaigns are `2/2` running.
- SHOWN: `es_daily_trend_v1` is idle with
  `reason=waiting_for_next_day`, `fills=20`, `closed=10`, and
  `pnl=31.4369`.
- SHOWN: `breakout_default` is idle with `reason=waiting_for_next_day`,
  `fills=13`, `closed=6`, and `pnl=-4.1601`.
- SHOWN: Hetzner `ema_cross_default` is `1/1` running, idle with
  `reason=waiting_for_next_day`, `fills=9`, `closed=4`, `pnl=-2.3157`,
  and latest fill `2026-07-21T00:05:06.659382+00:00`.

## ES Paper Gate

Command:

```bash
make status-paper-gate-qualification-json
```

Result:

- SHOWN: `qualified_round_trips=3`.
- SHOWN: required `min_qualified_round_trips=10`, so `7` remain.
- SHOWN: `all_history_round_trips=10`, but legacy history remains
  diagnostic-only because `9` evidence fills lack or mismatch required
  public-OHLCV provenance.
- SHOWN: counted qualified fill window is
  `2026-05-26T00:00:09.788947+00:00` through
  `2026-07-09T00:04:00.377830+00:00`.
- SHOWN: policy is still `legacy_round_trip_v1` with
  `legacy_evidence_policy=diagnostic_only`.

Interpretation:

- The current bottleneck remains qualified ES round trips, not elapsed days.
- Legacy fills remain excluded; no provenance weakening is implied by this
  refresh.

## Hetzner Crypto-Edge Runtime

Command:

```bash
make status-hetzner-edge-runtime
```

Result:

- SHOWN: status is `hetzner_crypto_edge_runtime_ready`.
- SHOWN: `ok=True`, `blocking_checks=0`.
- SHOWN: remote checkout is `master` at
  `5eb36cbb5dea80bf735779681f6d8260cbcddb46`.

Host cadence command:

```bash
tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json'
```

Result:

- SHOWN: `ok=true`, `missing=[]`, `stale=[]`.
- SHOWN: OKX `funding`, `open_interest`, and `basis` snapshots all have
  `capture_ts=2026-07-21T21:10:42+00:00`.
- SHOWN: each enabled family reported `reason=fresh` with
  `age_sec=252.049493` and `max_age_sec=43200.0`.
- SHOWN: `quote` and `order_book` checks are disabled by policy in this
  cadence run.

Interpretation:

- The July 18 crypto-edge host proof remains current as of this refresh:
  the accepted read-only OKX collector is producing fresh funding,
  open-interest, and basis rows.
- This refresh does not authorize live routing, live trading, derivatives
  execution, or crypto-edge promotion.

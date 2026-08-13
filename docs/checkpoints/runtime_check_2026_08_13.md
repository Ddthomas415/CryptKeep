# Runtime Check - 2026-08-13

Status: read-only operator evidence refresh.

Commands were run from `/Users/baitus/Downloads/crypto-bot-pro` with Hetzner
checks over the accepted Tailscale SSH path.

## Hetzner Paper Campaign

Command:

```bash
make status-paper-hetzner
```

Result:

- SHOWN: campaigns are `1/1` running.
- SHOWN: `ema_cross_default` is idle with `reason=waiting_for_next_day`.
- SHOWN: `fills=11`, `closed=5`, and `pnl=-2.8010`.
- SHOWN: latest fill is `2026-08-13T00:16:11.041213+00:00`.
- SHOWN: recommendation is `continue_paper_observation`.

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
  `capture_ts=2026-08-13T23:35:51+00:00`.
- SHOWN: each enabled family reported `reason=fresh`.
- SHOWN: observed `age_sec=234.916103` against `max_age_sec=43200.0`.
- SHOWN: `quote` and `order_book` checks are disabled by policy in this
  cadence run.

## Boundary

This refresh records host-side read-only evidence only. It does not authorize
live routing, live trading, derivatives execution, crypto-edge paper
qualification, or shadow promotion.

# Hetzner Crypto-Edge Runtime Gap — 2026-07-18

Active role: AUDITOR

Objective: verify whether the Hetzner host is already accruing read-only
crypto-edge history and whether the accepted cost/cadence proof tooling can run
there.

## SHOWN

- `make status-paper-hetzner` succeeded after Tailscale SSH browser
  authentication.
- Hetzner `ema_cross_default` is running and healthy:
  - `status=idle`
  - `reason=waiting_for_next_day`
  - `fills=8`
  - `closed=4`
  - `pnl=-2.2667`
  - `latest_fill=2026-07-14T00:05:03.287310+00:00`
  - session evidence already recorded for `2026-07-18`
- Remote app boundary is stale relative to local master:
  - remote `HEAD=b86105b`
  - remote branch: `review-stabilized...origin/review-stabilized`
  - local master at the time of this checkpoint: `65d3ce125`
- Remote app does not contain the accepted cost-assumption checker:
  - `./.venv/bin/python scripts/check_cost_assumptions.py --json`
  - result: `can't open file '/srv/cryptkeep/app/scripts/check_cost_assumptions.py'`
- Remote crypto-edge collector loop status:
  - `status=not_started`
  - `reason=status_missing`
  - `pid_alive=false`
  - `has_pid_file=false`
  - `summary_text=Collector loop has not written runtime status yet.`
- Remote scheduler scan found no matching user systemd timers or crontab entries
  for `edge`, `crypto`, `collector`, or `cbp`.
- Remote `sample_data/crypto_edges/live_collector_plan.json` is still
  Binance-based for funding, open interest, and basis.

## UNVERIFIED

- Whether the host has root/systemd authority to install the accepted
  `cbp-edge-cadence` units.
- Whether the current remote host should be fast-forwarded to master while
  `ema_cross_default` is running.
- Whether a separate process outside this repo is collecting crypto-edge rows.
  The repo-local loop/status/store files inspected here did not show it.

## Finding

The Hetzner paper campaign is healthy, but the crypto-edge research substrate is
not yet operating there. The host is also running stale code and a stale
Binance-oriented collection plan, so starting the repo-local collector as-is
would not follow the accepted OKX source decision.

## Recommended Next Action

Do not start the remote crypto-edge collector from the current remote checkout.
First perform a reviewed host sync or deploy step that brings the host to the
accepted master boundary and OKX collection plan. Then run:

```bash
./.venv/bin/python scripts/check_edge_cadence.py --json
```

and enable the accepted read-only cadence timer only after the plan and checker
are present on the host.

## Acceptance State

READY_FOR_INDEPENDENT_REVIEW

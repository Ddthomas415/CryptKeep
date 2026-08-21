# Host Runtime Check-In - 2026-08-21

Date: 2026-08-21

Scope: read-only runtime and evidence check-in. No service restart, deploy,
state migration, restore, live enablement, or campaign config change was
performed.

## Local Laptop Paper Campaigns

Command:

```bash
make status-paper-campaigns
```

Result:

- SHOWN: `ok=true`.
- SHOWN: `running_count=2`.
- SHOWN: `es_daily_trend_v1` is running and idle with
  `reason=waiting_for_next_day`.
- SHOWN: `es_daily_trend_v1` last completed day is `2026-08-21`.
- SHOWN: `breakout_default` is running and idle with
  `reason=waiting_for_next_day`.
- SHOWN: `breakout_default` last completed day is `2026-08-21`.

## Local ES Paper Gate Velocity

Command:

```bash
make status-paper-gate-velocity-json
```

Result:

- SHOWN: `ok=true`.
- SHOWN: policy id is `slow_daily_single_symbol_v1`.
- SHOWN: qualified bars are complete: `60/60`.
- SHOWN: qualified round trips are `3/5`, with `2` remaining.
- SHOWN: projected completion is `2026-09-11T04:19:18.304911+00:00` under
  observed qualified-close cadence.
- SHOWN: `7` all-history round trips remain diagnostic only because they do not
  satisfy the current provenance contract.

## Local Cost Assumption Check

Command:

```bash
make check-cost-assumptions-json
```

Result:

- SHOWN: exit code `2`.
- SHOWN: overall status is `warning`, not a hard failure.
- SHOWN: paper engine costs are configured:
  `paper_trading.fee_bps=7.5`, `paper_trading.slippage_bps=5.0`.
- SHOWN: modeled round trip is `25.0` bps against policy floor `5.0` bps.
- SHOWN: warnings remain for independently sourced evidence-scoring and
  backtest/walk-forward cost surfaces.

## Hetzner Paper Campaign

Command:

```bash
make status-paper-hetzner
```

Result:

- SHOWN: `Campaigns: 1/1 running`.
- SHOWN: `ema_cross_default` is idle with `reason=waiting_for_next_day`.
- SHOWN: `ema_cross_default` has `fills=12`, `closed=6`, and `pnl=-1.9833`.
- SHOWN: latest fill is `2026-08-19T00:15:15.161016+00:00`.
- SHOWN: recommendation is `continue_paper_observation`.

## Hetzner Crypto-Edge Runtime

Command:

```bash
make status-hetzner-edge-runtime
```

Result:

- SHOWN: `status=hetzner_crypto_edge_runtime_ready`.
- SHOWN: `ok=True`.
- SHOWN: `read_only=True`.
- SHOWN: remote branch is `master`.
- SHOWN: remote head is `a10aca01fc37de181cc32d17a30e5d677050f901`.
- SHOWN: `blocking_checks=0`.

## Hetzner Edge Cadence

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json'
```

Result:

- SHOWN: `ok=true`.
- SHOWN: `funding`, `open_interest`, and `basis` are fresh.
- SHOWN: all three fresh families have capture timestamp
  `2026-08-21T03:08:42+00:00`.
- SHOWN: all three fresh families reported `age_sec=4275.549833`, below
  `max_age_sec=43200.0`.
- SHOWN: `quote` and `order_book` checks are disabled by policy in this command.

## Remaining Risk

- This checkpoint does not install or restart systemd units.
- This checkpoint does not complete the backup/restore drill.
- This checkpoint does not close launch-packet host proofs requiring real
  action events, restoration, or secrets-rotation evidence.
- This checkpoint does not change promotion gates, campaigns, execution, or
  risk policy.

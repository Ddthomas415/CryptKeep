# Host Status Ready Check-In - 2026-08-20

## Scope

Read-only checkpoint replacing the stale host-proof blocker observation from
the same day. This records that Tailscale SSH worked on the fresh attempt and
the core Hetzner status wrappers completed successfully.

## Commands Run

```bash
make status-hetzner-edge-runtime
make status-paper-hetzner
tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json'
```

## Findings

- `make status-hetzner-edge-runtime` reported
  `status=hetzner_crypto_edge_runtime_ready`, `ok=True`.
- Remote checkout was on `master` at
  `a10aca01fc37de181cc32d17a30e5d677050f901`.
- `make status-paper-hetzner` reported `Campaigns: 1/1 running`.
- Remote paper campaign `ema_cross_default` was idle with
  `reason=waiting_for_next_day`, `fills=12`, `closed=6`, and
  `pnl=-1.9833`.
- Direct host edge cadence check under `CBP_STATE_DIR=/var/lib/cbp` reported
  `ok=true`.
- Funding, open-interest, and basis captures were fresh with
  `capture_ts=2026-08-20T23:03:17+00:00` and `age_sec` about `285` seconds at
  check time.

## Operational Boundary

No services were started, stopped, installed, restarted, migrated, restored, or
modified by this checkpoint.

## Follow-Up

The earlier `host_proof_blocker_checkin_2026_08_20` PR was closed as stale
because the fresh Tailscale SSH run succeeded. Remaining host-side proof work
still depends on the specific proof artifacts named in `REMAINING_TASKS.md`;
this checkpoint only proves current remote status and edge cadence.

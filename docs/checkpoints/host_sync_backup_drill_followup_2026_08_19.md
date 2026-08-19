# Host Sync and Backup Drill Follow-up - 2026-08-19

## Scope

Sync `/srv/cryptkeep/app` on Hetzner to current master without restarting
services, then rerun read-only proof checks for edge cadence, paper campaign
status, and backup drill readiness.

## Commands Run

```bash
tailscale ssh cryptkeep@100.86.128.9 'set -eu
cd /srv/cryptkeep/app
git fetch origin master
git merge --ff-only origin/master
printf "HEAD=" && git rev-parse --short=9 HEAD
git status --short --branch
systemctl is-active cbp-crypto-edge-collector.service cbp-edge-cadence.timer'
```

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json'
```

```bash
make status-hetzner-edge-runtime status-paper-hetzner
```

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && ls scripts/check_backup_artifact_secrets.py scripts/backup_state.py && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/backup_state.py --help'
```

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && STAMP=$(date -u +%Y%m%dT%H%M%SZ) && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/backup_state.py backup --dest /tmp/cbp-state-backups-$STAMP'
```

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_event_secrets.py --json'
```

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/report_platform_event_journal.py'
```

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_platform_event_secrets.py --json'
```

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_live_intent_history_schema.py --json'
```

## Findings

SHOWN:

- Host checkout fast-forwarded from `5eb36cbb5` to `a10aca01f`.
- `cbp-crypto-edge-collector.service` stayed active.
- `cbp-edge-cadence.timer` stayed active.
- No service restart was performed.
- `scripts/backup_state.py` is present.
- `scripts/check_backup_artifact_secrets.py` is now present.
- Host edge cadence against `/var/lib/cbp` is fresh:
  - funding/open_interest/basis capture timestamp: `2026-08-19T09:54:38+00:00`
  - age at check: about 170 seconds
  - `ok=true`
- Hetzner edge runtime wrapper reports:
  - `status=hetzner_crypto_edge_runtime_ready`
  - `ok=True`
  - `remote_head=a10aca01fc37de181cc32d17a30e5d677050f901`
- Hetzner paper campaign wrapper reports:
  - `Campaigns: 1/1 running`
  - `ema_cross_default` idle waiting for next UTC day
  - fills=12, closed=6, pnl=-1.9833
  - latest fill `2026-08-19T00:15:15.161016+00:00`
- Host operator-event secret scan reports `ok=true`, `finding_count=0`, and
  `event_count=0` for `/var/lib/cbp/data/operator_events/operator_events.jsonl`.
- Host platform-event secret scan reports `ok=true`, `finding_count=0`, and
  `event_count=0` for `/var/lib/cbp/data/platform_events/platform_events.jsonl`.
- Host platform-event journal report works and reports `ok=true`,
  `event_count=0`, and no latest event.
- Host live-intent history schema remains uninitialized:
  `db_exists=false`, `reason=live_intent_queue_db_missing`,
  `event_history_table_exists=false`.

SHOWN remaining blocker:

```json
{
  "ok": false,
  "reason": "snapshot_failed:market_raw.sqlite:OperationalError",
  "error": "attempt to write a readonly database",
  "backup_dir": "/tmp/cbp-state-backups-20260819T095731Z/cbp-state-backup-20260819T095731Z",
  "operator_event": {
    "ok": false,
    "reason": "operator_event_write_failed:OperatorEventJournalError"
  }
}
```

## Result

Status: `PARTIAL`.

The host checkout/tooling drift is resolved. The full-state backup/restore
drill remains blocked because the current `cryptkeep` execution context cannot
snapshot `cbp`-owned SQLite state or write the operator event journal under
`CBP_STATE_DIR=/var/lib/cbp`.

The host no-secret scans are clean for currently absent operator/platform event
journals. They do not close event-family proofs that require real event records.

## Next Operator Action

Run the backup/verify/scratch-restore/secret-scan sequence with effective access
to the `cbp` state data and operator-event journal. Do not restore over live
state; use a scratch `CBP_STATE_DIR` for restore proof.

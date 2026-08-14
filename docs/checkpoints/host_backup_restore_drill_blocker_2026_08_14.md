# Host Backup/Restore Drill Blocker - 2026-08-14

## Scope

Read-only/scratch attempt to advance the full-state backup/restore drill proof
on Hetzner without restarting services or restoring over `/var/lib/cbp`.

## Commands Run

```bash
tailscale ssh cryptkeep@100.86.128.9 'set -eu
cd /srv/cryptkeep/app
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_ROOT=/tmp/cbp-state-backups-$STAMP
RESTORE_ROOT=/tmp/cbp-restore-scratch-$STAMP
CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/backup_state.py backup --dest "$BACKUP_ROOT" | tee /tmp/cbp-backup-$STAMP.json
BACKUP_DIR=$(find "$BACKUP_ROOT" -maxdepth 1 -type d -name "cbp-state-backup-*" | head -n 1)
CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/backup_state.py verify "$BACKUP_DIR" | tee /tmp/cbp-backup-verify-$STAMP.json
CBP_STATE_DIR="$RESTORE_ROOT" ./.venv/bin/python scripts/backup_state.py restore "$BACKUP_DIR" --force | tee /tmp/cbp-restore-scratch-$STAMP.json
CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_backup_artifact_secrets.py "$BACKUP_DIR" --json --evidence-dest /var/lib/cbp/data/backup_artifact_secret_scan | tee /tmp/cbp-backup-secret-scan-$STAMP.json
echo BACKUP_DIR=$BACKUP_DIR
echo RESTORE_ROOT=$RESTORE_ROOT
echo STAMP=$STAMP'
```

```bash
tailscale ssh cryptkeep@100.86.128.9 'set -eu
cd /srv/cryptkeep/app
printf "HEAD="; git rev-parse --short=9 HEAD
printf "STATUS="; git status --short --branch
printf "MISSING_SCRIPTS="; ls scripts/check_backup_artifact_secrets.py scripts/backup_state.py 2>&1 || true
find /tmp/cbp-state-backups-20260814T052854Z -maxdepth 4 -type f -ls 2>/dev/null | head -50
find /var/lib/cbp/data -maxdepth 2 -type f \( -name "*.sqlite" -o -name "*.db" -o -name "*.sqlite3" \) -ls 2>/dev/null | head -50'
```

```bash
tailscale ssh cryptkeep@100.86.128.9 'set -eu
id
getent passwd cbp || true
ls -ld /var/lib/cbp /var/lib/cbp/data
sudo -n -u cbp sh -lc "cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/backup_state.py --help"'
```

## Findings

SHOWN:

- Hetzner checkout remains at `5eb36cbb5`.
- `scripts/backup_state.py` is present on that checkout.
- `scripts/check_backup_artifact_secrets.py` is absent on that checkout.
- `/var/lib/cbp` and `/var/lib/cbp/data` are owned by `cbp:cbp`.
- Current Tailscale login is `cryptkeep`.
- `sudo -n -u cbp ...` fails with `sudo: a password is required`.
- `CBP_STATE_DIR=/var/lib/cbp ... scripts/backup_state.py backup --dest ...`
  fails during SQLite snapshot with:

```text
sqlite3.OperationalError: attempt to write a readonly database
```

SHOWN partial artifact:

- The failed backup attempt created a partial directory under
  `/tmp/cbp-state-backups-20260814T052854Z/cbp-state-backup-20260814T052854Z`.
- The partial artifact is not a valid backup proof because the backup command
  raised before writing a complete manifest.

## Result

Status: `BLOCKED`.

This does not close the backup/restore drill. The blocker is host execution
authority and deployed-tooling drift, not missing local repo code.

## Next Operator Action

Run the drill from an account that can read and snapshot the `cbp`-owned state
without readonly SQLite failures, and sync the host checkout to a commit that
contains the backup-artifact secret scanner before attempting the full proof.

Minimum next proof sequence:

1. Sync `/srv/cryptkeep/app` to the approved current master without service
   restart.
2. Run `backup_state.py backup` with effective access to the `cbp` state data.
3. Verify the backup manifest.
4. Restore into a scratch `CBP_STATE_DIR`, not over live state.
5. Run the backup-artifact secret scan.
6. Record the drill checkpoint only after all prior steps pass.

# CryptKeep Full-State Backup and Restore Drill

Status: `POLICY_DOCUMENTED` · Tooling: `scripts/backup_state.py` (proof-ready)

## Purpose

Define the full-state backup/restore rehearsal required before capped-live
operation. This document does not execute a backup or restore.

## Current Boundary

SHOWN:

- Hetzner paper-host storage preflight checks backup directory presence, disk
  space, and inode availability.
- Isolated challenger restore proof exists for the Hetzner EMA campaign.
- Canonical `.cbp_state` migration remains separately blocked behind a
  stop-copy-verify-start packet.

SHOWN (2026-07-10): durable data-state backup/verify/restore tooling with
consistency-under-writer and guard proofs exists (`scripts/backup_state.py`,
`tests/test_state_backup_restore.py`).

UNVERIFIED:

- No full canonical state backup/restore rehearsal has been executed for the
  future capped-live state bundle.
- No launch packet currently proves restore-and-resume for all live-relevant
  state stores.

## State Families To Include

The drill packet must name every state family included or explicitly excluded:

- paper/live trading SQLite stores;
- trade journal and strategy evidence artifacts;
- live intent queue and reconciliation state;
- risk/accounting state;
- market-data archives and dataset manifests;
- campaign manifests and runtime status snapshots;
- alert/watchdog state required for unattended operation;
- deployment records and work-log evidence.

Secrets are not part of state backup. Restore secret access through the approved
server secrets model, not by copying secret-bearing files.

## Tooling

`scripts/backup_state.py` implements the durable `data_dir()` portion of
procedure steps 3-5 with drill-grade guarantees (proven by
`tests/test_state_backup_restore.py`):

- `backup --dest <dir>`: sqlite-backup-API snapshots (transactionally
  consistent even under active writers — plain file copies tear under
  WAL), checksummed manifest (`backup_manifest.json`: per-file sha256,
  sizes, counts). SQLite sidecars (`-wal`, `-shm`, `-journal`) are
  excluded because the backup API folds committed database content into
  the snapshot. Safe while services run.
- `verify <backup>`: read-only; every checksum plus `PRAGMA
  integrity_check` on every database; rejects invalid relative paths
  before restore can touch the target.
- `restore <backup> [--force]`: fail-closed guards in order — the backup
  must verify completely before anything is touched; any `*.lock` under
  the state dir blocks restore (stop writers first, per step 2); a
  non-empty data dir requires `--force` and is then moved aside to
  `data.pre-restore-<stamp>`, never deleted; only manifest-listed files
  are restored; post-restore, every file is re-checksummed. Exit codes:
  0 ok, 1 failure, 2 guard-blocked.
- Scratch-directory restore (step 4) = run restore with `CBP_STATE_DIR`
  pointed at the scratch root.

Deliberately NOT tool scope (drill-time steps): the secrets scan of the
backup artifact (run gitleaks over the backup directory, per the pass
criteria), runtime/config/snapshot families outside `data_dir()` that the
drill packet must explicitly include or exclude, and the resume/idempotence
proofs (steps 6-8), which are operator observations on the restored system.

## Drill Procedure

1. Record source host, Git SHA, state root, and running campaign status.
2. Stop or isolate writers according to the migration/runbook being tested.
3. Produce a backup manifest with file list, sizes, and hashes.
4. Restore to a scratch directory or isolated host.
5. Run integrity checks over restored SQLite stores and manifest hashes.
6. Run read-only status commands from restored state.
7. Resume only a paper/sandbox-safe component from restored state.
8. Prove no duplicate campaigns, intents, fills, or evidence windows were
   created by the restore.
9. Record rollback path and cleanup.

## Pass Criteria

The drill passes only if:

- backup manifest and restored manifest match;
- restored status commands can read all expected state;
- resume is idempotent and does not duplicate running processes;
- restored evidence counts match source counts unless an accepted delta is
  documented;
- no secrets are present in the backup artifact;
- cleanup leaves the source campaign untouched.

## Capped-Live Gate

Before capped live, the launch packet must include one successful full-state
restore drill or an explicit accepted exception with expiry.

## Executable Guard

`tests/test_full_state_restore_drill_contract.py` pins the drill boundary,
state-family coverage, tooling guarantees, deliberately excluded drill-time
steps, pass criteria, capped-live gate, and `docs/LAUNCH_CHECKLIST.md` link.
The guard does not prove a host drill ran; it prevents the required proof
contract from silently shrinking.

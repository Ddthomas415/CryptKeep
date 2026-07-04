# CryptKeep Full-State Backup and Restore Drill

Status: `POLICY_DOCUMENTED`

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


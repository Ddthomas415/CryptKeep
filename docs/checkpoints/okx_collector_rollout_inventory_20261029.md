# Collector Rollout Inventory

2026-10-29 America/New_York. AUDITOR findings; DIRECTOR proposal follows.
Operational rollout INCOMPLETE. No startup/DB-write authorization inferred.

SHOWN: saved local health file names PID2741, original sample plan,300s poll,
live_public source and last status10:34:05EDT/14:34:05UTC October29. PID file
records October12 startup. Historical work log corroborates that old restart;
it is not current liveness proof. Saved status saying running is stale evidence.

Sandbox ps was denied. The same targeted read outside sandbox returned no
PID2741; outside-sandbox pgrep found no recorded script match. lsof on the exact
SQLite/WAL/SHM paths reported no handles. These are scoped observations, not
proof about every launch mechanism/host or permanent database exclusivity.

Local default archive exists under .cbp_state/data with UID501/GID20, about
31.9MB plus existing WAL/SHM files. Metadata only; no SQLite connection, schema
inspection, recovery, backup, checkpoint or deletion. A WAL file's presence
does not establish corruption or an active writer. The alternate macOS app
state location lacked matching collector files. This inspection process had
no CBP_STATE_DIR override; another process could use one.

Only matching LaunchAgent filename was the separate ED-002 public-input job;
it was not inspected/changed. Packaging systemd unit and October8 Hetzner
checkpoint are references, not current remote operational evidence. No remote
connection or environment/credential file access occurred.

Sanitized observations: docs/review_artifacts/okx_collector_rollout_inventory_20261029/INVENTORY.json.

## Proposed Next Operation, Not Executed

DIRECTOR scope: one foreground service cycle to verify paired live capture plus
journal write/read in a NEW isolated research database, not the existing archive.
Use a separate funding-only diagnostic plan with explicit BTC-USDT-SWAP,2GET
budget,30s funding capture checks,10s per process,1MiB per body, one raw row and
4MiB journal budget. No other families requested for this diagnostic. This is
not a replacement/narrowing of the existing full-family collector or project.

Call the reviewed collect_once API once, not run_forever: no global collector
PID/status/stop-file lifecycle, background job or automatic retry. New append-
only diagnostic plan/DB/receipts would be confined to a fresh review-artifact
directory. Existing archive, WAL/SHM, plans, schedules and trading untouched.
Capture budget is not a hard deadline on local processing/SQLite persistence.
Preserve failure evidence; do not infer an exception means definitely unwritten.

Proof required: actual service outcome, raw row/content identity, reopen/read
forecast labels and unchanged authority gates; source/config/result hashes.
Record original archive metadata before/after without opening it. Binary trust
and actual payments/freshness remain unverified; no profitability claim.

Human authorization is required for these new public requests and isolated DB
writes. Prior two-GET permission was consumed. No diagnostic operation ran in
this inventory. The full multi-family collector has NOT been restored; that
needs a subsequent explicit operational decision rather than an inferred one.

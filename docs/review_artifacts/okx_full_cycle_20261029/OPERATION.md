# Single Full-Family Validation Cycle

ENGINEER operation preparation,2026-10-29. HIGH risk (original evidence writes
and process lifecycle). User continued after the stated next single validation
cycle. This covers no recurring collector, schedule, account or trading change.

The existing reviewed CLI is invoked once with the copied full-family plan,
source live_public, original local research archive, max-loops1 and paired raw
funding options. All five families retained. Funding has2GET/30s capture checks,
10s per transport,1MiB bodies; additional public SDK traffic for OI/basis/quotes/
orderbook is outside those funding limits. No private credentials are supplied;
existing collector constructs public clients with apiKey/secret None.

The artifact-local bounded_cycle.py is standard foreground invocation plumbing,
not a new service/launcher framework. It uses one exclusive attempt marker,
one new-session child and a180s wait, then at most two5s cleanup waits with
TERM/KILL restricted to that owned process group. Preflight, process creation
and final receipt writes are not hard-interruptible by the wait timeout.
Cleanup can fail and partial persistence can survive. It never restores an old
DB over new writes, removes evidence, resets the marker or retries.

The wrapper's process exit is not collection acceptance: inspect RUN_RECEIPT,
the CLI's paired_run_succeeded/last_result, all configured row counts and check
results. On normal completion it may have written the raw table/index, research
rows, global status and PID state; existing loop removes its PID file at
max-loops and leaves stopped status. On timeout those control files may remain
stale. Do not repair them automatically or infer an exception means no writes.

Fresh backup: NEXT_OPERATION points to the new UUID folder. PREPARATION records
original file hashes, baseline row fingerprints/maxIDs and control metadata.
backup_raw contains unopened exact copies of original SQLite/WAL/SHM; a separate
backup_verify copy passed quick_check and baseline reads. Originals were byte/
metadata unchanged across preparation. No observed handles is a scoped
observation, not global or permanent exclusivity. Recheck ownership and original
hashes immediately before launch; stop if another writer or stop flag appears.
The first lsof invocation had a field-flag typo; the corrected check returned
exit1/no handles. The failed invocation is not treated as proof of absence.

Four mocked subprocess tests passed0.08s. They cover one launch, exclusive
no-repeat marker, timeout owned cleanup, TERM/KILL escalation and launch failure.
They do not prove actual process-group cancellation, current network success or
archive compatibility by themselves. The prior accepted rehearsal and source
tests remain separate. Runtime state/binary authenticity remain UNVERIFIED.

Independent review of wrapper/tests and bound inputs precedes the operation.
After operation, read original archive through mode=ro, compare every existing
row prefix against baseline, validate new raw pair/forecast and verify appended
IDs/counts for each configured family. Use explicit paired-cadence source/native
ID and enable quote/orderbook thresholds only in that one check call, not in
global configuration. No report may substitute old rows for new-cycle success.

On failure preserve outputs, receipts and any partial writes; no automatic retry,
recurring launch, service change or rollback. On success report one-shot proof,
not ongoing collection, trading readiness or profitability. Recurring restoration
still needs separate authorization.

# Paper Recovery Failure Isolation - V2

Active role: ENGINEER. HIGH risk. Isolated candidate:
/private/tmp/cryptkeep-paper-correction-20261004.

The recovery sweep isolates errors per row and reports failed order IDs rather
than aborting the whole page. It advances past failures without marking their
evidence repaired. The unchanged ledger row and missing evidence remain the
retry obligation. A persisted cycle ceiling bounds each scan, so new fills
cannot continually postpone returning to the failed rows. Restart retains both
the cursor and cycle boundary. The original timestamp cutoff is unchanged.

SHOWN: new tests exercise persistent row failure in the same and a different
strategy, new fills during the scan, retry after engine restart, and cursor-write
failure without duplicate evidence. Original exact-quote and paging probes pass.
The existing 505-row traversal proof remains intact.

VERIFIED_ENV: local venv Python 3.12.10, isolated candidate, temporary accounts.
Targeted eleven-file slice (same command as the previous correction handoff):
153 passed in 6.52s. Narrow recovery/probe slice: 13 passed in 1.97s.
Bytecode and pytest cache writes disabled. Generated correction.patch passes
git apply --check against the prior isolated assembled candidate.

Frozen artifacts: docs/review_artifacts/paper_quote_recovery_correction_v2_20261004/.
Earlier checkpoint artifacts are retained unchanged. This delta does not include
the candidate's unrelated live-order edits. No main runtime source, configuration,
account, collector, merge or deployment change.

Limits: engine recreation is not a process-kill test; concurrent sweeps, external
logger durability, database replacement, full suite, CI and host operation are
unverified. Retries occur on later complete scans, not immediately; large ledgers
require multiple bounded cycles. Backfilled PnL remains unknown.

Independent reviewer Carson: failed-row isolation is SHOWN correct under
repeated serialized calls; operational recovery remains INCOMPLETE. Reviewer
ran quote/recovery/probe slice independently: 18 passed in 2.28s.

P2 blocker: paper_runner.py:253 calls recovery once before its loop. Production
does not yet drive subsequent pages or retries; tests manually call the sweep.
Required next correction: wire bounded repeated sweeps in the supported runner,
with explicit serialization against other sweeps/evidence writers and tests.
Logger append failures are swallowed, so ok/backfilled are attempted-write
results, not persistence proof; this must remain visible in reporting. Concurrent
writers can duplicate or overwrite evidence and are outside current proof.

Acceptance state: INCOMPLETE after separate review. No deployment authorized.

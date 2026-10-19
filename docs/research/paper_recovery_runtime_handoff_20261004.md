# Paper Recovery Runtime Handoff

Active role: ENGINEER, then independent AUDITOR Mill. Isolated candidate:
/private/tmp/cryptkeep-paper-correction-20261004. No campaign restart.

## Changes and Proof

The managed paper runner executes a bounded recovery page after fill evaluation
on every loop and reports recovery status. Fixed scan ceilings, cursor persistence
and per-row isolation retain retries and allow later fills to progress.

Cooperating evidence writers and recovery share a reentrant SQLite lock, with
0.1-second acquisition timeouts. Recovery catches contention without stopping
the loop. Artifact presence is checked before reporting a recovered record.
Generic logging still supports multiple fills for an order; only the paper
engine's single-fill-per-order paths use the shared identity check.

Initial independent review REJECTED a duplicate window: ledger commit, recovery
append, then normal append produced two evidence records. Both paper paths now
call _log_paper_fill_once, checking order identity and writing under one lock.
Reviewer Mill re-ran the deterministic real-ledger interleaving and confirmed
one ledger fill produces one evidence record. Independent re-review ACCEPTED
this bounded duplicate correction, not whole-system readiness.

SHOWN / VERIFIED_ENV: Python 3.12.10 in the isolated candidate. Expanded fifteen-
file slice: 191 passed in 7.98s, bytecode/cache disabled. Independent reviewer
ran runtime/backfill slice: 11 passed. Tests exercise recurring runner recovery,
transient failure, cross-strategy progress, restart, paging beyond 500 rows,
cursor-write failure, lock contention, silent logger failure, concurrent thread
appends and recovery between ledger commit and normal logging.

Artifact: docs/review_artifacts/paper_quote_recovery_correction_v4_20261004/correction.patch.
Generated against the previous assembled candidate. Applicability check passed
excluding test_codex_0040_0044_probe.py, already present there as a review overlay;
the patch includes that probe as a complete new file for clean series candidates.
Earlier checkpoint artifacts remain unchanged. No unrelated live-order delta.

## Limits and Next Step

No full suite, CI, multiprocess stress, sustained-contention exit test, actual
host scheduling or deployment proof. A page bounds row count, not elapsed time;
historical file scans may delay cycles. Locks protect cooperating writers only,
not external direct file edits. Readable artifact presence is not fsync proof.
Recovery may preserve a backfilled record with unknown PnL even when the later
normal writer has a PnL figure; unknown is not rewritten as realised evidence.

Bounded duplicate correction: ACCEPTED by independent review. Broader assembled
series and deployment: INCOMPLETE. Main runtime/config/accounts/collectors are
unchanged. Next: integrate this reviewed delta into a clean series candidate,
verify its exact baseline and run final integration proof before deployment.

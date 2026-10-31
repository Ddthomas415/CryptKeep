# Exit retry persistence: existing-store boundary

2026-10-28. AUDITOR stage. Evidence ACCEPTED_WITH_RISK after separate review.
The accepted pure exit planner is unchanged; durable integration INCOMPLETE.

## Result

SHOWN: retry state cannot safely be placed in intent metadata and then treated
as protected from the existing upsert. storage/execution_store_sqlite.py
upsert_intent replaces meta_json on conflict and truncates serialized metadata
to200000characters. No production state or account was inspected.

Four disposable-SQLite cases execute the unchanged selected upsert method:

- An ordinary same-ID upsert omitting the control key deletes it.
- A deliberately interleaved stale writer restores attempts=0 after a committed
  attempts=1/outcome=unknown update. This is a controlled lost-update schedule,
  not a stress test or proof of an observed production race.
- Explicit unchanged metadata roundtrips, a positive control rather than proof
  that all writers preserve it.
- Oversized metadata is truncated to200000characters and cannot be JSON-decoded.

These passing tests reproduce persistence hazards. They do not repair them,
prove that a real counter was reset, or authorize changing existing upserts.
Missing/corrupt state must remain unknown; it must never initialize as zero
attempts or grant another submission.

## Fit Before New Implementation

ExecutionStore's normal constructor creates/upgrades tables, so it was not
instantiated. Tests AST-read its existing DDL into a temporary database and
run only upsert_intent with a connection factory restricted to that fixture.
The production DB locator, PRAGMAs and constructor were not invoked.

OrderDedupeStore already owns remote-ID/uncertain-submit states; do not reset or
repurpose them as a retry timer. Generic strategy-state modules have different
schemas and database ownership and are not interchangeable stores.
storage/live_intent_queue_sqlite.py has a live_consumer_state(k,v) table. The
accepted cap prototype already uses caller-owned transactions on that schema.
This is a candidate reusable storage pattern, not evidence that the current
ExecutionStore database contains that table or authority to create it there.

## Proposed Next Objective

Prepare an offline checkpoint prototype using an isolated prefixed row in the
existing key/value schema and caller-owned disposable connections. No new table,
service, migration, actual DB path or default initialization. Reserve a potential
attempt atomically before any future submit; persist uncertainty across restart
and keep alert records independent of overwritten intent metadata. A reservation
may consume budget without an actual send, so that conservative counting rule
must be explicit. Do not automatically release uncertainty on elapsed time.

Required proof: two competing writers cannot reserve twice; restart preserves
the uncertain reservation; missing/corrupt state and failed writes cannot grant
a reservation; repeated alert events retain identity without claiming delivery.
Only explicit reconciliation may settle a reservation. Co-location with actual
intent/dedupe records, cross-store atomicity, initialization/cutover authority,
live values and real fill truth remain UNVERIFIED and require later design.

## Verification

VERIFIED_ENV, venv, actual SQLite only in pytest temporary files; invented rows,
selected unchanged method/DDL, socket/DNS refusal and no application imports:

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_exit_deferral_persistence_boundary.py

Author4passed0.23s,exit0. No previous41/72case suite or backtest rerun. No
production-source change, private/account/credential access, migration/real DB,
network, service/scheduler/pilot, settings/trading/capital, commit or push.
Only diagnostic tests, this note, current task index and visible log changed.

## Actual Independent Review

Reviewer01a11481-515d-7473-8ee3-7f6864c6d40b, submission
01a18431-4031-7b02-a8d9-d8101fe92745, returned ACCEPTED_WITH_RISK for bounded
persistence-hazard evidence only. No material evidence defect found. Verified
all ten bindings/reproduced tests.diff; independent bound command4passed0.21s.
Test SHA256:cdd26f94b98e4bc317547a4f07687865b582747ac6e8f94caf93a6de3582a2e2.

No test/source changes after review. Original BINDINGS and submitted checkpoint
are preserved; CLOSURE records the later disposition. The proposed KV design
is not adopted or accepted by this review. Real PRAGMA/crash behavior,
co-location/cross-store atomicity and durable integration remain
UNVERIFIED/INCOMPLETE. Reviewer made no edits or real-state/private/network/
runtime operations. Accepted planner/application source hashes are unchanged.

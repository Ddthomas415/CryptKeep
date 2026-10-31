# Unknown-interval funding observations: offline implementation

2026-10-28. ENGINEER stage, HIGH risk financial evidence/persistence.
Acceptance: READY_FOR_INDEPENDENT_REVIEW.
Original Fix3 production integration: INCOMPLETE.

## Adopted decision and implementation

Operator approved the proposal to retain unknown-interval observations as raw
diagnostics, excluding them from normalized scoring and annualized estimates.
Decision: "approve. carry out the next steps".

Implemented scripts/research/synthetic_funding_observations.py. This is an
unwired offline adapter, not a replacement collector, store migration or source
application. Existing funding sources, historical artifacts, production table
and consumers remain unchanged.

The existing funding table cannot store NULL intervals. Instead of inventing
zero/eight or rewriting history, the adapter uses a namespaced JSON value in
an explicitly pre-created disposable fixture with the existing
live_consumer_state(k TEXT PRIMARY KEY, v TEXT NOT NULL) schema. The schema
was checked in storage/live_intent_queue_sqlite.py; no production constructor,
database locator or migration is invoked. This proves a serialization/
transaction boundary, not that this KV is the right production co-location.

## Contract

- Preserve the JSON payload, exact rate source field, caller capture timestamp,
  reported exchange time fields and unverified plan interval separately.
- A nextFundingRate field is labelled predicted by name, not authenticated.
  A fundingRate field is not automatically called settled.
- Read only explicit positive interval evidence from supported payload fields.
  Missing, invalid or contradictory interval evidence becomes unknown with a
  reason. Plan interval is retained as an unverified claim, never a fallback.
- Unknown intervals have no per-eight-hour rate, annualization or neutral
  signal. Known intervals also remain unscored: the adapter has no verified
  venue/formula contract and no API to certify one.
- Append immutable, content-addressed observations in an owned transaction.
  Repeating identical input is idempotent. Changed evidence appends a new
  record; it does not revise an earlier observation.
- Require an explicit byte budget and timezone-bearing capture time.
  Unsupported/non-finite JSON, absent schema, conflicting stored evidence,
  and active caller transactions fail rather than reset, truncate or overwrite.
- Readback checks content hash/schema version. A digest is corruption evidence,
  not authenticity, tamper-proof storage or protection against other writers.

No DDL, connection creation, implicit initialization, overwrite, deletion,
credential/API access, output signal or execution authority exists in the adapter.
All normalization eligibility is false. No caller currently uses this adapter.

## Verification

VERIFIED_ENV: isolated venv, invented public payloads, in-memory/disposable
SQLite, socket/DNS refusal. No application-entry/config/credential modules or
SDK clients imported.

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_synthetic_funding_observations.py

Author result: 35 passed in 0.21s, exit 0. Covers missing/invalid/conflicting
intervals, explicit 1h/4h/8h without formula certification, predicted source and
separate timestamp retention, caller-copy isolation, raw nested payload,
zero/invalid rates, real temporary SQLite close/reopen, duplicate writes,
append-vs-overwrite, active caller transactions, absent schema, rollback after
injected INSERT failure, other namespaces, corrupt rows, byte limits and timezones.
No concurrent writer/process-kill proof, full suite, market run or actual
collector/venue/storage compatibility proof is claimed.

The original eight-case defect reproduction and production-source hashes
remain preserved. It is still correct that the existing collector and readers
are not repaired. This prototype must not be presented as deployed Fix3 closure.

## Limits and next proof

Assumption 1: callers supply public JSON and declare capture time honestly.
False input remains a false observation; hashes do not authenticate it.
Assumption 2: callers own a disposable fixture and grant transaction ownership.
Passing a real database would cause writes; the adapter cannot establish
path provenance from a connection object.

No production location, namespace ownership/capacity/retention policy or
collector integration is adopted. Existing arbitrary KV writers are not fenced.
Historical interval/source/formula truth cannot be recovered from discarded
fields. Current venue formula/timestamp semantics remain UNVERIFIED.

Next: separately review exact implementation and test/diff bindings; then
choose an explicit production persistence/reader compatibility path and verify
venue/formula evidence before source application or normalized scoring.
The previously used reviewer reported a usage limit; no new review attempt or
independent acceptance is claimed in this implementation.

No collector/scheduler/pilot/service, account/credential/public-fetch,
production database/DDL/migration, capital/risk/trading, dependency, commit or
push action. No strategy, campaign, archive or frozen result changed.

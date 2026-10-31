# Funding strategy-context qualification boundary

2026-10-29 America/New_York. ENGINEER stage, HIGH risk strategy input and storage
read boundary. Acceptance: READY_FOR_INDEPENDENT_REVIEW. Offline source only.

## Confirmed next gap and scope

Source trace found funding_context_from_crypto_edge_store still returned ready
for fresh legacy rates without field/interval qualification. strategy_runner's
registry helper consumes that context. A new fake-store probe failed before
repair (1failed0.19s: okTrue when no qualified basis existed). This is a shown
source/fixture defect, not an observed live trade or running-host claim.

Applied the already adopted rule that unknown provenance cannot authorize
normalized funding strategy actions. Freshness and a numeric stored interval
do not establish that provenance. Legacy rows remain available as diagnostics.

Impact: funding_extreme cannot receive legacy unqualified context through this
adapter. Both its buy and sell strategy signals are withheld until a qualified
basis/source is implemented. Underlying strategy rules, other strategies,
protective-exit code, settings and schedules are unchanged; their runtime
behavior was not certified by this check.

## Repair and preservation

- Context retains missing/invalid/stale checks, but a fresh legacy row returns
  funding_context_unqualified, eligibilityFalse and no context. Raw row and
  capture/snapshot metadata are retained; no eight-hour fallback or percentage
  becomes an actionable context. Caller boolean/interval assertions do not
  qualify a row.
- Default/explicit-path access uses SQLite URI mode=ro and query_only rather
  than a schema-initializing store constructor. Missing paths do not create
  files/directories. Error details expose exception type, not message content.
- Supplied store objects own their read behavior; no claim is made that an
  arbitrary caller-provided object cannot have side effects. SQLite read-only
  access can still coordinate WAL/shm files; this is not a promise of no
  filesystem/daemon side effects in an eventual actual-host read.
- Legacy signal replays and forward-price joins now carry explicit model-only,
  unqualified funding metadata. Their rules, model actions, arithmetic, fees,
  dataset hashing and observed/saved studies are not retuned or rerun.
  ok still means the model artifact has sufficient input, not economic
  qualification. Consumers must not discard the qualification fields.

Existing research outputs/artifacts remain immutable. The new label does not
magically repair old artifacts or turn modeled returns into real fills/profit.

## Contract before positive normalization

Cash-cost normalization and crowding interpretation are different contracts:
confirmed per-period rate/interval may support a modeled common-time cash
equivalent, but not automatically a common premium/crowding meaning across
formula changes/caps. Neither is currently qualified by this adapter.

A positive path must bind native rate semantics, effective interval/time,
source evidence and the intended economic quantity. Source/receipt freshness
alone is insufficient. No boolean flag, current formula announcement or
legacy eight-hour field supplies that missing binding. No positive normalizer,
new strategy criterion or market experiment is introduced in this patch.

## Verification

VERIFIED_ENV: invented data in explicit temporary SQLite/fake stores,
selected actual strategy-runner helper plus actual pure registry, no runner
application import/execution. New tests refuse external sockets, non-temporary
SQLite targets and context store initialization. Read-only URI handles reserved
filename characters; controlled DELETE-journal fixture bytes/schema unchanged.

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_funding_context_qualification.py tests/test_crypto_edge_context.py tests/test_funding_context_replay.py tests/test_funding_context_price_join.py tests/test_funding_archive_views.py tests/test_crypto_edge_analytics.py tests/test_crypto_edge_store_sqlite.py tests/test_dashboard_crypto_edge_research.py tests/test_funding_consumers.py tests/test_funding_receipts.py tests/test_funding_store_bridge.py tests/test_synthetic_funding_observations.py tests/test_funding_provenance_boundary.py

Final author252passed2.83s,exit0. Initial17passed0.67s before the expanded
qualification/read-only/parity tests. Includes interval/claimed-flag matrix,
missing default path, sanitized error, actual selected registry boundary,
read-only old schema and filename escaping, v1 replay/join parity apart from
qualification/generated time, fresh metadata isolation and prior suites.

Two existing context expectations changed from ready/actionable percent to
unqualified/raw-only; originals are archived. Existing replay/join tests retain
their numerical expectations. All comparisons use invented fixtures only.
No archived market-data strategy rerun, full suite, real SDK/provider capture,
actual host/DB read, Streamlit/auth, process/service or trading operation.

## Handoff

Before copies and exact source/test diff are retained under
docs/review_artifacts/funding_context_qualification_20261029/.
Freeze hashes for separate GATE; author cannot accept its own high-risk change.
Source evidence does not certify deployed use or existing positions.

Remaining Fix3: evidenced positive native/effective-interval/cash/crowding
contract, collector/raw-mode operational authorization and runtime proof.
Legacy modelling APIs retain old assumptions for reproducibility and are not
financial qualification/security gates. No actual configuration, account,
credential, public capture, production DB/schema/migration, collector/service/
scheduler/pilot, capital/risk/trading, dependency, commit or push changed.

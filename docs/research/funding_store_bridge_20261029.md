# Funding raw-journal storage bridge

2026-10-29 America/New_York. ENGINEER stage, HIGH risk persistence/financial data.
Acceptance: READY_FOR_INDEPENDENT_REVIEW. Source-only implementation; original
Fix3 production collection/scoring repair remains INCOMPLETE.

## Chosen compatibility path

Use a separate raw_funding_observations journal in the existing research-store
database, not a fabricated numeric interval or an in-place rewrite of
funding_snapshots. No separate server, database file, scheduler or KV owner is
introduced. Existing funding table/schema, append API, normalized readers and
reports retain their existing behavior, including their previously documented
limitations. This bridge does not make their annualization correct.

The source DDL now defines the additive raw table and source/capture index.
Existing _init_db would create them when the changed source is deployed and
the store initialized. That is a future real schema side effect, not an
operation performed here. Tests initialize disposable files only.
Do not deploy, initialize a real store or reconnect the collector from this
handoff without the required operational authorization.

## Implementation

- Copied the separately accepted decoder byte-for-byte to
  services/analytics/funding_observations.py. Its hash remains
  e884234f22607b551fa81d662d192ad9bb9e4b72e0a7466825114c6d44a7df89.
  The original research prototype remains unchanged as the reviewed reference;
  no research artifact or original test was replaced.
- CryptoEdgeStoreSQLite.append_raw_funding_observations accepts only explicit
  source, row/encoded-value byte budgets and raw input objects. It validates
  the entire batch before inserts, then uses one owned connection/transaction.
  Identical content deduplicates within a source; changed content appends.
  Conflicting stored content is refused rather than replaced.
- recent_raw_funding_observations requires an explicit source and positive
  limit, checks hash, reconstructed schema/derived fields and indexed capture
  time, and returns a separate diagnostics envelope. Legacy observations are
  not imported, relabelled or certified. No raw row enters normalized reports.
- Index capture times are UTC-canonical for ordering. The exact supplied
  capture time and reported exchange timestamps remain separately preserved.
- All observations remain normalization-ineligible; known intervals alone
  cannot certify venue/formula basis. Raw inputs, source and clock remain
  caller assertions, not authenticated observations.

New API budgets cover all presented rows and encoded SQL values before
deduplication. There is no pruning, overwrite, release or history repair.
The new API owns and closes its connection; it does not adopt caller transactions.
The raw readback validation is not an adversarial database access-control gate.

## Verification

VERIFIED_ENV: repository venv, temporary SQLite only, network/DNS refusal,
production default-directory helper refused. Full store module is imported,
not an application entrypoint or SDK exchange. No credential/account/config
loader or actual collector is invoked.

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_funding_store_bridge.py tests/test_synthetic_funding_observations.py tests/test_crypto_edge_store_sqlite.py

Author result: 73 passed in 0.63s, exit 0. Covers the 35 accepted decoder/
prototype cases, new bridge and existing store regressions. The bridge tests
verify exact decoder promotion; an old-DDL fixture with unchanged legacy rows/
schema; unknown interval after close/reopen; explicit 1h/4h/8h still unscored;
source isolation/idempotency; timezone ordering; row/byte budgets; invalid
later input and injected second-INSERT atomic rollback; corrupt content and
rehashed normalization forgery refusal; two independent SQLite connections
racing identical appends with only one insert.

Not run: full suite, market-data experiments, current API capture, process-kill/
power-loss durability, real database schema operation or deployed collector.
SQLite busy waiting retains the existing connection timeout; no new runtime
deadline or performance guarantee is claimed.

## Preservation and next boundary

Original store bytes are archived under
docs/review_artifacts/funding_store_bridge_20261029/before/.
The older defect diagnostic bindings describe that original source; their
store hash is historical, not the new store's current hash. Other original
collector/alternative-data/summary sources remain unchanged.

The reviewed prototype, earlier review records and other agents' entries remain
untouched. Exact new source/test diff and dependencies are frozen for one
separate GATE review. This author cannot accept its own high-risk implementation.

Next after review: collector receipt capture and explicit raw-writer integration,
plus native-to-unified field lineage and source/interval/formula verification.
That must not silently preserve old defaults, certify legacy observations,
normalize an unverified venue formula, or activate a new collector/job.
No API, scheduler, service, real DB/DDL/migration, account, credentials, trading,
capital/risk settings, dependency installation, commit or push operation occurred.

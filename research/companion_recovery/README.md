# Companion ingestion recovery candidate

## Real offline feed parsing (2026-10-01)

Four fixture cases now use feedparser 6.0.11, BeautifulSoup 4.12.3 and the
recovered document model. They exposed feedparser's missing-updated alias to
publication time. Ingestion now reads concrete updated keys so publication-only
feeds do not invent revision timestamps. Combined temporary-environment tests:
45 passed, 1 persistence opt-in skipped in 0.73s. New date correction is
READY_FOR_INDEPENDENT_REVIEW. Transport/storage are still mocked in these tests;
this is not a running feed-to-database pipeline or semantic-quality evaluation.
The separate persistence cleanup correction was accepted by reviewer Huygens.

## Disposable persistence proof (2026-10-01)

Review follow-up: Locke found cleanup gaps after startup failure or index-close
failure. The test now checks the owned cluster in an unconditional cleanup path,
and database cleanup runs even if index close raises. Three cleanup regressions
pass. Corrected opt-in run: 4 passed in 2.43s; default regression: 41 passed,
1 skipped in 0.45s. Updated test READY_FOR_INDEPENDENT_REVIEW. Earlier human
acceptance preceded these findings and does not cover this new correction.

`tests/test_companion_memory_persistence.py` is opt-in via
`CBP_TEST_MEMORY_PERSISTENCE=1`. It starts an isolated PostgreSQL cluster on a
temporary Unix socket (no TCP listener) and uses Qdrant client 1.12.1 local mode
with on-disk storage. The app environment is not modified. Temporary environment:
`/tmp/cryptkeep-memory-integration`; psycopg/psycopg-binary 3.2.3, pytest 8.3.4.

SHOWN: 1 passed in 3.39s on PostgreSQL 14.20. An injected pre-upsert exception
leaves a real SQL row but no vector result; retry indexes canonical stored
content, retrieves it after closing/reopening the local index, preserves null
publication and revision metadata, and excludes changed retry asset tags.
The disposable database was stopped; `pg_ctl status` reported no server running.
Default app regression: 38 passed, 1 opt-in test skipped in 0.46s.

Scope remains limited: recovered function bodies run via AST harness, with
minimal compatible SQL tables, not full migrations/TimescaleDB. No Qdrant server,
HTTP transport, RSS parsing, MinIO, concurrency, crash recovery, semantic search
quality or production activation is established. The user approved this bounded
test deliverable after reviewing the work log/history: ACCEPTED_WITH_RISK
(2026-10-01, human acceptance). This does not claim completion of the separately
requested agent review. Overall news recovery remains INCOMPLETE.

## Storage/index recovery candidate (2026-10-01)

`memory_retrieval.py` is recovered from
`ad18488df^:phase1_research_copilot/memory_retrieval/main.py`. The historical
database wrapper autocommits SQL inserts before indexing. Its duplicate branch
previously returned success without checking or repairing the vector index.
The candidate reindexes the persisted row, not the retry payload, and requires
completed indexing before success. Local isolated verification: 16 storage tests
and 20 existing news tests passed together (36 passed in 0.38s). These execute
recovered function bodies with in-memory SQL/vector boundaries, not real services.
Locke independently accepted the sequential retry source repair as
ACCEPTED_WITH_RISK (36 tests passed independently). Subsequent test-only work
replaces the fixed search result with a stateful in-memory index: failed or merely
acknowledged writes remain absent, completed retries expose the canonical record,
and changed retry asset tags do not change search membership. All 38 tests pass
locally; that test delta is READY_FOR_INDEPENDENT_REVIEW. This does not establish
real service integration, ranking, persistence or concurrent ingestion.

Next real integration proof must persist a parsed document, interrupt indexing,
retry the same document, and retrieve that same canonical record by its stored
ID. It must preserve publication/revision metadata and fail rather than report
success while indexing remains unavailable. In-memory adapters do not establish
PostgreSQL/Qdrant/MinIO behavior, network authentication, or restart recovery.
No new services are activated by this candidate. Hash embeddings remain a stub,
not evidence of semantic retrieval or event-aware trading.

## Specialist pilot repair (2026-10-01)

Ingestion no longer sends a forced `timeline_hint=present`; the recovered
parser's existing keyword inference is allowed to run. This does not establish
semantic accuracy. Only RSS `published` supplies `published_at`; absent
publication stays null, even when `updated` exists. RSS `updated` is preserved
separately as `metadata.updated_at` (null when absent). Both timestamps use the
existing UTC normalization. Malformed or timezone-free values in either field
fail the entry before parser/storage calls and leave it eligible for re-polling;
no date is fabricated. Parser and model files are unchanged.

SHOWN / VERIFIED_ENV: `./.venv/bin/python -m pytest -q
tests/test_companion_news_recovery.py` returned **20 passed in 0.24s**.
Caller-level tests execute recovered poll, outbound request, storage, document
builder, and timeline-inference function bodies. They capture parser requests
and storage payloads for past/future text, missing dates, updated-only dates,
distinct publication/revision dates, invalid dates, and storage-failure re-polls.

UNVERIFIED: this AST harness is unit proof only. Feed reading, HTTP transport,
HTML extraction, audit emission, and the retry wrapper are fakes. HTTP request
validation/serialization, actual retry/backoff, persistence/retrieval, service
startup, and live integration are not proven. No external requests, services,
credentials, dependencies, deployments, or trading were used or changed.
Independent reviewer Locke accepted this isolated caller/date repair on
2026-10-01 as ACCEPTED_WITH_RISK; the user subsequently approved it. Independent
verification returned 20 passed in 0.24s, with additional request-model/JSON
and malformed-date probes. This is not service integration proof. Overall
recovery remains INCOMPLETE; activation is not approved. Historical downstream
indexing recovery remains separate unfinished work.

## Second recovery slice (2026-09-29)

Recovered `parser_normalizer.py` and `models.py` verbatim from the same historical
parent revision. Ingestion now normalizes RFC RSS dates and ISO timestamps to
UTC before passing them to the parser. At that stage, missing publication
incorrectly fell back to revision time (corrected in the pilot repair above);
invalid or timezone-free dates fail rather than inventing an availability time.
Nine isolated tests pass, including the historical Pydantic document contract.
The test's dynamic module required explicit Pydantic namespace rebuilding;
that harness issue was corrected without changing the historical schema.

Full integration is NOT proven: BeautifulSoup is absent from the current venv,
and PostgreSQL/Qdrant/MinIO and the historical shared dependency closure have
not been restored or started. No existing environment packages were changed.
The recovered parser must not be exposed as a service before review of URL
fetching and authentication. Publication normalization is not proof of timely
historical receipt or absence of look-ahead bias.

Source: `ad18488df^:phase1_research_copilot/news_ingestion/main.py`.
This preserves the historical module for isolated repair, not deployment.
It is not wired into root startup and cannot currently run standalone without
the historical shared modules and parser/memory services.

Changes: forward service authorization on parser and storage requests; reject
missing outbound credentials before requests; mark a document seen only after
storage explicitly confirms success. No credentials were read or modified.

Local proof: `tests/test_companion_news_recovery.py` executes selected original
function bodies with fake dependencies, without importing service startup.
Four tests pass: missing credentials, header forwarding, exception retry, and
unconfirmed storage retry. These are unit tests, not ingestion/retrieval proof.

Remaining: restore dependency closure, prove authenticated parser-to-persistent
storage-to-retrieval integration and timestamp behavior across that boundary, and assess
concurrent polls, persistent deduplication, URL-fetch safety, and error health
reporting before activation. Historical hash embeddings are not semantic search.
No live feed or adaptive strategy behavior is demonstrated by this candidate.

Risk: HIGH (auth and background-service source). State:
READY_FOR_INDEPENDENT_REVIEW for this bounded repair; overall recovery INCOMPLETE.

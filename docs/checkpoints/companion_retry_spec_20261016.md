# Existing companion: single instrumented retry specification

Revision: 2, 2026-10-16. Active role: DIRECTOR.
Document state: READY_FOR_INDEPENDENT_REVIEW.
Operational state: INCOMPLETE. Runtime authorization: NOT GRANTED.
Risk: HIGH. This document specifies an operation; it does not execute it or
establish that a compliant runner already exists.

## Purpose And Preserved Evidence

Test one real repository dashboard-client explanation against the existing
stored-evidence service, retaining sanitized diagnostics before any rejection.
The accepted offline token-boundary repair is not proof that the earlier
runtime failure is fixed. Its cause remains UNRESOLVED.

Historical records remain unchanged:
- `companion_reconnection_20261016.md`: failed request and rollback.
- `companion_diagnostics_20261016.md`: diagnostics implementation and review.
- `companion_asset_guard_repair_20261016.md`: scoped guard repair and review.

No container inventory, service request, credential access, test run or startup
is performed while preparing this specification. Current runtime state and
installed-image/source compatibility are UNVERIFIED, not inferred from October11
or the previous October16 operation.

## 1. Exact Scope And Preconditions

Only these seven already-existing container identities may be started:
1. `phase1-timescaledb`
2. `phase1-qdrant`
3. `phase1-minio`
4. `phase1-audit-log`
5. `phase1-risk-stub`
6. `phase1-memory`
7. `phase1-orchestrator`

Use the existing local Docker daemon, pinned to
`unix:///Users/baitus/.docker/run/docker.sock`; do not follow a default/remote
context. Docker Desktop must already be available. No opening/restarting the
daemon, Compose up, build, pull, recreation, migration, schema initialization,
container/volume deletion, extra service, collector, schedule, image update,
exchange/private account access, model API call or trading action is included.
The isolated-stack verifier is NOT the runner for this operation.

For this proposal, all seven must initially be stopped. If any is running,
missing, restarting, unhealthy or ambiguous, abort before starting anything;
preserve that state rather than taking ownership of an existing process.
Unrelated running containers may remain and must not be touched.

## 2. Baseline And Immediate Recheck

Before any start, record an allowlisted inventory for all containers: full
container ID/name, image content ID, state, StartedAt/FinishedAt, restart count
and restart policy. For the seven targets also record volume name/ID/driver and
destination, bind-mount identity, network identity, port bindings, healthcheck
definition and entrypoint/command identity. Redact/hash sensitive path or
command fields; never dump full inspect output or environment values.

Verify that the three existing data volumes match the operation record's named
volumes, and that initialized PostgreSQL data already exists (PG_VERSION16).
No image tag alone is an identity. Compare content IDs against the earlier
record, but do not assume an unexplained change is acceptable. This cold
baseline records metadata and expected namespace names from pinned artifacts,
not successful connectivity to stopped services. Existing schema/archive/
bucket/collection existence is checked only AFTER authorized storage-only
startup and BEFORE application startup, within the 420-second verification
budget. Failure there triggers rollback of owned storage; no resource creation.

Immediately before the first start, repeat the metadata-only inventory and
compare it with the baseline. Any target identity, mount, image, state or
restart-policy difference aborts. Before every subsequent start, recheck that
specific container ID. Resolve the local CLI identity without changing tools.
Do not issue an operational command whose environment remains UNKNOWN_ENV.

A future controller must reserve one new secret-free attempt receipt before
starting. Record each intended start by exact ID before issuing it, its result,
observed state transition and StartedAt. No name-based rediscovery/recreation.
Concurrent operators must not change these targets during the attempt; if
ownership becomes ambiguous, do not stop an ambiguously owned container.

## 3. Credential And Network Boundary

Only the existing internal service token may be transferred into the probe,
using a private parent/child memory channel. No token in shell arguments,
stdout/stderr, prompts, logs, diagnostics, files, shell history, .env edits,
URLs or persistent environment/config changes. Do not print hashes of tokens.
Do not dump container environments. Never retrieve exchange credentials.
Existing database/object-store authentication stays inside the services that
already own it; no DSN or additional credential is exported to the host.

The short-lived probe must close token-bearing channels and clear references
on every exit; no promise of forensic memory erasure is made. No debug dumps.
Requests use only these exact recipients, bound by preflight to the seven
pinned container identities: host loopback bindings for ports5432, 6333, 9000,
8009, 8008, 8007 and8002; inside their existing Docker network, aliases
timescaledb:5432, qdrant:6333, minio:9000, audit-log:8009, risk-stub:8008,
memory-retrieval:8007 and orchestrator:8002. Only verified existing bindings may
be used; host loopback alone is not sufficient identity proof. DB/object-store
authentication remains internal as above. No other recipient is permitted.

There is no allowance for market-data, parser-normalizer, news-ingestion,
archive-lookup, gateway, exchange, public web or model-API requests, even if
those services already exist or a failed request would be swallowed. Before
any start, inspect the exact installed call graph/configuration for fan-out
and require evidence that all permitted request origins resolve to the pinned
IDs. Abort on out-of-scope or unverified fan-out before dispatch; do not contact
an extra service to discover whether it is present. Do not patch the server or
substitute fabricated tool results to make this gate pass.

No environment/system proxy, redirects or alternate endpoint discovery. Image-side
audit/SDK transports need the same origin/proxy/retry verification; a safe host
client does not prove safe downstream behavior. No configuration is changed to
make a failed precondition pass.

## 4. Hard Time Budget And Single-Attempt Policy

One attempt ID, one staged startup, at most one explanation submission. No
automatic retry, second question, parameter change, alternate backend, polling
loop, repair-and-resubmit or implicit client/server/SDK retry.

The proposed controller uses an absolute monotonic deadline of 600 seconds
from baseline capture. Verification stops by second420; up to 180 seconds are
reserved for diagnostics and rollback/final inventory. Each call is bounded by
the smaller of its cap and remaining phase budget:

| Operation | Cap |
| --- | --- |
| Metadata/identity command | 10s |
| Each start command, issued once per stopped ID | 15s |
| Each HTTP health/connectivity request | connect2s, total5s |
| Each read-only storage check | 5s connect/statement, 10s wall |
| Single dashboard child/query | 45s hard child wall; HTTP cap30s |
| Each rollback stop, once per owned ID | 8s grace; 12s command wall |
| Final inventory | 10s |

After the storage stage, one fixed 15-second settling interval is allowed;
after the application stage, one fixed 10-second interval. These are not
readiness polling. Each acceptance probe runs once; cold-start failure ends
the attempt rather than causing more probes. Insufficient remaining budget
means failure before dispatching the next operation.

A child timeout is NOT proof of server cancellation or of an unexecuted Docker
command. The receipt must preserve that uncertainty and initiate bounded
rollback. At second600 all owned probe subprocesses must have terminated and
the controller must return; if daemon cleanup cannot be verified, report
INCOMPLETE/cleanup-unverified, not a fabricated successful rollback. No automatic
stop retry, daemon restart, force removal or unapproved escalation follows.

Existing periodic Docker healthchecks are disclosed monitoring, not permission
for controller polling or repeated explanation calls. Their exact definitions
must be reviewed. If the no-repeat boundary also excludes that pre-existing
monitoring, unchanged-container startup is incompatible; do not disable it.

## 5. Known Compatibility Conditions: Must Not Be Waved Through

SHOWN IN LOCAL SOURCE, NOT VERIFIED IN EXISTING IMAGES:
- `phase1_research_copilot/shared/tools.py::_request_json` calls
  `retry_async(..., retries=1)`. `shared/retry.py` permits a second downstream
  request after a failure. One top-level call therefore does not meet the
  specified zero-implicit-retry condition by itself.
- `memory_retrieval/main.py::_startup` can create a missing MinIO bucket and
  Qdrant collection. Their existence must be proved after the storage-only
  start and before starting memory; no namespace creation is authorized.
- The local orchestrator's core tools include get_market_snapshot and
  get_operations_summary; shared/tools.py can contact market-data,
  parser-normalizer, news-ingestion and archive-lookup with the service token.
  The seven-container startup list alone does not constrain that fan-out.
  If this call graph is present in the installed images, this strict recipient
  boundary fails preflight. No extra-service startup, silent scope expansion,
  query dispatch or runtime suppression patch is authorized as a workaround.
- Audit HTTP and storage SDK settings must be inspected for implicit retries,
  proxy use and logging of sensitive data. They are not certified here.

Future read-only preflight must inspect the exact existing image/mounted code
and effective configuration, without starting application imports. If the
installed path has retries, no proven supported zero-retry setting, unexpected
startup DDL/ingestion, or uncertain token handling, abort before the relevant
start/query. No monkeypatching the server, bypassing guards, changing retries,
redeploying, rebuilding or creating missing resources is authorized by this
specification. A demonstrated incompatibility needs a separately scoped repair
or an explicit reviewed change of the condition, not another blind attempt.

## 6. Health And Connectivity: Separate Gates

Start the three storage containers by their pinned IDs, then check each once.
Only if they pass and existing namespaces are confirmed may the other four
containers be started. Do not use Compose dependency expansion.

| Target/interface | Health requirement | Connectivity/preservation requirement |
| --- | --- | --- |
| PostgreSQL: existing pg_isready interface | accepting connections, exit0 | read-only SELECT1 succeeds; existing documents/audit schema present; no DDL |
| Qdrant: GET /healthz on existing port6333 | HTTP200 | read-only GET /collections/{existing_collection} succeeds; expected namespace exists |
| MinIO: GET /minio/health/ready on existing port9000 | HTTP200 | authenticated read-only HeadBucket of existing bucket succeeds; never create |
| Audit: GET /healthz on existing port8009 | HTTP200, service=audit-log, ok=true | its DB health SELECT1 succeeds; one authenticated GET /v1/audit/events/recent?limit=1 succeeds |
| Risk: GET /healthz on existing port8008 | HTTP200, service=risk-stub, ok=true, no_trading=true | one authenticated GET /v1/risk/status returns allow_trading=false, execution_mode=DISABLED, gate=NO_TRADING |
| Memory: GET /healthz on existing port8007 | HTTP200, service=memory-retrieval, ok=true | db=true, qdrant=true, minio=true through service-owned connections |
| Orchestrator: GET /healthz on existing port8002 | HTTP200, service=orchestrator, ok=true | no_trading=true and openai_enabled=false; actual authenticated path checked by the single query |

Ports/routes are source/documentation references, not verified current host
bindings. Preflight must confirm existing bindings and image schemas; no
substitution of endpoints if a check fails. Storage existence checks must use
existing internal authentication without exporting credentials. A health
response is not a cited query, usable retrieval or source-authenticity proof.

## 7. One Query And Explicit Explanation Acceptance

Freeze asset=BTC, question="What news explains Bitcoin liquidations?" and
lookback_minutes=60 before execution. No alternate question on empty results.
Use the actual dashboard client's companion transport, normalizer, guard and
provider/fallback checks under capture_explain_diagnostics(). The unrelated
legacy-primary route must be explicitly suppressed inside the disposable probe
before dispatch, rather than contacted and allowed to trigger a second path.
This proposed harness isolation must itself be reviewed; no guard is bypassed.
One companion POST /v1/explain, no other explanation endpoint. A timeout,
authentication failure, invalid response or static fallback exhausts the attempt.

Every gate below must independently pass; missing evidence is UNVERIFIED and
fails operational acceptance:
- Response: HTTP200, expected object/fields, BTC identity, nonempty explanation.
- Safety: execution_disabled is exactly true; execution.enabled is false; risk
  posture stays NO_TRADING. No truthiness conversion or optimistic default.
- Provider: known service-generated output, never dashboard_fallback/mock data.
  A deterministic backend provider named fallback is not automatically static;
  it passes only if the following stored-evidence checks independently pass.
- Retrieval: at least one question-matched stored document, not only a market
  snapshot, stale summary, arbitrary URL, evidence count or confidence score.
- Citation identity: positive persisted document_id exists in the pre-existing
  documents table; URL/source/content hash and the approved article-view mapping
  agree. Use one parameterized read-only query through service-owned DB auth;
  no ingest endpoint, upsert, archive repair or new document. Existing view IDs
  must map to original persisted records, not be guessed from an ID label.
- Relevance: cite actual archived Bitcoin/liquidation content supporting at
  least one factual statement in the answer; mere keyword count is insufficient
  for a claim of explanation relevance. Record identity/traceability separately
  from topical support, and distinguish topical support from causation.
- Limits: unknown current-market cause, stale context or insufficient evidence
  must be explicit. A fabricated causal explanation cannot pass because its
  citations exist. If relevance cannot be assessed with approved, non-sensitive
  evidence within the budget, mark UNVERIFIED and fail; do not claim semantic
  validation from a keyword-only interface.

No fresh browsing, article fetching, model call or new evidence ingestion is
part of this query. Do not force LLM activation or alter the question to get a
positive result. A useful honest no-evidence answer can diagnose behavior, but
does not pass this particular stored-citation acceptance target.

## 8. Diagnostics, Failure And Success Handling

Retain a secret-free phase receipt BEFORE checking assertions and BEFORE
cleanup: attempt ID, UTC/New York time, monotonic elapsed time, expected and
observed metadata identities, start ownership, call counts, HTTP status,
sanitized stage/reason/shape/provider category, safety flags, citation hashes,
separate health/connectivity/retrieval/identity/relevance outcomes and cleanup
state. Hash citation IDs using an explicit canonical string representation.
Never save raw response bodies, prose, credentials, headers, URL query strings,
full environment/inspect output, raw stderr, uncensored service logs or dumps.

If any gate fails or times out, stop dispatching work and record the failure
first. Stop only exact baseline-stopped IDs recorded as started by this attempt
with confirmed transition/StartedAt; application dependencies first, storage
last. No stop of pre-existing/unrelated containers. If ownership is ambiguous,
preserve the container, record ambiguity and request operator disposition.
Compare final inventory with the baseline: original container/image/mount/volume
identities and unrelated states unchanged, owned targets stopped. Incomplete
cleanup is reported honestly; no repeated stop or removal command.

Proposed success handling: leave the seven existing services running ONLY if
all gates, final inventory and side-effect checks pass and the eventual written
authorization explicitly permits that outcome. Do not change restart policies,
add persistence jobs or call this sustained operation. Otherwise rollback;
ambiguity is not success. Suggested result label: PASSED_SINGLE_CITED_QUERY,
with a separate runtime acceptance state assigned by review, not automatically.

## 9. Side Effects That Rollback Does Not Undo

Possible normal writes: PostgreSQL crash recovery/WAL/checkpoints, service
startup metadata, MinIO/Qdrant internal metadata, daemon health/access logs,
risk-status and explanation audit rows, plus the new sanitized local attempt
receipt. Existing healthchecks may run autonomously. These are not read-only
effects merely because the question concerns stored data. Missing bucket or
collection creation, schema migration, ingestion/indexing and new documents
remain prohibited. Stopping services does not revert permitted writes, scrub
logs, undo server-side requests or restore data bytes to their prior values.
No claim of database backup, restore proof, durable availability, trading
readiness or profitability follows from success.

## 10. Submission And Review Conditions

This revision specifies all requested controls. It is NOT executable approval:
effective image retry/SDK behavior, startup compatibility and the future
timeout/ownership controller remain unverified. No operational authorization
is requested until those conditions and the proposed harness isolation have
been reviewed. A compliant retry may abort before startup; that is not a reason
to relax the conditions silently.

Source inspection and document consistency checks only; no pytest is claimed
for this documentation-only revision. Prior test counts are not new results.

Interface references: local service routes, shared/tools.py, shared/retry.py,
shared/audit.py, dashboard/services/views/_shared_http.py and market_view.py.
Public endpoint references (not evidence of installed-image compatibility):
[Qdrant service API](https://ui.qdrant.tech/),
[MinIO healthcheck source](https://github.com/minio/minio/blob/master/docs/metrics/healthcheck/README.md).

## Document Review Record

Separate AUDITOR found two specification issues: downstream recipients were
not enumerated, and namespace verification was ordered before stopped storage
could be queried. Both were corrected. Bounded re-review confirmed those two
findings resolved for specification consistency only; no operational approval
was given. Installed compatibility remains UNVERIFIED, runtime INCOMPLETE,
authorization NOT GRANTED. Document state remains READY_FOR_INDEPENDENT_REVIEW
for the operator's review. No operation or test was run by either reviewer.

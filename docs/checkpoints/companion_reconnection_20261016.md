# Existing companion reconnection: failed dashboard acceptance, rolled back

Date: 2026-10-16. Active role: AUDITOR after operator-approved bounded startup.
Acceptance state: INCOMPLETE. No source, strategy or trading-readiness acceptance.

## Authorization And Boundary

Operator approved opening existing Docker Desktop, then separately approved
staged startup of seven named existing containers and one dashboard-client
stored-evidence query using the existing service token in temporary process
memory. No build, recreation, migration command, credential change, collector
startup or trading operation was authorized or performed.

Opening Docker revealed19 stopped containers, including12 companion containers.
The12 companion restart policies were `no`. Current volume ownership matched
the `phase1_research_copilot` project. Custom memory/orchestrator/parser/gateway
images and missing temporary deployment files made blind Compose recreation
inappropriate. Existing container identities/configurations were preserved.

## Staged Runtime Evidence

The stopped PostgreSQL container's non-secret PG_VERSION marker was read through
the Docker archive interface:16. The first reader failed because it attempted
backward seeking on a streaming tar; a corrected in-memory reader succeeded
before any container startup. This was a verification-program error, not a
database failure or evidence of a migration.

Approved startup order:
1. `phase1-timescaledb`, `phase1-qdrant`, `phase1-minio`.
2. After readiness checks, `phase1-audit-log`, `phase1-risk-stub`,
   `phase1-memory`, `phase1-orchestrator`.

PostgreSQL accepted connections. Qdrant and MinIO readiness returned HTTP200.
At09:49UTC, audit/risk/memory/orchestrator health all reported `ok: true`;
memory reported `db/qdrant/minio: true`. Risk and orchestrator reported
`no_trading: true`; orchestrator reported `openai_enabled: false`.
Only these seven containers were running at inspection. Roughly four hours
elapsed between startup and continuation; this is not continuous monitoring proof.

## Dashboard Proof Failed

One actual repository dashboard-client call attempted the question:
`What news explains Bitcoin liquidations?` for BTC. It used the existing
orchestrator service token in a temporary client-process environment, no token
in command arguments or printed output, and temporary local client state.
The primary API was explicitly directed at unused loopback port1 so the actual
companion path on8002 would be tested rather than a different legacy backend.

The acceptance check failed with `AssertionError: static_or_unknown_provider`.
It rejected a provider in `(None, empty string, dashboard_fallback)`.
The verifier stopped before its execution-disabled, citation-ID/URL correlation
and authenticated persistent-memory checks. Thus **no successful source-linked
dashboard query or persistent-citation verification is claimed**.

The probe did not retain the sanitized response/provider or HTTP rejection
reason before asserting. The exact transport/normalization rejection cause is
UNRESOLVED. Do not claim authentication failure, unavailable memory, or a
particular client guard caused this runtime result. No second explanation
request was made. No external model call was made by the verifier.

## Confirmed Offline Client Weakness, Not Proven Runtime Cause

`dashboard/services/views/_shared_signals.py::_explain_mentions_foreign_asset`
uses substring matching against BTC/ETH/SOL in narrative fields. An isolated
source-function probe returned true for a BTC sentence containing `whether`,
because that word contains `ETH`. This establishes a false-positive case,
not that it caused the runtime failure. No guard was changed or bypassed.
The default payload explicitly labels `dashboard_fallback`; it is not evidence
of retrieved market/news facts even though it contains static narratives.

## Rollback And Preservation

At09:52UTC, stopped only the seven containers started by this operation, in
dependent-first order. Follow-up inventory showed no running containers.
Docker Desktop remains open as separately approved; it was not quit.

The same image IDs and persistent volume mappings remained after rollback:

| Container | Image SHA256 suffix after `sha256:` |
| --- | --- |
| phase1-timescaledb |068df316fc9dc448a80f1f39d808a06c08a54f35a66eb1d36b92636db78c3a43|
| phase1-qdrant |241edb9d7778327516ef218f8c74e1bd61b5ea42cd4f193cb8d0896199705636|
| phase1-minio |9535594ad4122b7a78c6632788a989b96d9199b483d3bd71a5ceae73a922cdfa|
| phase1-audit-log |a9b205b41e2b7499497e346e49cde29890b36f4d4b1dfee89fb32f4f726953ad|
| phase1-risk-stub |d56c35039ec0bce6b7be7deefa3bc1ec03681e3000dbc5320eb765f9d76905aa|
| phase1-memory |276ce227380a64af3602a045e99b95100461070284dd15df75e07d72a857681d|
| phase1-orchestrator |8fc35122fd4ae2dfbc9048e6951618c6599c425f45626e05e3e1f75ce3a72cc7|

Persistent volume names:
- `phase1_research_copilot_phase1_timescaledb_data`
- `phase1_research_copilot_phase1_qdrant_data`
- `phase1_research_copilot_phase1_minio_data`

Normal startup recovery, service activity and audit writes may have occurred;
rollback does not undo them. No data-content checksum, full backup, semantic
retrieval quality, historical-source authenticity or browser proof is inferred.
No exchange account/key, `.env` file, scheduler or research criterion was changed.

## Next Bounded Diagnostic

Before another operational attempt, make the verifier emit a sanitized failure
receipt (HTTP status, missing-field/asset-rejection reason, provider label and
citation identifiers) without headers, tokens or credentials. Add offline
coverage for the substring false positive and existing fallback behavior.
Do not silently bypass the guard, retune market rules, replace the backend or
claim a diagnosis not captured by the first request. A further startup/query
needs authorization under the same explicit service/rollback limits.

No broad suite was run; this was operational checking plus one isolated offline
source probe. Existing747 configuration-floor caveats and registered strategy
results remain unchanged. No portfolio implementation or experiment was added.

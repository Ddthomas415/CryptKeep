# Existing companion runtime adapter: offline implementation

Date: 2026-10-16. Active role: ENGINEER. Risk: HIGH.
Implementation: READY_FOR_INDEPENDENT_REVIEW.
Runtime objective: INCOMPLETE. Retry authorization: NOT GRANTED.

## Change and scope

Implemented the concrete Backend missing from the prior controller-core handoff:
- `scripts/research/companion_runtime_adapter.py`
- `scripts/research/companion_docker_transport.py`
- `scripts/research/companion_evidence_checks.py`
- Three matching synthetic test modules.
- A separate synthetic controller/adapter wiring test module.

No existing service/controller source, old manifest, research dataset, strategy,
schedule or configuration is modified by this stage. All14 previously reviewed
source/test hashes were checked and remain unchanged. No CLI entrypoint,
automatic approval generator or deployment script is supplied. Construction and
imports are inert. Runtime methods require explicit enablement and the existing
controller's disposable-child context; those API flags do NOT constitute human
permission. There is no claim the service was restored.

## Concrete behavior

The transport constructs argv for the pinned local Docker executable/daemon and
an explicitly empty, canonical temporary Docker config directory. It rejects
unsupported commands and credential/config archive paths. Execution uses no host
shell, user Docker config, proxy environment, retry or detached session. Stdout
and private stdin are handled concurrently with size/time bounds; stderr is
discarded. Only a validated single regular tar member may be read into memory;
links, traversal, extra members and oversized archives are refused, never
extracted. CLI/native-image checks are real code, but were exercised on synthetic
files only, not the installed executable in this stage.

The adapter implements actual inventory, compatibility, exact-ID start/stop,
storage checks, service checks, dashboard probe and evidence-verification calls:
- Inspect emits selected metadata and environment comparison booleans, never a
  raw environment dump. Secret values and secret hashes are not requested.
- The preservation digest excludes dynamic IP/endpoint allocation while binding
  mount/network/port/command/health/configuration metadata. Known service aliases
  must belong to the pinned owners on one network. Custom DNS/extra-host entries,
  alias collisions, non-loopback bindings and unknown/nonlocal volume drivers
  are rejected.
- Installed source bytes must match reviewed per-container pins, including
  service/probe code, relevant SDK files and startup helpers. PostgreSQL PG_VERSION
  must already be16; resource initialization is not an authorized recovery path.
- Policy checks require actual accepted review-record bytes, matching hashes,
  exact image/subject/source bindings and SHOWN policy dispositions. Merely
  supplying hash-shaped strings is insufficient. These records do not prove the
  identity or honesty of their author: the expected manifest hash must be trusted
  from independent review outside this program. No real installed-policy manifest
  was invented or accepted during these tests.
- Storage checks precede application startup: owned PostgreSQL local-socket
  readiness and read-only schema query, Qdrant health/collection reads, and MinIO
  readiness/authenticated HeadBucket. DB/object-store credentials remain inside
  their owning containers. The MinIO shell/curl path refuses unsupported credential
  characters rather than exposing or rewriting them.
- HTTP uses fixed loopback routes, zero transport retries, no proxies/redirects,
  bounded bodies and a five-second whole-request timer in the same controller
  child. Risk, persistence/connectivity, read-only startup and model-disabled
  checks are distinct. The explanation uses the reviewed actual dashboard probe.
- The optional token handoff consumes/closes one owned anonymous pipe/socket;
  there is no file, environment, argv, stdout or credential-discovery fallback.
  Only synthetic tokens were used here. Clearing references is not forensic
  memory erasure.

## Evidence and limits

The fixed verifier runs inside memory's existing credential boundary. It loads
the approved archive and compares lineage against a parameterized SELECT in one
read-only transaction, with connect/statement limits. It returns only five
booleans; public article text, URLs, records and credentials are not exported by
that command. Parent transport bounds and discarded stderr remain required.

Topic support requires a separately reviewed exact-question content witness,
bound to the original record hash and derived-body hash. It is not inferred from
keywords, list membership or title similarity. No real topical approval was
generated here. The current verifier intentionally accepts only the frozen
archive-only deterministic narrative and refuses nonzero-market/current-price
claims. That is a restricted probe acceptance profile, not removal of normal
market/news/model capabilities or proof the broader explanation service works.

The current last-inspected images are known to predate the strict probe repair.
They cannot be declared compatible just because this adapter exists locally.
Actual installed CLI/SDK/source/configuration parity, binary availability,
symlink layout, namespace existence, persistence, timing and cancellation are
UNVERIFIED. Unsupported binary/layout/configuration cases fail closed. Timeout
is not proof a Docker/server-side operation never happened or was cancelled.

Two assumptions only: the eventual manifest/witnesses are independently reviewed
and trusted, not self-approved from runtime output; exclusive operator control
of the pinned targets holds during an authorized attempt. Detected changes or
ownership ambiguity remain failures, never permission to stop unrelated work.

## Proof and independent review

VERIFIED_ENV: Python3.12.10 and synthetic local fixtures. UNKNOWN_ENV for actual
Docker/SDK/storage execution: none was attempted. Tests create disposable fixture
files, pipes and short-lived local subprocesses only; no Docker, service/network,
private account or real credential access.

Initial new-component slice:237 passed in2.68s. First independent reviews rejected
the policy-hash-only gate, missing local-volume-driver requirement, and unsupported
claims inside nested raw-response fields. Those findings are retained, not
relabelled as passing proof. Bounded corrections, final test totals, source hashes
and independent re-review dispositions are recorded in the completion addendum.
No full-suite, real-stack or profitability result is claimed.

## Operational boundary

This implementation does not authorize deployment/rebuild/recreation, config or
credential changes, startup, migrations, ingestion, accounts or trading. The next
operational preparation needs separate authorization: identify compatible existing
images/SDKs/configuration, obtain independently reviewed installed-policy pins and
topic witnesses, and resolve any installation/reconnection changes before proposing
one instrumented retry. Do not use synthetic review records from tests as that
manifest, or invoke the isolated-stack verifier as a substitute.

## Completion addendum

The source implementation is complete for this bounded adapter scope, not for
service restoration. The prior core is now wired to a concrete Backend in two
synthetic scenarios: one permitted explanation and a risk-health refusal with
no explanation and reverse cleanup. Those tests use fake external state and
in-process calls, not Docker or a real dashboard HTTP submission.

The evidence-helper correction rejects unknown nested fields and contradictory
query-audit text, validates known diagnostic structures, and adds a total8s
remote timer. It preserves real empty-market/metadata-builder/assembler
compatibility in AST-only tests. Causal acceptance remains explicitly restricted
to the fixed archive-only narrative, not arbitrary prose plus a disclaimer.

Final frozen-source command:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q \
  -p no:cacheprovider tests/test_companion_runtime_adapter.py \
  tests/test_companion_docker_transport.py tests/test_companion_evidence_checks.py \
  tests/test_companion_runtime_wiring.py tests/test_companion_existing_controller.py \
  tests/test_companion_probe_policy.py tests/test_explain_diagnostics.py \
  tests/test_explain_asset_guard.py tests/test_dashboard_companion_http.py \
  -k 'not environment_proxy_never_receives_companion_bearer'
```

SHOWN:467 passed,1 deselected,126 startup deprecation warnings in14.53s. The
deselected case opens a loopback listener; this stage remains synthetic-only.
No full suite was run. Seven new-file hashes and the generated evidence-script
hash are recorded in
`docs/review_artifacts/companion_runtime_adapter_20261016_sha256.json`.

Separate adapter/transport AUDITOR accepted the bounded fixes after independently
running154 tests, checking changed/unbound record refusal, local-driver checks,
and a5.002s stalled-stream/timer restoration probe. It explicitly retained the
external manifest/reviewer trust assumption and unknown installed/runtime state.
Final helper and supplemental wiring dispositions follow below; no source has
changed since the frozen combined run.

Final independent dispositions:
- Evidence AUDITOR: ACCEPTED the frozen nested-envelope correction and offline
  timer implementation, independently150 passed in9.73s with the supplied source/
  SCRIPT hashes confirmed. It verified timer coverage through DB teardown,
  occupied-timer refusal and sanitized stalled-input termination. Actual DB/SDK
  signal responsiveness remains UNVERIFIED and parent transport caps required.
- Adapter AUDITOR: ACCEPTED the additional synthetic wiring coverage,2 passed
  independently; no claim of real Docker/process isolation/evidence-script proof
  from that in-process harness.

No reviewed source changed after final independent review. Hash-manifest
validation checked all seven new files and generated SCRIPT bytes, zero
mismatches. `git diff --check` passed. Nothing committed, pushed or deployed.
Implementation handoff: READY_FOR_INDEPENDENT_REVIEW with separate scoped
acceptances recorded; service restoration remains INCOMPLETE. No runtime retry
authorization was granted or inferred.

## Authorized read-only installed refresh, 21:26 UTC

Active role AUDITOR. SHOWN: all seven target IDs, images, exited states, restart
counts and policies still match the earlier inventory; the final inventory
matches the initial one. Five allowlisted installed source files match their
earlier hashes. Four differ from the repaired current local source: tools.py,
audit.py, orchestrator/main.py and memory_retrieval/main.py. retry.py still matches.
The existing installed source therefore still lacks the reviewed local changes;
an unchanged-stack retry would not exercise those repairs.

Receipt: `docs/review_artifacts/companion_compatibility_refresh_20261016.json`.
VERIFIED_ENV for this selected metadata/archive inspection only; installed SDK,
effective configuration, namespaces and actual explanation remain UNVERIFIED.
The successful collection took3.13s; that is not total task duration. An initial
metadata-template error was corrected, not represented as a service failure.
No services started/stopped, no exec/build, credentials, environment export,
service query, deployment or broad tests. No reviewed implementation changed.

Next recommendation: prepare a minimal installation/reconnection and rollback
plan for the repaired application sources, explicitly preserving the existing
data volumes and normal research capabilities. Installation may require changing
the existing no-build/no-recreation boundary; do not assume that permission.
No installation command is approved by this read-only check. Runtime INCOMPLETE;
retry authorization NOT GRANTED. No new experiment or framework is needed.

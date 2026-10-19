# Companion offline controller and compatibility repair

Date: 2026-10-16. Active role: ENGINEER. Risk: HIGH.
Implementation state: READY_FOR_INDEPENDENT_REVIEW.
Operational objective: INCOMPLETE. Runtime authorization: NOT GRANTED.

## Scope and explicit limit

This is an offline implementation, not a service restoration. Previous operation,
diagnostic, guard and installed-source audit artifacts remain historical. No
container command, service request, credential retrieval, deployment, image
change, migration, ingestion, scheduler/account/campaign or trading action is
part of this stage. Tests use synthetic services, tokens and state.

The controller enforcement core is implemented in
`scripts/research/companion_existing_controller.py`. It deliberately has no CLI,
credential reader or Docker adapter. Its Backend interface specifies real checks
which a future separately reviewed adapter must perform. Synthetic booleans in
tests are fixtures, not evidence of installed compatibility, namespace existence,
source traceability or semantic relevance. Do not call this a complete operational
controller or run the isolated-stack verifier in its place.

## Implemented components

- Fixed seven-target state machine, stopped-target baseline/recheck, exact IDs,
  preservation digests, start ledger, observed StartedAt ownership, storage
  checks before application startup, one explanation, and conditional retention.
- Verification deadline at420s and final deadline at600s, operation caps, fixed
  settling periods, no polling/retries, and ownership-limited reverse cleanup.
  A timed-out start is ambiguous, not proof it did nothing or belongs to us.
- POSIX disposable-process executor, private bounded result channel, suppressed
  child stdout/stderr, no raw exception text, and explicit single-thread parent
  requirement. It is a local mechanism, not proof Docker/server cancellation works.
- Exclusive0600 append-only receipts with allowlisted phase/diagnostic fields.
  Raw prose, URLs and token values are not persisted in these receipts.
- Opt-in dashboard probe context suppresses legacy primary dispatch, supplies an
  in-memory token to the existing companion transport, adds the versioned strict
  probe header, caps response size/timeout and spends its one request budget on
  failure as well as success. Ordinary dashboard behavior remains the default.
- Real dashboard normalizer and asset guard remain in the probe path. Acceptance
  examines the raw response separately so synthesized provider defaults cannot
  pass. Positive integer document IDs are hashed canonically, excluding booleans.
- Persisted citation identity, approved-view mapping, content hashes, topical
  support and causal limits remain separate required adapter checks. Keywords
  and a passing transport do not supply those checks.

Service compatibility source changes:
- `shared/probe.py` introduces a versioned request-local profile. Unknown or
  duplicate profile headers are rejected; auth remains required at each route.
- `shared/tools.py` restricts strict-profile internal HTTP origins and removes
  its retry. The strict explanation obtains actual memory and risk responses,
  not the ordinary tools' unavailable/fallback payloads.
- `orchestrator/main.py` routes only opt-in probes through that restricted tool
  set, retaining the existing response assembler. It does not call the model or
  market/parser/news/archive services for this profile. Normal mode is retained.
- `shared/audit.py` propagates the marker with explicit strict HTTP options;
  audit remains best-effort and persistence writes are still possible.
- Memory's new `memory_read_only_startup` setting defaults false. When enabled,
  missing namespaces cause startup failure rather than creation, ingestion is
  refused, and health reports the mode. Restricted storage clients request SDK
  retry/proxy constraints; actual installed SDK behavior remains UNVERIFIED.
- Middleware is installed on orchestrator, memory, risk and audit. It is not a
  network sandbox, Docker identity proof or alternate authorization mechanism.

These source files are gitignored in this checkout (confirmed with
`git check-ignore`). They therefore require explicit packaging review; an
ordinary tracked-files diff or commit would omit them. No ignore rule, image,
deployment or existing configuration was changed to hide that limitation.
Source changes are not installed-image changes.

## Proof so far

VERIFIED_ENV: repository Python3.12.10; synthetic local tests, no Docker/network
service or real credential required.

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_companion_existing_controller.py \
  tests/test_explain_diagnostics.py tests/test_explain_asset_guard.py \
  tests/test_dashboard_companion_http.py \
  -k 'not environment_proxy_never_receives_companion_bearer'
```

Initial result:86 passed,1 deselected. The deselected test opens a loopback
listener and is outside this synthetic-only run. This is not a full-suite run.
`git diff --check` passed. Independent review is pending; these are implementation
checks, not same-thread approval of high-risk work.

Separately reproduced the service worker's43 synthetic tests:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q \
  -p no:cacheprovider tests/test_companion_probe_policy.py
```

Result:43 passed,86 FastAPI startup-event deprecation warnings. The fixture
bypasses Settings environment/dotenv initialization, injects synthetic storage,
uses in-process ASGI/HTTP mock transports and forbids socket connects/DNS. It
does not run application lifespan against real namespaces or certify SDKs.
Deprecation cleanup is deliberately outside this repair.

## What still requires proof

1. Independent source review of the frozen implementation and any corrections.
2. A concrete reviewed runtime adapter: pinned CLI/daemon/container/image/source
   and effective-setting checks, actual namespace and service health checks,
   secure existing-token handoff, parameterized read-only citation verification
   and independent topical-support assessment. No arbitrary boolean checklist
   or claimed hash may substitute for those checks.
3. Separately authorized installation/reconnection, current preflight and one
   instrumented query. Existing installed images still contain the behaviors
   shown in the prior audit; local patches do not repair them in place.

Assumption1: opt-in probe behavior is an additional restricted mode, not a
replacement for the existing intelligence capability. Assumption2: a future
adapter operates under exclusive operator control of these targets; its local
ledger cannot prevent unrelated direct Docker actions. Detected ambiguity must
remain a failed/cleanup-unverified attempt.

The cause of the earlier failed runtime query remains UNRESOLVED. WP4 item1 and
accepted research artifacts are not reopened. No profitability or readiness
claim follows from this implementation.

## Independent first-pass findings and bounded corrections

Two separate AUDITOR agents reviewed the controller/dashboard and service slices.
Both returned INCOMPLETE on the first version, with these SHOWN source defects:

1. Receipt write/flush/fsync was outside the process cap; a delayed receipt
   could consume the budget after `_call` calculated its timeout.
2. Parent-side pickle reconstruction could execute slow arbitrary reconstruction
   code outside the child's cap, despite a bounded private pipe frame.
3. Raw risk gate alone did not reject contradictory LIVE/allow-trading values.
4. A final receipt write failure could leave a successful terminal record even
   though the controller rolled back and returned INCOMPLETE.
5. Socket timeout did not cover the complete HTTP read/decode wall time.
6. Restricted SDK constructors accepted unapproved configured storage endpoints.

Controller/dashboard corrections: receipt I/O is child-bounded and the operation
budget is recalculated afterward; the wire format is bounded JSON, not arbitrary
Python reconstruction; all three raw risk fields are required exactly; successful
terminal records are never written. `checks_passed_pending_return` is explicitly
provisional and is NOT proof the services were retained. A subsequent error may
leave that provisional record and trigger cleanup; an unreadable/incomplete
receipt must never be interpreted as success. Error receipts are best-effort if
the filesystem is unavailable. HTTP open/read/decode stays inside the existing
outer dashboard child, with an additional POSIX signal wall timer. It requires
the child/main-thread context, refuses an occupied timer and restores the prior
handler. Nested executors are refused; no HTTP child may create a detached
session and escape an outer deadline.

New tests exercise real synthetic slow fsync, delayed receipt dispatch, rejected
custom result reconstruction, contradictory/missing risk fields, failed success
receipt and slow HTTP consumption. They do not prove hard real-time guarantees
under arbitrary operating-system failure, daemon cancellation or deployment.

Only these demonstrated issues are being corrected in this pass. Final focused
test totals, storage-origin correction and bounded independent re-review are
recorded in the handoff addendum; no full-suite or real-stack run is implied.

## Final focused verification and source freeze

Re-review found one additional demonstrated ownership defect in the first HTTP
timer correction: an inner executor created a detached session and could survive
the outer timeout. Removed that nested child and added a shorter-outer-deadline
regression that verifies the HTTP owner's PID is gone after the outer executor
returns. The inner HTTP timer now runs in the same disposable query child.

Storage correction: strict Qdrant/MinIO paths validate service-specific exact
endpoints before SDK construction AND cached-client return. Both probe requests
and read-only startup are covered; ordinary mode is unchanged. Only
`http://qdrant:6333` and `http://minio:9000` (optional trailing slash) are accepted.
This is source-level endpoint validation, not proof of DNS/container identity or
the installed SDK's retry/redirect implementation.

Final command on frozen code:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q \
  -p no:cacheprovider tests/test_companion_existing_controller.py \
  tests/test_companion_probe_policy.py tests/test_explain_diagnostics.py \
  tests/test_explain_asset_guard.py tests/test_dashboard_companion_http.py \
  -k 'not environment_proxy_never_receives_companion_bearer'
```

SHOWN:161 passed,1 deselected,126 FastAPI startup deprecation warnings in3.40s.
No full-suite run. Source hashes are recorded in
`docs/review_artifacts/companion_offline_controller_20261016_sha256.json`.
That manifest identifies current source bytes, not an incremental patch against
the already-dirty starting tree, nor installed image parity. `git diff --check`
passed. No code is committed/pushed/deployed by this handoff.

Final independent source-review dispositions:
- Controller/dashboard AUDITOR: ACCEPTED_WITH_RISK for the bounded offline
  implementation;98 passed,1 deselected independently. It verified the frozen
  controller/HTTP/test hashes and found no remaining demonstrated blocker in
  that scope. POSIX/fork, single-thread and controlled SIGALRM limits remain.
- Service AUDITOR: ACCEPTED for the bounded storage-endpoint correction;
  63 passed,126 deprecation warnings independently. It checked the exact frozen
  source hashes. That closes configured-endpoint validation, not SDK behavior,
  full ordinary/model-path integration or installed recipient identity.

The parent independently ran the combined161-test slice; neither auditor claimed
to rerun that entire combined command. No source changed after these reviews.
Implementation handoff remains READY_FOR_INDEPENDENT_REVIEW with separate scoped
source acceptance recorded above. Runtime remains INCOMPLETE and unauthorized;
the Backend contract and synthetic checks do not replace the missing real
runtime adapter or its independent evidence.

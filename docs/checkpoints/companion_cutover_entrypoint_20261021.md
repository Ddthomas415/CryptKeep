# One-Shot Staged Cutover Command

Date: 2026-10-21. Active role: ENGINEER. Risk: HIGH.
Implementation: READY_FOR_INDEPENDENT_REVIEW. Actual runtime: INCOMPLETE.

## Implemented Scope

`scripts/research/companion_cutover.py` wraps the accepted staged API without
changing it. Default behavior validates public reviewed inputs only: no token
read, native backend, Docker command, lock, reservation or startup. An explicit
`--execute-cutover` flag selects operations but does not substitute for separate
operator authority. No operation was executed during this implementation.

Required inputs reuse existing schemas:

- Reviewed v5 manifest and its independently trusted hash.
- Preparation evidence, actual-ID review and independently trusted review hash.
- Public staged metadata whose complete selected Snapshot values must reproduce
  the exact four reviewed stopped records, not a new inventory-to-approval path.
- Runtime review and independently trusted hash (`companion-runtime-pins-v1`).
- Existing per-image dependency-policy reviews and topical approvals, whose
  bytes/subjects/hashes must match that runtime review.

Storage runtime pins must equal the original three IDs/images/preservation hashes.
Application pins must use reviewed prepared IDs/images, frozen application-source
hashes and the exact modeled pre-start raw preservation hash. The latter retains
the native blank raw network ID while configured projection must separately match
the manifest. Raw/configured hashes are not interchangeable. Only planned logical
aliases are modeled; current command supports the packet's alias-only options.
No generic metadata normalization or gate waiver was introduced.

SDK/source coverage, no-retry/no-proxy/entrypoint policy records and a topical
witness are mandatory even for inert validation. Tests use clearly synthetic
records in temporary files; they are not native policy or runtime approvals.

## Execution Boundary After Separate Authorization

Execution takes the existing shared install lock and exclusively reserves
`.cbp_state/runtime/companion_cutovers/<prepared-attempt>/`. The marker is durable
across commands, manifest changes, failures and receipt renames. This is a
separate phase from preparation; it cannot rebuild or create replacement IDs.
Descriptor-relative traversal, ownership/mode/no-follow checks and parent fsync
precede token/native work. Directories0700; receipt/provisional result0600 and
exclusive. Do not delete the marker to retry.

The existing service token must arrive on an owned anonymous pipe/socket FD>2;
there is no argument, environment or file-value fallback. It is consumed once
with a2second bound, closed and retained only in runtime memory. The transport
uses an empty private Docker config, not the user's default credential config.
Runtime close and temporary-config cleanup run on exit; this is not a claim of
memory zeroization. Default validation refuses a token FD without reading/closing it.

The accepted controller owns600seconds total, reserving180 for recovery. Input,
lock, reservation, receipt binding and token/config setup occur before that clock;
no total CLI wall-time guarantee is claimed for local filesystem I/O. The command
records the four trusted input hashes before token or native work.

The staged controller freshly checks originals, reviewed replacement identities,
sources, policies and storage namespaces before interruption. It retains existing
owned-only recovery, pre-start configured checks, post-start actual-recipient
checks, health, one query, sanitized diagnostics before assertions/cleanup, and
persistent citation verification. It never builds, recreates or starts storage.
If every check and final receipt commit passes, replacement applications remain
running; the original applications remain preserved under rollback names, not
deleted. Failure may remove owned replacements while restoring original running
configuration. That consumes the prepared set rather than silently recreating IDs.
Startup/request logs and audit writes may persist even after rollback; this is
not a transactional rollback of storage contents. No application/database data
preservation claim follows from restoring container metadata and running state.

After successful controller return, a sanitized provisional result is published
inside remaining work time and committed to the receipt. Success is provisional
without that final receipt commitment. Publication/commit failure attempts the
existing rollback inside recovery time; the failed artifact is preserved rather
than treated as accepted. SIGINT/SIGTERM request one failure; repeated signals
do not interrupt recovery. SIGKILL, host failure and daemon-side unknown outcomes
are not solved by these handlers. Failed/unknown recovery remains INCOMPLETE.

## Verification

VERIFIED_ENV for local synthetic tests only. Combined command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tests/test_companion_cutover_entrypoint.py tests/test_companion_cutover_inputs.py \
  tests/test_companion_staged_update.py tests/test_companion_staged_composition.py \
  tests/test_companion_prepare_entrypoint.py tests/test_companion_runtime_adapter.py
```

SHOWN:240passed in3.06seconds, exit0. Includes58new cases. Entry-point tests use
the real staged Installer.run/recovery API over a synthetic backend, not a canned
success return. Input tests independently use real loaders/policy validators and
public saved observations with temporary synthetic approval records. Native and
network calls are forbidden. Runtime close, private-config cleanup, deadlines,
publication failures, signals and durable replay refusal are covered. No full
suite/backtest ran. Module help exits0.

Frozen SHA256:

| File | SHA256 |
| --- | --- |
| companion_cutover.py | 3f33b2b2e9f9f88eb302db0fe19f3b95b6eb960ede69e76619299a8dd69cc3a0 |
| test_companion_cutover_inputs.py | 69522fff1a44d2c3e2b633c95e4bba1bd136102bd3fe553bd1066ab21c79d6bb |
| test_companion_cutover_entrypoint.py | ef5007612301aaa55c6bf66a8f413d8ea5bb34811a253d60d604ed0cbb00b9b4 |

## Remaining Native Evidence

The reconciled preparation artifacts do not supply an accepted runtime-pin,
dependency-policy and topical-witness packet for this command. Historical SDK,
entrypoint and source evidence exists, but its suitability for the prepared
image subjects remains UNVERIFIED here. No approval is fabricated from it.

A default invocation using deliberately unissued runtime-review paths returned
exit1, phase=input_validation, actions_executed=false, attempt_reserved=false,
receipt=null. This verifies refusal, not a usable native runtime packet. No token
or Docker/native operation ran. Separate review of this command is pending.
After acceptance, reconcile existing installed-policy evidence and identify exact
remaining evidence gaps before requesting bounded execution. Prepared containers
and all previous evidence remain untouched; startup/cutover are not authorized.

## R1 Review and Bounded Corrections

Separate GATE R1: REJECTED despite240passing tests. Receipt:
`docs/review_artifacts/companion_continuation_20261021/cutover_entrypoint_review_r1.json`.
P1: first cancellation entering publication-failure handling could escape before
recovery began, leaving synthetic replacements running/originals exited. P2:
cancellation during partial initialization could access absent runner fields and
escape without a sanitized summary. Both were shown in offline reviewer probes;
no actual container or OS-service signal was involved.

R2 defers cancellation when an exception is already active, not only once the
runner reports recovery. Deferred cancellation is checked after controller return
before publication. Recovery/initialization guards use getattr defaults for fields
that may not yet exist. No deadline reset, extra attempt, core API change or native
operation was added. Four new deterministic trace-injection regressions cover both
boundaries for SIGINT and SIGTERM, requiring one recovery after effects and no
recovery before effects, with sanitized output and original state restored.

Corrected same six-file command:244passed in3.16seconds, exit0; diff-check clean.
Corrected source SHA256: `fcea6d3e181372e3db02882f70392f38a985067081a42c5c3e2a8bfd34a3a550`.
Corrected wrapper tests SHA256: `71801c52c85e4580f52a120197af009223ddf53b59bde2c14b7fd532f4edc31a`.
Input-test hash remains unchanged. R1 proof is preserved, not called acceptance.
Corrected implementation READY_FOR_INDEPENDENT_REVIEW; bounded re-review pending.

## Final Bounded Re-Review

Separate GATE ACCEPTED_WITH_RISK for R2 closure. Both R1 findings closed;
independent62tests passed in1.11seconds and exact initialization/recovery-handoff
probes passed for SIGINT and SIGTERM. Partial initialization fails with sanitized
output/no effects, and post-effects publication failure rolls back once/restores
originals. Frozen hashes match; R1 receipt remains preserved. Reviewer made no
source/test change or native call. Receipt:
`docs/review_artifacts/companion_continuation_20261021/cutover_entrypoint_review_r2.json`.
Parent checked whitespace in all three new untracked files directly with awk,
not just git diff, and rechecked the frozen hashes; all match and whitespace
check exit0. The244-test parent result remains the wider targeted slice.

This supersedes pending review for the offline command only. No accepted native
runtime-policy/topical packet, live cutover, SDK/endpoint success, storage-data
preservation or cited explanation is inferred. The command will not manufacture
those inputs. Next is evidence reconciliation against the actual prepared IDs
and installed-image policy records before proposing a separately authorized
execution. No build, preparation rerun, token or native service operation ran.

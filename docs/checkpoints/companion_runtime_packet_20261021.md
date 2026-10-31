# Restricted Runtime Evidence Packet

## Objective and Authority

Active stage: ENGINEER, offline packet assembly. Risk HIGH because the packet
feeds operational compatibility gates. No native operation, credential access,
start, stop, cutover, query, build or scheduler change is authorized by this work.
Original artifacts, stopped replacements and consumed attempt remain preserved.

Reuse the accepted preparation and actual-ID disposition from
`companion_s3_preparation_result_20261021.md`; do not prepare another set.

## Changed Artifacts

`docs/review_artifacts/companion_continuation_20261021/assemble_runtime_packet.py`
derives four packet artifacts from seven frozen evidence/review inputs. It
rehashes all 93 saved installed files, verifies the separately captured new memory
main, uses the existing preparation loader, and compares all four staged snapshot
models before deriving final alias-only preservation pins. It creates no policy
approval. The candidate is not a runtime-review record accepted by the CLI.

Output folder: `docs/review_artifacts/companion_continuation_20261021/runtime_packet/`.

| Artifact | SHA256 |
| --- | --- |
| staged_metadata.derived.json | 98c186a31d78686bf7702eb46685c87a2d6487a680cad0e702a35244c7eed118 |
| subjects.draft.json | 6215685a6dcd6fc35e3acf87fbb595acf995758ff4013c3c551919692a2c72e6 |
| topical_approvals.json | f4de03c65058769eb434e5931065deaeb5795087983a92a3b2f54dacd8feff45 |
| provenance.json | 3d14445432cffec436e9b94b0e767b5e83041100d4ee1a937792f76d990ebd69 |

## Verification

VERIFIED_ENV for local offline reads and derivation only. `python -B` import of
the assembler's `derive()` reproduced all four saved artifacts byte-for-byte.
Existing adapter source-coverage and topical-contract checks passed for seven
ordered subjects. Four patched-in-memory input mutations were refused by the
frozen-input hash check. No production code changed, full suite not run, no
Docker/network/service command invoked. These are packet checks, not seven
operational passes or a completed explanation request.

## Evidence Boundaries

- SHOWN: exact selected IDs, image identities, saved metadata and source bytes
  reproduce the accepted evidence. Raw stopped network IDs stay blank; only
  aliases are modeled. Configuration is not a connected endpoint observation.
- SHOWN: new memory main was separately captured from the new ID. All 43 app
  source checks remain preparation-controller attestations. Earlier SDK captures
  and identical non-memory images are reused, not described as newly captured.
- Inference: new memory SDK files are inherited unchanged by the source-only
  COPY build. Fresh installed-source checks remain mandatory before activation.
- Attempt labels in derived metadata come from accepted preparation evidence,
  not from the separate postcheck, which did not capture that field.
- Policy assessment is restricted to the reviewed single-query profile and
  disclosed startup behavior, not unrestricted image behavior or a claim that
  startup has no effects. Read-only startup can open sockets and emit logs;
  the eventual query can append approved audit events.
- The existing bounded query uses deterministic probe/fallback reasoning over
  retrieved evidence. Passing it would not establish general model-backed
  explanation readiness, current-market causation or profitability.

## Handoff

Independent reviewers assess policy semantics and exact subject bindings.
Do not manufacture `SHOWN` policy records to satisfy the loader. Complete the
existing runtime manifest only from accepted, exact-image independent records.
Then run its inert input validation, without `--execute-cutover` or a token.
Operational authorization remains separate. Initial handoff state:
READY_FOR_INDEPENDENT_REVIEW; runtime/explanation objective INCOMPLETE.

## Independent Disposition

Separate GATE ACCEPTED_WITH_RISK the exact assembler and four draft artifacts.
See `runtime_packet/independent_review.json` for the source-bound assessment.
Reviewer independently reproduced the derivation, all 93 captured file hashes
and sizes, seven subjects, 43 app-source bindings and alias-only models. No
actionable draft defect was found; no native operation or test-suite repeat.

The full runtime-policy packet remains INCOMPLETE for these specific reasons:

1. Captured HTTPcore implementation is synchronous; the guarded audit/tools
   HTTPX clients use its asynchronous pool/connection implementation, not yet
   captured. Configuring retries=0 is shown; its invoked implementation is not.
2. Captured Uvicorn launcher invokes installed main/config/import-loader files
   absent from the capture. Authored application startup effects are reviewed,
   but this invoked loader chain is not yet characterized from installed bytes.
3. Captured psycopg connection delegates connection-attempt selection to an
   uncaptured helper. One SQL call is not proof of one underlying connection
   attempt. Storage services remain running and are not cutover start targets;
   no daemon-wide no-retry or no-side-effect claim is needed or made.

A bounded search of saved review JSON/Python artifacts found no prior captures
of these named missing paths. This is not a machine-wide absence claim.
Runtime transport currently excludes Uvicorn package paths; retain that boundary
rather than bypassing it or silently widening the allowlist. No retry or source
comparison criterion has been relaxed to make the packet pass.

Next affected action requires a separately scoped, read-only capture of missing
installed code and its exact-image review, plus only any demonstrated source-pin
compatibility change. It does not require another build, restaging, SDK execution,
container startup, database query or credential access. No capture performed.

Draft derivation objective ACCEPTED_WITH_RISK. Per-image policy records and final
runtime manifest are deliberately absent; cutover input validation has NOT been
claimed to pass. Runtime and genuine cited-query objective remain INCOMPLETE.

Memory reviewer confirmed no policy files were written. Minimal proposed source
selection, beneath `/usr/local/lib/python3.11/site-packages/`, is:

```text
httpcore/_async/connection_pool.py
httpcore/_async/connection.py
uvicorn/main.py
uvicorn/config.py
uvicorn/importer.py
uvicorn/server.py
uvicorn/lifespan/on.py
psycopg/conninfo.py
```

The captured Psycopg version imports the helper from `conninfo.py`; an assumed
`_conninfo_attempts.py` filename would be wrong for this capture. Uvicorn
server/lifespan cover startup dispatch beyond import loading, not every import.
Read from applicable exact image subjects, preserving inheritance distinctions.
Do not claim this list proves full import closure or extend it without showing
an actual relevant delegation. Capture remains unperformed and unauthorized.

## October 21 Evening Follow-Up (Supersedes Unperformed Capture Status)

Operator continuation authorized the requested read-only source inspection.
VERIFIED_ENV: exact pinned Docker CLI and local socket, engine29.9.1 observed.
The first sandboxed metadata read was refused before any file copy; its separate
`missing_runtime_sources/report.json` is preserved INCOMPLETE. Refused alone does
not establish the precise reason. The explicit permission-reviewed engine check
and second capture succeeded; no blind same-output retry or deletion occurred.

`capture_missing_runtime_sources.py` is an explicit, inert-by-default capture
artifact, not a production transport bypass or another running collector.
Permission-reviewed invocation:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
 -m docs.review_artifacts.companion_continuation_20261021.capture_missing_runtime_sources \
 --execute-capture --output missing_runtime_sources_authorized
```

SHOWN: saved32 files cover exactly8paths x4 accepted stopped IDs. Before and
after selected identity/image/state/start-time/restart/policy rows match; all4
remain created/never-started/restarts0. Each corresponding file matches across
all4 images. Reported34commands,1.83seconds,409488transfer bytes; receipt SHA256
7e0445af269135ea252e69da471098e884d71cb967ce261761f7c9c37cb44363.
Separate GATE ACCEPTED_WITH_RISK capture integrity only in
`missing_runtime_sources_authorized/capture_review.json`. No semantics or
startup acceptance follows from source-copy integrity. The120second command
budget is not a universal local-I/O/report-write/cleanup wall-clock guarantee.

The captured `psycopg/conninfo.py` actually reexports `_conninfo_attempts.py` and
`_conninfo_utils.py`. This corrects the earlier filename expectation; `conninfo.py`
alone does not contain the implementation. Per the demonstrated-delegation rule,
a separately permission-reviewed read copied those2helpers x4same IDs into
`missing_psycopg_attempt_sources/`:10commands,0.544seconds, stable selected rows.
Receipt SHA256d68eb1714c13b5379ad0904f46b83c800fa668530dd497945f17100854cc77fd.
The wrapper narrowed the capture's explicit PATHS tuple to those2 named helpers;
no source execution, environment read, SQL or lifecycle action was performed.

## Concrete Source Findings and Targeted Proof

- SHOWN: HTTPcore async pool passes configured retries to its connection. The
  captured `_connect` raises the original connect failure immediately when
  retries_left=0. Pool reassignment on ConnectionNotAvailable is a separate
  path; this is not an unconditional whole-pool no-repeat claim.
- SHOWN: Psycopg's resolver expands a hostname to all returned addresses; its
  captured connection code iterates attempts. One SQL call does not imply one
  underlying connection attempt. The synthetic two-address case produces2;
  explicit hostaddr produces1 without a DNS call. Actual DNS output is UNVERIFIED.
- SHOWN: Uvicorn's ordinary single-worker server path imports the configured app
  and dispatches lifespan startup before opening listeners. Reload/multiprocess
  supervisors can bind a socket earlier; this order is not universal. Lifespan
  auto can treat an unsupported/erroring lifespan as unsupported, not always
  fail closed. Config can use WEB_CONCURRENCY and its CLI accepts
  UVICORN environment defaults. Effective presence/values were not inspected;
  these files alone do not establish one worker or an entire startup closure.

New offline captured-method tests extract selected functions with AST rather
than import installed modules or initialize SDKs. Network, sleep and trace
dependencies are synthetic. This is executable method proof, not native SDK proof.

## Minimal Source-Pin Compatibility Change

ENGINEER / HIGH: production transport `_FILES` now includes only the5 captured
Uvicorn Python paths. No wildcard SDK expansion, command, authorization, startup,
timeout or recipient behavior changed. Reconstructing the previous `_FILES`
block reproduces accepted transport SHA98e94faa02c87c38c2b1379bb5d909791d0077a994e7dba3d59b6a5d7bd96d17,
proving this turn's delta against the already-dirty prior baseline. New SHA:
817c378c289093a7f7c5395f3eb28291e5af1c3a7ae8b09eed2bde5868d2ecc5.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
 tests/test_companion_uvicorn_source_pins.py tests/test_companion_docker_transport.py \
 tests/test_companion_captured_transport_paths.py
```

Result:134passed1.45seconds. New path tests include exact5allowed and7rejected
nearby/traversal/secret/compiled paths. Captured-method probes:5passed0.30seconds
in the prior narrow run, included in134, not an additional139 total. Full suite
not run. No code was tested against live SDK initialization or an endpoint.

Offline `augment_runtime_sources.py` preserved the accepted original draft and
adds40directly captured source hashes to a separate128-entry candidate:

| Artifact | SHA256 |
| --- | --- |
| runtime_packet/subjects.sources_v2.draft.json | b99ccc38ce8942bd2bdfd601f30d3d734d1a7c1fed3037870199151a6fc673bc |
| runtime_packet/source_augmentation.json | 74f70d84b5cf7a62ebb2f19b496ec050d53091fab3ebf29b7d63f307f3843c10 |

IDs, images, preservation hashes and historical topical witness unchanged.
No accepted policy or runtime manifest was generated. Sent frozen compatibility
delta, tests, source findings and augmented candidate to separate GATE.
Compatibility implementation READY_FOR_INDEPENDENT_REVIEW. Runtime-policy
packet and actual cited-query objective remain INCOMPLETE; no startup/cutover
authorization is inferred. No containers built, started, stopped or recreated;
no credentials, accounts, trading, scheduler or database query touched.

## Final Independent Review of This Follow-Up

Separate GATE ACCEPTED_WITH_RISK the exact five-path compatibility delta and
deterministic augmentation. Parent read both complete review records:

- `missing_runtime_sources_authorized/compatibility_review.json`: previous
  transport reconstructed exactly; AST unchanged outside `_FILES`; all old88pins
  preserved,40added,128total; seven subjects/preservation identities unchanged.
- `missing_runtime_sources_authorized/source_policy_assessment.json`: supplemental
  capture integrity accepted; narrow source findings accepted with risk, not
  blanket runtime policy approval. Parent's134-test execution was not repeated.

The first capture/read objective and offline compatibility component are closed
ACCEPTED_WITH_RISK. No additional source dump or general SDK audit is queued.
The next boundary is a narrowly sanitized effective startup-profile check
(relevant option presence/matches, not raw credentials) and a scoped policy
disposition. Zero HTTPcore connect retries must not be generalized to no pool
reassignment or one physical connection, and one SQL call must not be generalized
to one address attempt. No such traffic duplication was observed. No seven-subject
policy records, accepted runtime manifest, service restoration or actual cited
explanation result exist from this work. Runtime remains INCOMPLETE; no operational
cutover or query approval is created by either independent acceptance.

## Sanitized Startup Profile Follow-Up

AUDITOR objective: bind the effective options previously left UNVERIFIED without
exporting environment values or starting services. Operator continuation plus
explicit tool permission covered8read-only selected-container inspections.
VERIFIED_ENV: pinned native CLI and local endpoint; empty temporary Docker config
and PATH-only child environment. No exec, SDK initialization, credentials or SQL.

Saved observation:2026-10-22T01:44:48Z (October21,21:44EDT). Receipt reports8commands
and0.404seconds; all4ID/image/state/start/restart/policy fields match before/after,
and the selected subjects remain created/never-started. Fixed comparisons show:
expected command/module/port, empty entrypoint, /app working directory, known PATH;
no UVICORN_* overrides, WEB_CONCURRENCY, FORWARDED_ALLOW_IPS, BASH_ENV or ENV.
Orchestrator has the expected repository PYTHONPATH; other3 have no PYTHONPATH.

The initial diagnostic incorrectly required that repository import path for all4
apps, so the preserved receipt says profile_matches=false. This was a diagnostic
false positive, not a new container defect. Captured Uvicorn main.py:343-347,513-514
shows CLI app-dir defaults to the current directory; /app supports the other3.
Preserved the executed v1script and raw receipt; corrected only offline assessment
and added regression coverage. No runtime criterion or container was changed.

Artifacts under `startup_profile/`:
- report.json SHA3c49e4246f5b69864f3b3aedae8562dcb857926995f78591452de2af3836f3d9.
- capture_startup_profile_v1.executed.py SHA5b514d8b35359c8b8c5d1687b0bd588dd2ac7fd76ba8e2ae85a04742d0c711f3.
- assessment_v2.json SHA8fe928ab2fdccb96d7e5b93f5942730d0bfc9f20ac656af912ce70944388a31c;
  all4corrected profile checks pass. This is configuration evidence, not startup.

VERIFIED_ENV targeted command:
`env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_startup_profile.py`
Result15passed0.19seconds. Earlier14case run preceded the diagnostic correction;
do not sum them as29different tests. No production code changed or full suite run.

Frozen script/test/assessment sent to independent GATE. No source capture repeat,
rebuild, restaging, approved seven-subject policy manifest or runtime attempt.
Profile acceptance and remaining policy scope await that review. Handoff
READY_FOR_INDEPENDENT_REVIEW; overall runtime/explanation remains INCOMPLETE.

## Startup-Profile Gap Closed

Separate GATE ACCEPTED_WITH_RISK the exact4configured profiles, preserved v1
diagnostic and corrected assessment. Parent read `startup_profile/independent_review.json`
in full. Reviewer independently checked typed sanitized rows, exact ID/image and
stopped-state bindings, both predicates, unchanged capture template, captured
Uvicorn current-directory/default behavior and assessment input hashes. No native
capture or test suite was repeated. This scope is closed; no recapture, rebuild
or new universal DNS/TCP requirement follows.

The scoped disposition preserves the original fixed-loopback HTTP zero-transport-
retry contract. It does not require one physical socket/address, and Psycopg
address fallback is not SQL resubmission. Characterized startup effects remain
effects; actual startup and general model readiness are still UNVERIFIED.
No material contract decision is pending from this profile assessment.

Next: assemble the existing exact-image policy records and runtime manifest
from independently reviewed scoped evidence, then use existing inert input
validation. This review is not itself seven loader-consumable policy records;
none were fabricated or approved in this profile task. Runtime remains INCOMPLETE.
No application startup, query, cutover or token handling is authorized by it.

## Exact-Image Policy Record Preparation

ENGINEER / HIGH: `prepare_policy_records.py` mechanically prepares seven
existing-schema image-policy drafts, one runtime-manifest draft and a separate
proposed evidence/scope mapping in `runtime_packet/policy_record_proposals/`.
Every approval draft starts INCOMPLETE with an empty reviewer and UNVERIFIED
policies. The scope mapping is a CLAIMED proposal for independent assessment,
not a source of approval. No policy parser, comparison, production code or
acceptance criterion changed in this step.

The proposal preserves7exact subject/image/preservation bindings and128source
pins, and hashes eight existing independent supporting reviews plus the current
consumer sources. Per-subject scope distinguishes already-running storage from
application startup and planned read/audit effects from unrestricted daemon
behavior. It retains physical-address/pool-reassignment and native-init limits.

VERIFIED_ENV offline verification: `prepare_policy_records.derive()` reproduced
all9saved artifacts byte-for-byte. Calling the existing `_review_json` on every
one of the8unapproved approval drafts refused them, as required. Command:
`env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_continuation_20261021.prepare_policy_records`
published the proposals only; no native operation or approved record was created.
No test suite repeated; no production behavior changed.

Frozen proposals sent to independent GATE for exact-image scoped disposition.
Only that separate review may create accepted records. Existing inert CLI
validation may run after its accepted record bytes and hashes exist; never
use synthetic or self-approved records to make the loader pass. Preparation
handoff READY_FOR_INDEPENDENT_REVIEW. Runtime remains INCOMPLETE and unauthorized.

## Offline Packet Completed and Validated

Separate GATE independently authored and accepted seven exact-image records,
their runtime manifest and a detailed scope review in
`runtime_packet/accepted_policy_records/`. Parent read the complete scope review
and checked independently supplied hashes, all seven child digests, exact128-pin
subjects and the scope hash embedded in every accepted reviewer field.

- runtime_review.json SHA64127a85c985be4e09c0c6df24f5a688d5faae5a38077a3ccd20af7e82d7d43b.
- scope_review.json SHA271c1c2c204f1493fd36caf0db57b5af464aba4c920526e2e77fd019ce24790d.

The independent decision is ACCEPTED_WITH_RISK for the restricted policy packet,
not general image behavior or runtime execution. Storage remains the existing
running3subjects; four applications are the only prospective startup targets.
The original HTTP retry meaning and all recorded provenance/effect limits remain.
Original unapproved drafts and earlier reviews are preserved, not relabeled.

VERIFIED_ENV: ran existing `scripts.research.companion_cutover` once in default
non-executing mode, using the accepted root hash, seven dependency records, actual
preparation evidence/review, derived staged metadata and topical approvals.
Exit0 at2026-10-22T02:30UTC (October21,22:30EDT):

```json
{"state":"READY_FOR_INDEPENDENT_REVIEW","actions_executed":false,"startup_authorized":false,"input_bindings_validated":true,"controller_budget_seconds":600,"recovery_reserve_seconds":180}
```

Full exact command and output are in `runtime_packet/inert_validation_receipt.json`.
No `--execute-cutover`, token descriptor, native command, reservation, credential
read, application query or service operation was supplied/performed. No test suite
repeated. The CLI's static inert-mode state is not operational authorization;
the separate accepted review hashes are the record-disposition evidence.

Offline assembly/independent-policy binding/inert-validation objective CLOSED
ACCEPTED_WITH_RISK. Full runtime/explanation remains INCOMPLETE. The next boundary
is human authorization of one existing bounded runtime attempt, not another
source audit, recapture, restaging, schema change or new approval framework.

Prospective operation only: existing600second controller/180second recovery
reserve; four-app cutover and one archived-evidence cited query; preserve the
three storage services and volumes; existing token only through the reviewed
in-memory handoff; declared audit/log/state writes; owned rollback on failure;
leave new applications running only if all existing acceptance gates pass.
No builds, migrations, new collectors, models, trading or risk/capital changes.
This paragraph is a proposed authorization scope, NOT an execution grant.

## Authorized Single Runtime Attempt: Preparation

Operator replied "carry out the next steps" directly to the explicit bounded
cutover/query authorization question. DIRECTOR scope: execute that one attempt,
with existing600second total controller budget/180second recovery reserve,
four research applications only, three storage services/volumes preserved,
one archived-evidence query, internal token in memory, declared audit writes,
owned rollback and success-only running replacement apps. No automatic retry,
build, migration, new collector, trading or capital/risk change.

The accepted consumer requires an owned anonymous pipe but has no token-source
fallback. ENGINEER / HIGH: added one operation-specific handoff artifact,
`execute_reviewed_cutover.py`, default inert. It freezes the earlier validated
argument list, trusted runtime/scope hashes and reviewed consumer bytes; it calls
the unchanged cutover loader before native work. Its sole token source is the
exact original orchestrator ID/image in the reviewed baseline, conditional on
running state. Docker returns only the existing SERVICE_TOKEN field through a
private in-process capture; no other credential field or account is queried.
JSON framing/duplicate/ASCII/length checks precede pipe handoff. No token value,
length/hash, traceback payload, argv/environment or file persistence is emitted.
Core dumps disabled; reference clearing is not forensic memory erasure.

The handoff closes its writer, transfers reader ownership to the existing
`token_from_pipe` consumer, and calls the unchanged `companion_cutover.main`
once with the execute flag and FD number only. No new controller, parent kill
timer, retry, recovery change or direct application lifecycle command is added.
No credential retrieval or runtime action has occurred at this preparation stage.

VERIFIED_ENV synthetic command:
`env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_reviewed_cutover_handoff.py`
Result13passed0.19seconds on the final handoff source. Tests use a synthetic
internal token and real anonymous pipe/accepted reader, validate no secret in
argument list and reject malformed/ambiguous payloads. No native call or full
suite. Frozen handoff submitted to independent GATE before operation.
Handoff implementation READY_FOR_INDEPENDENT_REVIEW; runtime INCOMPLETE.

### Independent Handoff Acceptance and Dispatch Boundary

Separate GATE ACCEPTED_WITH_RISK handoff SHA
5c319350681e2fb4fdac363e29b829947e0348678fdcc8ecabc84820713adf12;
parent read `runtime_packet/reviewed_handoff_review.json` in full. Reviewer ran
13focused tests on final source and3synthetic descriptor-failure checks; no native
or credential call. Accepted P2 diagnostic limit: entrypoint_handoff_entered can
be true before consumer entry; do not infer actions from that flag. Existing
consumer receipt, reserved marker and actions_executed are authoritative evidence.

Operator approval applies to the exact one runtime attempt above. Dispatch will
verify and execute the reviewed source bytes, request native tool permission,
use the one fixed token source privately, and invoke the existing controller once.
No automatic retry or removal of a consumption marker. Tool approval and actual
execution outcome are pending at this entry; success is not yet claimed.

## Single Attempt Failed; Metadata Defect Isolated

2026-10-22T02:59:16Z (October21 22:59EDT). AUDITOR, VERIFIED_ENV:
the authorized handoff ran once, exit1. Controller receipt shows inputs bound,
installation reserved, staged_checks intended, then installation_failed at
staged_preflight. No quiesce/start/query phase reached; services_started=false,
query_attempted=false. Preserve the reserved attempt; no automatic retry.

Read-only post-attempt inspection of the same15selected IDs shows metadata
identical to saved preparation postcheck: original7running, previous4stages and
current4stages still created. This resolves misleading default summary flags:
prepared_ids_preserved=false was not a demonstrated deletion, and
rollback_verified=false was not a demonstrated rollback failure. No lifecycle
action was reached. This comparison is metadata proof, not volume-content proof.

Failure diagnosis, no new token/HTTP/SQL or service operation:
- Actual PG_VERSION read through the pinned transport passed (0.081seconds).
- All128accepted source pins matched actual transport reads (6.688seconds).
- Actual runtime metadata reader refused with transport_command_failed.
- The same original inspect template over the27current containers exited1;
  a restricted error extractor returned missing field Healthcheck only. Raw
  stderr and source contents were not printed/persisted. No particular missing-
  field container was identified. The exact command on the failed preflight path
  is thus reproduced; original receipt itself lacks check-level diagnostics.
- First isolated diagnostic mistakenly passed noncanonical /tmp config; verify_cli
  refused locally without native command. Corrected canonical diagnostic passed.
  Actual cutover already resolves its config directory: this was not its cause.

ENGINEER/HIGH: changed only optional healthcheck lookup to
`(index .Config "Healthcheck")`, preserving null for absence instead of aborting
the full inventory. No exclusion of unrelated containers, relaxed digest or
authorization gate, marker reset, token fallback or retry. Added one exact
selector regression and two fixture cases preserving null/present healthchecks
and unrelated-container inventory. Existing dirty changes remain untouched.

VERIFIED_ENV offline command:
`env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_runtime_adapter.py tests/test_companion_docker_transport.py`
188passed1.93seconds. In-memory old-selector mutation causes the new selector
regression to fail1/1 (expected); source restored simply by process exit.
These tests do not execute the Go template engine or repaired native path.
No full suite or real explanation query. Repair READY_FOR_INDEPENDENT_REVIEW.

Evidence: runtime_packet/authorized_attempt_outcome.json (full summary, original
private-receipt digest, diagnostics and limits), post_attempt_inventory.json.
Adapter SHAe7315cd9047f656afca0b3845be54629c46c80c9a20065d8646978dce20fce38;
test SHA3ca8318be5ecda58f5ea6e758ba18720f6ed23e2adc6dcf4b3765e50d85f8c8b.
The reviewed handoff freezes old adapter bytes and must NOT be reused against
changed code. Next boundary: independent offline review, narrowly refreshed code
bindings, then a separately authorized operational attempt. Runtime INCOMPLETE.

### Independent Metadata Repair Disposition

Separate GATE record runtime_packet/metadata_healthcheck_review.json is
ACCEPTED_WITH_RISK for this exact offline selector repair only. Parent read the
complete record and checked its two final source hashes. Reviewer independently
ran3new regressions (3passed,68deselected0.20seconds), and verified reversing
only this selector reproduces the prior cf2d6193 adapter SHA. No reviewer native,
credential, service or query operation. Earlier READY_FOR_INDEPENDENT_REVIEW
entries remain historical stages, not current disposition.

The original receipt does not establish exclusive causation; reproduced metadata
failure is SHOWN, a successful repaired cutover remains UNVERIFIED. Old packet/
launcher bindings and consumed marker remain untouched. Do not execute the old
launcher. Runtime INCOMPLETE; changed binding refresh and separate operational
authorization remain before any new attempt.

## October 22: Consumer Binding Refresh

AUDITOR, 2026-10-23T00:21:28Z (October22 20:21EDT). Continued the accepted
offline binding-refresh objective; no current native/container observation,
credential read, service operation, query or scheduled-task change.

SHOWN: exactly one of the seven prior bound consumers differs: adapter
cf2d6193 -> independently accepted e7315cd9. The other six exact consumer
hashes and the metadata-repair review's three file bindings still match.
Old records/launcher, seven subject policies, preparation IDs and failed
reservation remain unchanged. No new policy meaning or resource scope.

Invoked existing companion_cutover.main offline with the exact argument list
from hash-checked inert_validation_receipt.json, without execute/token flags;
Popen and network entrypoints patched to refuse. Exit0,
input_bindings_validated=true, actions_executed=false, startup_authorized=false;
no full/targeted suite repeated. The same probe verified old launcher inputs()
refuses reviewed_consumer_changed and consumed-attempt file digests stayed
unchanged. Result saved in runtime_packet/consumer_binding_refresh_validation.json
(SHA8ab0c07517a8a34cf682e173cd953d2dd37d0f3ef5593a357ee9fc0c8040dd03).

Important remaining implementation constraint, not an operator/account failure:
companion_cutover._reserve uses the preparation's plan.attempt as the exclusive
execution-receipt directory. It will refuse the existing consumed directory.
The inert validator does not check that eligibility. A code-hash refresh alone
therefore cannot make this plan executable again. main reserves before consuming
token_fd, but the external handoff producer reads the token before calling main;
do NOT invoke that producer merely to test the consumed reservation.

Recommended next offline repair: distinguish a separately reviewed execution
receipt identity from unchanged preparation identity, explicitly bind the prior
pre-start failure, preserve all old receipts/markers/IDs, and retain fresh exact
preflight and single-attempt limits. No such continuation path is implemented or
authorized by this record. Do not evade the marker by deleting it, changing
preparation labels, modifying evidence or recreating the stopped containers.
Any implementation requires independent review; runtime requires separate bounded
authorization. Runtime remains INCOMPLETE. Binding refresh review pending.

### Binding Refresh Independently Accepted

Separate GATE completed runtime_packet/consumer_binding_refresh_review.json,
SHA817ada1c70811f878104c91cba42b2972612ecae6b9d6d856fcf7a3b6325b9f8,
ACCEPTED_WITH_RISK for supplemental offline consumer binding only. Parent read
the complete record and verified every bound artifact and all seven consumer
hashes. The original scoped policies remain valid without reissuing their
records; only adapter host-code binding is supplemented. No tests repeated or
native/credential/service/query operations by reviewer.

Binding refresh CLOSED ACCEPTED_WITH_RISK. No executable handoff readiness or
operational grant. The separate execution-receipt/preparation-identity
continuation requirement remains unimplemented, independently confirmed from
_reserve and ReviewedPreparation source. Original marker, prepared IDs, receipt
and historical bindings stay intact; runtime INCOMPLETE.

## Offline Pre-Start Continuation Implemented and Reviewed

Operator requested the next offline repair. Implementation details and frozen
source hashes are in companion_prestart_continuation_20261022.md. The existing
entrypoint now accepts a paired external continuation review/hash that binds a
new execution receipt to unchanged preparation identity, same4IDs, exact prior
pre-start failure and ten host-consumer hashes. It rechecks under the existing
shared lock before exclusive reservation/token consumption. No retry loop,
marker removal, relabeling, restaging or fresh-preflight/recovery bypass.

VERIFIED_ENV:142focused offline tests passed2.46s (continuation, entrypoint,
input loader and staged controller). Separate GATE independently ran37new tests:
37passed0.76s. Review runtime_packet/prestart_continuation_implementation_review.json
SHAdfeaf12e2b2f2ff7f38e7954fc21f818cdd878c733c5aac8dc90f83ae9e45ded:
ACCEPTED_WITH_RISK for the exact implementation only. Parent read complete record,
verified all9bound files and unchanged original receipt hash. Frozen implementation
checkpoint remains unmodified to preserve the review's exact-byte binding; its
ready-for-review status describes that earlier handoff stage.

No native operations, real token reads, service changes, scheduled-task changes,
accounts or trading this step. No actual continuation approval record or refreshed
executable producer is issued. Next: independently reviewed exact-input record
and token handoff using the accepted current consumers, then separate bounded
operational authorization. Old launcher and consumed attempt remain unusable.
Runtime INCOMPLETE; repaired native startup/explanation remain UNVERIFIED.

## Exact Continuation Packet Ready for Operational Decision

The independently authored actual continuation record (56c03c4c...1ccc) and
scope (2ae3cc1e...e649) bind a separate s3cutover20261022health01 execution to
unchanged preparation/four IDs/failed receipt/ten current consumers. Versioned
execute_reviewed_continuation.py preserves and reuses SHA-verified original
source-format/token-parser/private-pipe helpers, checks actual bindings before
credential access, and remains inert by default. No old artifact was rewritten.

Parent66focused tests passed1.20s. Separate GATE independently17passed0.39s,
ACCEPTED_WITH_RISK handoff in reviewed_continuation_handoff_review.json
SHA3e134045ff27c3aba1b34d656e3267c0202b52c5485c2d8d0c382a8a51c9230d.
Parent read full record and verified18bound files. Assembled actual default CLI
exited0/input_bindings_validated=true/actions_executed=false/startup_authorized=false;
command/full output preserved in continuation_inert_validation_receipt.json.
Original failed receipt unchanged; new reservation absent. No native/real-token/
service/query operation this preparation stage. No full test suite repeated.

See companion_continuation_handoff_20261022.md for exact hashes, tests and risks:
producer precheck is advisory, consumer lock/reservation authoritative; entered
flag is not action proof; no forensic token zeroization; bounded handoff prelude
precedes existing600/180controller budget. These limits are not hidden behind
offline acceptance. Preparation COMPLETE ACCEPTED_WITH_RISK; runtime INCOMPLETE.
Next is separate human authorization of one exact bounded attempt, not more
assembly or re-auditing. No operational approval is supplied by this checkpoint.

## Authorized Operation Failed; Packet Consumed

Operator subsequently authorized the explicit single attempt. Exact reviewed
launcher ran once, exit1, at2026-10-23T00:46-00:47Z (October22 evening EDT).
Staged/source and storage checks advanced to orchestrator quiesce, which failed
before replacement startup/query. Recovery cleanup removed the current4owned
never-started replacement IDs. The new execution reservation is consumed; old
failed receipt remains intact. Earlier ready-for-authorization text is historical.

Actual output: rollback_exact_baseline=true but rollback_verified=false with
unresolved orchestrator quiesce ownership. Read-only postcheck at00:49Z confirms
all7originals running with identical selected metadata;11survivors all unchanged,
only4preparedIDs missing, old4stages intact. No manual follow-up lifecycle action
or retry; no claim of full-volume equality. The private token was used only by
the authorized handoff and not retrieved during diagnosis.

Exact quiesce substep remains UNKNOWN. Current read-only pre-signal check passes;
sh parent/uvicorn child is merely a lead; empty retained event query is nonproof.
Do not assume signal forwarding caused it or change signals/deadlines to force a
pass. Separate evidence review INCOMPLETE, causeUNKNOWN, SHA30115967...a0e76;
parent verified every bound evidence hash. No source/test change this operation.

Current evidence and next OFFLINE diagnostic scope:
companion_continuation_failure_20261022.md,
runtime_packet/continuation_attempt_outcome.json and
runtime_packet/continuation_post_attempt_inventory.json. Existing packet cannot
be rerun and removed IDs cannot be reused. No fresh preparation, forced kill,
recreation, restart, further signal or new runtime attempt authorized. Runtime/
explanation remain INCOMPLETE; next is saved-row replay and synthetic quiesce
substep evidence before any reviewed repair/new operational proposal.

## Offline Diagnostics Independently Accepted

The saved-row replay and diagnostic implementation are complete. Separate GATE
accepted the frozen patch ACCEPTED_WITH_RISK, with 21 new tests independently
passing. Parent verified the review and all seven source/supporting hashes:
runtime_packet/quiesce_diagnostics_review.json, SHA
8a227fa32856874ce6a1b9db7ac91e12864938a0be75c4723f039c2d6cd4dc07.
The implementation checkpoint remains frozen with its historical review-pending
status; this later record supplies the acceptance, not a source change.

No historical shutdown cause or live repair was established. Runtime remains
INCOMPLETE. Current continuation bindings are stale, the attempt consumed and
four prepared IDs removed. Next is a bounded read-only look at the original
orchestrator's current process/signal dispositions, with no signals, credential
reads, preparation, lifecycle changes or retry. Current dispositions cannot by
themselves prove what occurred during the failed attempt.

## Read-Only Signal Observation Completed

At2026-10-23T01:12:15Z, exact original orchestrator/image/start/restartcount
matched before/after three bounded native read-only command operations. Container
PID1 is sh without a SIGTERM handler; childPID7 is uvicorn with one. Current
quiesce signals the main process, and allfour frozen replacement command arrays
retain the shell wrapper. This supports a current shutdown-target mismatch, not
proof of which historical substep failed. See companion_signal_diagnosis_20261022.md
and runtime_packet/orchestrator_signal_observation.json. No lifecycle/credential
actions; temporary exec process and Docker execution events are disclosed.

Next proposal is an offline lifecycle-contract repair: verified worker targeting
for originals plus exec-based future replacement launch. No hardcoded childPID,
SIGKILL or silent deadline extension. This changes reviewed contract/metadata and
is not authorized by observation alone. Runtime INCOMPLETE; no packet reuse,
marker reset, preparation or retry performed.

Separate AUDITOR interpretation review: ACCEPTED_WITH_RISK, no material findings;
both diagnostic evidence hashes verified. This reviews the inference limits,
not native reobservation, source/manifest verification or the proposed repair.
Full response captured in runtime_packet/orchestrator_signal_interpretation_review.json.
No implementation/operational acceptance inferred.

## Offline Lifecycle v6 Implementation

October23: implemented the next scoped repair, source frozen for independent
review. Explicit v6 opts into identity-verified pidfd original-worker shutdown
and fixed direct-Uvicorn replacement commands, including empty image entrypoint
checks; v1-v5 behavior is preserved. Targeted11file slice509passed3.66s; no native
commands, service requests, credentials, signals or operations. Both prior
receipts, manifest, continuation record and observed-signal evidence retain
their exact hashes.

See companion_worker_shutdown_repair_20261023.md: six source/test hashes,
verification command, two material assumptions and remaining limits. Runtime
still INCOMPLETE. Implementation READY_FOR_INDEPENDENT_REVIEW; no new actual
manifest, preparation, packet, retry or permission. Installed capability/argv,
clock compatibility and successful acknowledged shutdown remain unverified.

Separate GATE completed the bounded offline review ACCEPTED_WITH_RISK, no
blockers, independently45newtests passed0.33s. Parent read the full review and
verified allsix source/test hashes plus the frozen checkpoint. Review:
runtime_packet/worker_shutdown_repair_review.json. The implementation checkpoint
keeps its historical review-pending status because its bytes are review-bound.
Offline acceptance does not authorize operation or prove live shutdown. Next
boundary is current read-only installed capability/time/process evidence before
any reviewed fresh v6 preparation/runtime proposal.

## Installed Prerequisites Observed Read-Only

October23 08:49EDT: all4original app identity validators passed with real kernel
pidfd opens and the signal operation replaced by a read-only fdinfo callback.
Signal API is present in Python3.11.17; it was never called, including zero.
All7originals retained pinned selected metadata and running state before/after.
Clock sample intervals all include zero; roughly84-95ms roundtrip precision,
not exactsync, futureclockguarantee or an approved tolerance. Six read-only
native command operations, no credential/environment reads or argument exports;
temporaryexecprocesses/kernelhandles/Dockerevents disclosed.

Checkpoint companion_worker_capabilities_20261023.md and saved observation/probe
capture this bounded result. Sources and original receipts/manifest unchanged.
Evidence READY_FOR_INDEPENDENT_REVIEW; runtime INCOMPLETE. Actual signal delivery,
shutdown/ack/recovery and real citedquery remain unverified. No new actualv6
manifest/preparation/packet/IDs or operation; consumedattempt not reset or reused.

Separate GATE ACCEPTED_WITH_RISK this bounded evidence snapshot, no blockers.
Parent read full worker_capabilities_review.json and verified allthree pinned
evidence/checkpoint/probe-suffix hashes. No independent native reobservation:
exact interpreterflags remain parent-reported; raw remoteepochs and separate
secondinspectpayload were not retained in these artifacts. Reviewer checked
interval widths/inclusionofzero, not rawremoteendpoint recalculation. These are
provenance limits, not reasons to rerun the same check or infer full runtime
success. Frozen evidence/checkpoint unchanged. Next is offline fresh-v6 planning;
no packet/preparation/operation is approved by this evidence review.

## Fresh v6 Preparation Draft Assembled

October23: new attempt workerprep20261023v6a is proposed and unreserved. Offline
derivation preserves43sourceentries and seven original fullsaved snapshots,
changing only schema/attempt/clearedreviewfields/fourcommands/fourMODELEDmetadata
predictions (12fieldgroups). No actualnewimage/ID evidence; priorstagedIDs are
removed historical modeling inputs only. Recipe, draft, provenance and nine
targeted passing tests are frozen for separate input review; see
companion_worker_preparation_inputs_20261023.md. No acceptedmanifest or operational
permission generated by this thread. New source-support hashes are recorded;
no prior reviewed source/helper/receipt changed or tests repeated broadly.

Any later preparation is separately authorized: existing300/120controllerrecovery
budgets, fourlocalCOPY-onlybuilds/fournewneverstartedappcontainers, privatecopy of
existingconfiguration/credentials, owned-new-onlycleanup, nooriginalinterruption,
startup/query/storagechange or cutover. ActualIDs need independent review before
assembling runtimeinputs. Current runtime/explanation remains INCOMPLETE.

Separate GATE ACCEPTED_WITH_RISK prospective inputs, no blockers, independently
nine tests passed0.22s. It published a separate accepted derivative changing only
decision/reviewer, SHA35032e02db1bf1d569d7918ef9127562abc205154d68908455c3ec5bf3201d42.
Parent read full inputs/preparation_plan_review.json and verified all24boundfiles,
exactderivative and unchanged priorreceipts; newattempt stillunreserved.
Existing prepare defaultCLI exit0/actionsfalse/startupfalse; exact command/output
saved in inputs/inert_validation_receipt.json. No --execute-preparation/native
action. Frozen implementation checkpoint remains historical READY_FOR_INDEPENDENT_REVIEW;
this later entry supplies separate acceptance of offline inputs only.

Offline packet task complete ACCEPTED_WITH_RISK. Next requires explicit approval
of ONE preparation-only run with the reviewed manifest: four local builds/four
new neverstartedcontainers and private existingcredentialcopy; original seven,
older stages, volumes and prior consumedmarkers preserved. No cutover/start/query
permission. ActualnewIDs must be separately reviewed after any authorized run.

## Authorized v6 Preparation Failed; Correction Pending Review

Operator then approved that one preparation-only run. Existing command ran once,
exit1/preparation_build, workerprep20261023v6a consumed; cleanupverifiedtrue/no
unresolvedcreationcleanup. Receipt has no createintent or newID. All11prior
resource metadata rows compare equal before/after; no attemptnamedstages found.
Not a volume/cache audit or proof any build command ran. Raw sanitized evidence
and command/result are under companion_worker_preparation_20261023/actual/.

Read-only engine/image diagnosis reproduces an optional Entrypoint-key template
failure in the new v6 check. One-expression nullsafeindex correction has194
targetedpasses; equivalentreadonlyquery passes4parentimages. No runtime retry.
Same bounded handoff includes prospectivev6b inputrefresh (onlyattempt/reviewfields
andonebackendbinding),7proposal/regressionpasses, oldrecords preserved. See
companion_worker_preparation_failure_20261023.md. Correction/refreshedinputs
READY_FOR_INDEPENDENT_REVIEW; runtime/preparation INCOMPLETE. Previous inputs are
stale for changed source and consumed, never reset/reused. No second attempt,
startup, query or cutover authorized.

Separate GATE completed the combined correction/input review ACCEPTED_WITH_RISK,
no blockers; failedactualv6a remains INCOMPLETE and consumed. Independently7new
tests passed0.31s; before/post11row equality and exact reverse-source hash verified.
Parent read full correction_and_plan_review.json, verified allboundhashes and
fresh derivative changingonlydecision/reviewer, SHA67e29202a3bcd78f050f94b42bc87f91c7a50be90d3485ebd1fc0cfac0b7485e.
New defaultprepareCLI exit0/actionsfalse/startupfalse, saved refresh_inputs/
inert_validation_receipt.json. v6b remains unreserved, v6a receipt unchanged.

No secondpreparation or runtimeaction. New explicit approval is required for one
fresh preparation-only run under the corrected reviewed inputs. Fourlocalbuilds/
fourneverstartedcontainers/privateexistingcredentialcopy and ownednewonlycleanup;
nooriginalinterruption/startup/query/cutover. ActualnewIDreview stillrequired.
Historical checkpoints/candidate/proof are frozen, not overwritten to hide failure.

## Corrected v6b Stopped Preparation Completed

Operator separately approved one corrected preparation. Existingcontroller ran
ONCE, exit0/preparationcomplete;4newstoppedIDs created without service startup or
original interruption. Sevenoriginals/fouroldstage full selectedrows unchanged;
4actualstage snapshots/digests match controller evidence, directcommands verified,
43actualcopiedsourceentries hash-match. Four finalalias projections match their
MODELEDexpectedfingerprints but have not been applied. No cutover/query/signal.

See companion_worker_preparation_result_20261023.md and companion_worker_preparation_20261023/
actual_b/ for exact command/stdout, privatepublicbyteidentical evidence/receipt,
raw15postrows and sourcehashwitness. Images may reusecache; newcontainerIDs are
distinct and neverstarted. Evidence da7ee2de44a4e98990cceb6b4c53edc530fc717cc45c7c94d6b65994edfa35ef.
No source/testchange or pytest repeated. ActualID/source/image/fingerprint review
requested, READY_FOR_INDEPENDENT_REVIEW; runtime INCOMPLETE. Next after separate
acceptance is offline runtime-packet assembly, not another operational attempt.

Separate GATE ACCEPTED_WITH_RISK actual stoppedpreparation only, no blockers.
Detailed disposition actual_b/actual_id_disposition.json SHA5acff968aa55160d21673691cdbef2dc7be0c520caae06aadbbeedf58e04f4bd;
existing5field loaderreview actual_b/actual_id_review.json SHAc8fd96dd96b12576a82494d079022f6571ef52dd8bbdade7a154a70d826bce96.
Parent read disposition/limits and programmatically verified43repeatedsource
witnessrecords and allfrozenhashes. Existing pure Plan/ReviewedPreparation loader
passes with the exact externalreviewhash and4acceptedIDs; no backend/native call.
Saved actual_b/loader_validation.json. No pytest or codechange.

Limits preserved: no independent reviewer Docker reobservation, attemptlabel
comes from controller evidence, and after-copy equality is a parent assertion
without separately retained finalinspectrawrows. Finalalias fingerprints remain
MODELLED. No health/runtime/shutdown/query/cutover/profitability acceptance.
Stoppedpreparation milestone complete ACCEPTED_WITH_RISK; fullruntime INCOMPLETE.
Next permitted task is offline packetassembly for these exactacceptedIDs, not
any new operational attempt or automatic startup.

## October23 Offline V6b Runtime Draft

Under operator approval for offline assembly only, derived12immutableartifacts
in companion_worker_preparation_20261023/runtime_packet_v6b/. Existing128source
pins/images and storage3bindings retained; application4 exactnewIDs/snapshots
validated from accepted evidence,43sourceentries directly witnessed. Finalalias
preservationprojections remain MODELLED. Oldrecords and consumedattempts intact.

Newproducer/tests/checkpoint: companion_v6b_runtime_packet_20261023.md. Isolated
7tests passed0.18s; no subprocess/network/native/credential/service operation.
Allsevenpolicyproposals/runtimeproposal remain INCOMPLETE, emptyreviewers.
No policyapproval, tokenproducer or executablehandoff manufactured. Separate
GATE reviewing exactdraft and applicability to direct-module Uvicorn launch
and currentconsumers. Draft READY_FOR_INDEPENDENT_REVIEW, runtime INCOMPLETE.

Separate GATE completed: offline derivation ACCEPTED, policyapplicability
INCOMPLETE. independent_review.json SHA
b8e72a553264b02357b6ccd569b82551fd016b0c4d3e1c151259bfe3be78e33a.
All12draftoutputs independently reconstructed; all128sourcepins retained and
43directwitnesses checked. Parent verified44review-boundartifact/sourcehashes.
No reviewer tests/nativeoperations; parent7testresult remains separately labelled.
Frozen draft/checkpoint unchanged; previous actualIDacceptance remains in force.

R1 is missing exact-image Uvicorn package __main__.py source/delegation evidence
for the new direct python-mUvicorn commands. This is not evidence of unsafe
behavior or a failedstartup. No completeimportclosure audit is required.
No acceptedimagepolicy/runtime derivatives created by the review.

Proposed next bounded capture, NOT authorized/performed: only
/usr/local/lib/python3.11/site-packages/uvicorn/__main__.py from each of the
four acceptedstoppedv6b IDs. Fixed-path readonly docker-cp, <=64KiB perfile,
sanitized exactID/image/state inventory before/after, <=15s percommand and
120s overall. Preserve readable sourcebytes and hashes for staticreview;
no imports/exec/start/stop/build/create/signals/servicequery or credentialread,
no broadsearch, no retry. Fresh pinnedCLI/image/ID/state checks must still pass
before any separately approved capture. Storage/originalcontainers untouched.
After sourcebridge review, packetpolicy applicability may be reassessed without
repeating acceptedpreparation/derivation or redesigning the runtime.

## October23 Approved Launcher Capture Completed

The operator explicitly approved four-file readonlycapture. One fixeddriver
invocation completed6native readcommands in0.303s:4IDbeforeinspect,4fixedpath
docker-cp,4IDafterinspect. Each separatefile62bytes, identical SHA
0d08b3cba9ca3f4cb084fa6708782644360831f72a64a544ccd2164198eab554.
Source imports uvicorn and calls uvicorn.main() under __main__ guard; source
was read, not executed/imported. FourcreatedneverstartedIDs/images/name/command/
entrypoint/workdir/started/restartfields unchangedbeforeafterandpriorsavedfields.

See companion_uvicorn_launcher_capture_20261023.md and launcher_capture/report.json
SHA5e1f397376c0e2f4ff1617b5881accb70baf5202ef35bfe2b7bfdf2e58d36d32.
No nativeops otherthan6approvedreads; no envsecrets/credentials/startup/build/
signal/reservation/servicequery/trading. Runtime _path allowlist unchanged;
capture used separately authorized fixedarguments, not a general transportbypass.
Separate staticreview pending on launcherbridge; no repeatednativecapture or
broadsuite. Evidence READY_FOR_INDEPENDENT_REVIEW; runtime INCOMPLETE.

Separate staticreview completed: captureevidence and narrow R1staticbridge
ACCEPTED_WITH_RISK. launcher_capture/independent_review.json SHA
03a3e5fc9687cb190bc0a099fa984d050a8578fec6a82d1ee790b5371effaab1.
Parent readfullreview/verified13boundhashes, no repeatednativeoperations/tests.
R1missing-sourcegap CLOSED: same62bytes on4exactID/imagebindings, staticshim
delegates to existingUvicorn packageCLI with no own addedretry/config/worker/
proxy/network/subprocess behavior. Actual import/callable/startup remains
UNVERIFIED. PrioractualIDacceptance and original128pins unchanged.

Review I1identifies one separate minimalofflineintegration requirement: add
only the fixed launcherpath to runtime transport _FILES; add thecapturedhash
to4applicationsubjects (128to132totalpins), explicitly requirethoseentries in
refreshedv6bpacketvalidation, and refreshaffectedconsumer/packetbindings.
Do not broaden _SDK or bypass normal _path. Preserve existingdraft/reviewbytes.
That change was not implemented/authorized by capture-onlyscope. No accepted
runtimepolicyset or tokenproducer created; no automaticoperationpermission.
Captureobjective complete ACCEPTED_WITH_RISK; runtime/explanation INCOMPLETE.

## October23 Exact Launcher Pin Offline Integration

User requestedfinishremainingwork. Implemented I1 as one fixedtransport_FILES
path and4additivesourcepins in separate runtime_packet_v6b_launcher/ drafts;
132total,all128oldpins/IDs/images/storage/modelledpreservation unchanged.
TransportSHA5cbdf417a6b180bdd6e77cf7c9b85eba6649ebd15212f0836725f13301edcd81;
removingonlythatline reconstructs old817c... source. No regex/authorization/
ID/timing/limit/lifecycle change. Exact13consumerhashes checked; onlytransport
binding changes. Priorreviewedartifacts remain unchanged and are not newhandoffs.

Focused packet/transport/cutoverinputs run:152passed1.54s; no fullsuite/native/
credential/startup operation. See companion_launcher_pin_integration_20261023.md
for exactcommands/hashes/scope. IndependentGATE reviewing frozenimplementation,
derivation and restrictedpolicyapplicability; no self-issuedpolicyacceptance.
Implementation READY_FOR_INDEPENDENT_REVIEW, runtime INCOMPLETE.

## October23 Offline Integration Accepted And Loader Validated

Separate GATE ACCEPTED_WITH_RISK exactonepathtransportdelta and132pinpolicy
applicability, no blockingfindings. R1/I1 closed in source/configuredscope only.
Reviewer independently14selectedsynthetic tests passed0.24s; largerparent152case
run remains separate. IndependentreviewSHA
607dbae7221bbb51738b82f3c28e2961adb6f993c47b2cc092017cbbec360835.

Reviewer authored7exactsubjectpolicychildren, runtime_review.json and
scope_review.json under runtime_packet_v6b_launcher/accepted_policy_records/.
Runtime reviewSHA47dbeebdbdbd3cd978156f9a25d8b07027f34023ab6b0ff541f2d05cfc1ca3e6;
scopeSHAd32f3589c9156844f9a4211a3cec289c36c5260536e82c82be38f947d3ff4054.
Parent verifiedaccepted9recordhashes, support/artifact/current13consumerhashmaps,
and compared inherited7policy-rationale/risksets and policymeanings to oldscope.
Repeatedsubject/source rows checkedprogrammatically, not claimed fullyread from
truncatedtext. Newapplicabilitybases and alladditional/preservedlimits retained.

Parent existingdefault companion_cutover.main acceptedactual132pinrecords:
exit0,input_bindings_validated=true,actions_executed=false,startup_authorized=false;
attemptworkerprep20261023v6b,600scontroller/180srecovery budgets. Noexecute/token/
continuationflags. Duringvalidation subprocess/network calls, nativebackend/
transport construction, token_from_pipe and _reserve were patched forbidden.
No runtimecredential, reservation, signal, startup or servicequery. Exactargv/
stdout/trustedhashes in runtime_packet_v6b_launcher/inert_validation_receipt.json
SHAaebbeb6384465e01fff7d2354b4e654619af5d57d566d304607d35619aabe0af.

Offlineintegration milestone complete ACCEPTED_WITH_RISK; no morecapture,
producerderivation or targetedsuite repeats queued. Runtime/explanation remains
INCOMPLETE, and no executedshutdown/ack/SDK/health/network/citation/profitability
proof follows. Current acceptedrecords do not grant an executabletokenhandoff,
cutover or retry. Any operationalattempt requires a separate boundedauthorization
and must use currentreviewedinputs/consumerbindings, not oldconsumedlaunchers.

## October23 Fixed V6b Handoff Prepared Offline

New execute_reviewed_v6b.py reuses hash-pinned original tokenformat/parser/
privatepipe helpers, never oldinputs/execute. Validates currentacceptedreceipt/
review/scope/runtime/13consumers/7subjects/132pins and exactv6bworkerplan.
Default onlyexistinginertCLI; futureexplicitexecute refusesusedreservation
before fixedoriginalID/image/running-service-token read. No fallback/retry.
Controller600s/180recovery retained; separatepre-controllerCLIverify10s/source
read10s disclosed ratherthan falselyclaimedinsideone600soverallbudget.

Targeted3file52tests passed0.71s(18new); allnative/tokenresponses synthetic.
Actualdefaultmodulehostcommandexit0/inputbindingsvalid/actionsfalse/startupfalse.
Saved handoff_inert_validation.json; no --execute-once or livecredentialread.
FrozenwrapperSHAF9362E808538FA9D3FDBE7DC29B8BB947283BBD2AE720771963DF1B8D4B37DFE.
See companion_v6b_execution_handoff_20261023.md for full impact/limits/commands.
Handoff READY_FOR_INDEPENDENT_REVIEW; separateGATE reviewing frozeninputs.
No nativeDocker, sourcecapture, service/startup/query/reservation/trading action.
Runtime INCOMPLETE; no operationalauthorization inferred.

SeparateGATE ACCEPTED_WITH_RISK offlinehandoff only, no blockingfindings.
Review runtime_packet_v6b_launcher/handoff_review.json SHA
c923b36c6c7626ff0ad09bdf27d933d32c5226a90e8cd71d347711ae50747487.
Independent18synthetictests passed0.36s; parent52case run remainsseparate.
Parent readcomplete review and verified23boundartifact/currentconsumerhashes.
Frozenwrapper/tests/checkpoint/acceptedpacket unchanged; no moretest/nativework.

Limitsretained: lexistsbeforetoken is advisory, not atomic/globalonceguard;
existingcontrollerlock/exclusivereservation remains authoritative. Handoffentered
means helperattempt, not proof of reserved/mutatedstate. Referencescleared is not
memoryzeroization. Producer10sverify/10ssource precedecontroller600/180, not one
wholewrapper600sdeadline. Actualtoken/sourcepermission/startup/shutdown/ack/
network/health/recovery/citation and rollbackhealth remain UNVERIFIED.

Handoffpreparation objective complete ACCEPTED_WITH_RISK. Next explicitoperator
approval must cover ONE frozen --execute-once invocation and disclosedeffects:
privateexistingservice-tokenread,4originalresearchappsgracefulquiesce/rename/
detach,4acceptedstageactivation/start,existingfreshchecks and onecitedarchivequery.
3storageoriginals/volumes remain untouched; no build/create/migration/ingestion/
collector/account/trading changes. Logs/auditwrites maypersist. Failureowned
cleanup/restoration attempted within existingrecoverybudget, not guaranteed.
Only fullsuccess leavesreplacementsrunning; no retry/reset or reuseofoldconsumed
launchers. No runtimeinvocation is authorized or performed by this acceptance.

## October23 Authorized V6b Attempt Failed; Current State

The operator subsequently approved ONE actualinvocation. The frozen --execute-once
ran once and failed runtime_verification immediately after configured_compatibility
intent, before replacement_start_intended/query_intended. Controller reports
receiptcomplete/rollbackverifiedtrue, exactbaselinefalse/no unresolvedoperations.
The private/public61eventreceipt confirms4originalworkerexit acknowledgments,
4stageactivation identity/configchecks, thenownedcleanup removes4preparedIDs and
restores/restarts4originalapps. servicesstartedtrue includes thoseoriginalrestarts.
Attempt workerprep20261023v6b consumed; no retry/reset or newpreparation grant.

Readonlypost2nativecommands SHOWN7originals running/sameIDs/images/names; all11
survivingknownresource configuredprojections matchprior.3storage starttimes
unchanged/4originalapp starttimeschanged;4oldstages sharedfields equal,4newIDsabsent.
Rawpost falsefullrow/rawpreservationflags retained/explained:5historicalfields
notrecaptured and3IPAMConfignull-to-emptyobjectdifferences. No byteexactstate/
health/volumebytes claim. Noextra servicequery/tokenread or lifecycleoperation
performed duringpostcheck.

Offline savedpacketreplay SHOWN4acceptedfinalpreservationpins were built with
blankstagedNetworkIDs. Substituting knownphysicalnetworkbinding changesall4raw
preservationdigests withoutchangingconfiguredprojections. Packet-model/adapter
representation defect; likelycandidate, not capturedactualper-predicatecause.
Activatedreplacementrawrows/compatibilitysubcheckresult were not retained.
The NetworkID-only replay is not an approvedcompletecorrected fingerprint;
IPAM/defaultalias representations and both producer/loader modelling must be
covered before any correctionproposal. Do notweaken identity/sourcechecks.

Frozen fullrecord: companion_v6b_runtime_attempt_20261023.md and
companion_worker_preparation_20261023/runtime_attempt_v6b/.
OutcomeSHA1ce084cb...744f,receipt63003bed...5d5a,rawpost44602ff8...4d40,
offlinereplay939dc97d...8cae. No productioncode/policy/inputchange afterfailure.
Separate failure/replayreview pending; runtime INCOMPLETE. This result supersedes
older preparation-ready/current-ID text:4v6bIDs no longerexist, original4apps
have newstarttimestamps. No automatedrepair/newcollector/preparation/retry.

Separatefailure/replayreview completed ACCEPTED_WITH_RISK for evidenceinterpretation
only; runtime/source remains INCOMPLETE. runtime_attempt_v6b/independent_review.json
SHA6544e658ad89ef2aea7e1a7124c03905640c920926ac9d7dfb5b2fe5195599a0.
Parent readcomplete boundedreview, verified14boundartifact/source/inputhashes and
programmaticallymatched11comparisonrecords/4fingerprintmodels to savedreplay.
Reviewer independentlyrecomputedrepresentationcomparisons; no native/tests or
private receiptread repeated. Private/publicreceiptidentity remainsparentproof.

Review confirms Codexpacket/modeldefect across originalassembler and strictloader
aliases-only finalprediction; actualconfiguredcompatibility comparesrawpreservation
first. No actualactivatedrow/per-predicatefailure retained, so exactcause not
invented. IPAMnull/{}differences shown onrestoredoriginals; defaultaliasdifference
is a boundedmodelobligation, not a demonstratedactivatedaliasfailure.
Savedreplay last_runtime_operation=inventory includes rollbackinventory; the last
PRE-FAILURE operation was configured_compatibility. Do not confuse those stages.

Nextoneofflineobjective: correctsharedactive-networkprediction in producer AND
companion_cutover.load_inputs, prove intendedequivalencerepresentations while
stillrejectingwrongnetwork/container/image/source/unexpectedconfiguration/aliases.
Preservelegacycontracts and strictidentity/sourcechecks. Add onlynecessary
sanitizedpredicate/stagediagnostics, not a newframework/importaudit or invented
historicaltrace. No correctioncode/freshpreparation/IDs/operation has been built
or authorized by this evidence-onlyreview. Consumedv6b/removedIDs remainhistorical;
anyfuturepreparation/operation requires genuinelyfresh reviewedinputs/approval.

## October 23 Offline Correction Implemented

The operator requested the bounded correction. ENGINEER implemented the shared
final-model/subject helpers, a new inert historical producer, opt-in V2 reviewed
configuration semantics in loader/adapter, and sanitized compatibility receipts.
Legacy raw hashes/inventory/storage/rollback comparisons remain unchanged; raw
evidence, old assembler and failed consumed packet remain frozen. Exact declared
aliases are required; extra daemon names are not guessed equivalent. Configured
blank IDs are allowed only on never-started created applications; actual recipient
attachment remains a separate pre-query gate.

Final focused local verification: 434 passed in 2.82s, no full suite/native ops.
Implementation READY_FOR_INDEPENDENT_REVIEW, runtime INCOMPLETE. No fresh IDs,
credentials, Docker operations or retry. Details/hash bindings and limitations:
`docs/checkpoints/companion_active_network_correction_20261023.md`.

### Separate Offline Acceptance

Independent GATE accepted the frozen correction ACCEPTED_WITH_RISK, no blocking
findings, 109 selected synthetic tests passed in 1.33s. Counterfactual reproduced
independently byte-for-byte. Review at
`companion_worker_preparation_20261023/active_network_correction/independent_review.json`
has SHA256 `0484cdde9dec89b2a22f91aa4082cbe2782caa10318b5ad027363a6feac9bacc`.
Parent read the complete review and verified all bound artifact/source hashes.
No implementation, tests or reviewed checkpoint changed after review.
Acceptance is offline implementation only, not installed policy applicability,
fresh preparation readiness or operation authority. Runtime remains INCOMPLETE.
Fresh-ID/complete-alias evidence and separately authorized operations remain
required; no old consumed packet or receipt can be reset/reused.

## Fresh Preparation Inputs Independently Accepted, October 23

Read-only native selected metadata capture19:23:45UTC provides a fresh seven-
original baseline: full selected observations equal across two reads; same IDs/
images/running/configured fingerprints, storage snapshots unchanged, known app
startup/raw-network changes preserved. Legacy collector's INCOMPLETE/exited-
expectation flag retained and separately interpreted, not rewritten. Sandbox
signature/socket failures did not establish daemon damage; same CLI hash and
native codesign verification passed. No service lifecycle or credential values.

New v6c input proposal changes attempt/cleared approval/baseline only, preserving
four application specs/43sources/policies/options/commands/modeled predictions.
Separate GATE ACCEPTED_WITH_RISK preparation-input scope, no blockers,9tests0.23s.
Review `fresh_preparation_v6c/independent_review.json` SHA
`6bcf752e347ecae8ebfa42f8863701195025a9bed0e7e2ffadae04e4d64584ad`;
accepted derivative SHA
`e20775accd2ea02ac16d258ead2fb58e5ba1b6d26ff003ba10492dc6d442b6b9`.
Parent read complete review, verified23bindings and two-field derivative, default
inert CLI exit0/actionsfalse/startupfalse with backend/native/reservation/lock
tripwires. Receipt `fresh_preparation_v6c/inert_validation_receipt.json` SHA
`b0a68090c6fff111344ba389815fe9aa9562eaffc9d1551369bdfe94cdbdfb1d`.
These folders are under companion_worker_preparation_20261023.

No actual stopped preparation/build/create, credentials copy, startup/query or
cutover authorized/executed. Runtime INCOMPLETE. Next explicit boundary: ONE
existing preparation run,300s controller including120s recovery, four COPY-only
images/four never-started new IDs, private existing credential configuration,
originals/storage untouched, owned-new-stage cleanup on failure only. New-ID/
source/alias review follows; cutover remains separate. No retries/old-marker reset.

## Actual V6c Stopped Preparation Accepted, October 23

The operator subsequently approved the exact one-run stopped-preparation scope.
Existing companion_prepare ran once, session93011/exit0; evidence9f52a511...dfb9,
receiptf4ddc5d5...835c. Four new created/never-started IDs were prepared using
cached immutable images; seven original snapshots remain equal to the baseline.
No original interruption or service startup. Attempt v6c is consumed for
preparation and must not be rerun/reset.

One bounded read-only postcheck (46reads,2.858s) verifies11selected raw rows equal
before/after, actualstage snapshots equal controller evidence and43source hashes
equal frozen/local sources. Temporary stage aliases observed exactly; four final
configured projections match but remain MODELLED. No final attachment/health/query
or volume-byte proof. Details frozen in companion_v6c_preparation_result_20261023.md.

Separate GATE ACCEPTED_WITH_RISK actual-preparation scope only, no blockers.
`actual_c/independent_review.json` SHA
`2bec57b4fdb612dc3f75627071c0beaf3274670bc3a648d2e16a8231f70dc092`;
five-field `actual_c/actual_id_review.json` SHA
`f2b926136e5503d9310ec88b0f881c82c8292a92dc4ffcb5e78c97cfac54946e`.
Parent read non-repetitive review in full, verified24boundhashes and checked all
7original/4stage/43source repeated records programmatically against saved data.
Existing pure ReviewedPreparation loader passed with native calls forbidden;
`actual_c/loader_validation.json` SHAcc55b26527e7b457643ff35f2c659be6258f821005457de7fcb28f29591ee58d.
Folders are under companion_worker_preparation_20261023.

Preparation scope complete ACCEPTED_WITH_RISK; runtime INCOMPLETE. Next is offline
V2 runtime-packet assembly and policy applicability review, not another native
preparation or automatic cutover. Exact final network configuration/startup and
one genuine cited-evidence query still need later separately bounded approval.

## Offline V6c V2 Packet Accepted And Inertly Validated

Versioned assemble_runtime_packet_v6c.py produced twelve drafts from accepted
actual_c IDs, retaining three storage subjects, all seven images/source maps and
132pins. Four app IDs/configured V2 preservation pins updated using the accepted
shared final-model helper.43direct new-ID witnesses/89inherited same-image/storage
pins remain explicit; four launcher pins are historical inheritance, not newly
captured on v6c. No production-source or native operation in packet assembly.
Parent14focused tests passed0.32s; separateGATE14tests passed0.46s and reconstructed
all12drafts. Actual attachment/aliases remain MODELLED; runtime INCOMPLETE.

Independent restricted source/configured-policy acceptance ACCEPTED_WITH_RISK,
no blockers. Review runtime_packet_v6c/independent_review.json SHA
`313af3aa86100b223ed10da2cd0fbe16ca417cb7bc3fbde07dd7bc0de5c2beb2`;
scopeSHA`76f3e5f8f8a788f2b683bc01be58c42a0489e413476120abd062aa28c6927935`;
runtimeSHA`f916471d3618eb5a44bc8bf00ac6421aa3e941febab431b8a1c49fd65daddb74`.
Parent read compactreview/currentper-subjectscope rationale/limits, verified61
artifact/support/currentconsumer/childhash bindings, exact derivative changes,
scopehash in all8acceptedreviewer fields, and unchanged policymeanings/sevenlimits/
per-subjectpolicies/risks/support. No blanket image or zero-physical-retry claims.

Existing actual default companion_cutover.main against accepted records exited0,
input_bindings_validated=true,actions_executed=false,startup_authorized=false.
Native/backend/token/lock/reservation calls patchedforbidden. Exactargv/results
and61bindings saved runtime_packet_v6c/inert_validation_receipt.json SHA
`0767f631cd59f9656322b963a185b23c19d528260fc8a42ba1def98e3a8b18cf`.
No fullsuite, private token read, daemon action, new receipt reservation or query.

Offline packet scope complete ACCEPTED_WITH_RISK. Runtime/explanation remains
INCOMPLETE. Next: fixed bounded v6c handoff, then its separate review and explicit
operational authorization before original-app quiesce, activation/startup/query.
Old wrappers are bound to consumed old attempts/records and must not be rebound.

## Fixed V6c Handoff Independently Accepted

Added separate execute_reviewed_v6c.py, SHA
`6908501b0cf0c0c26c70f72b6d8e14ef8492cd6536a8bf2ef3822360e0eb2393`.
No production/controller/accepted packet or old-wrapper change. Reuses only the
SHA-pinned generic private-token/pipe/parser helpers without invoking old inputs
or execution. New wrapper binds exact V6c V2 receipt/review/scope/subject table,
current13consumers, worker plan and132pins. Default is inert; execution branch
requires separately authorized --execute-once, unused cutover marker, pinned CLI,
one exact-original token source and existing private pipe/controller.

Parent23synthetic tests passed0.31s; actual default module exit0/actionsfalse/
startupfalse/inputbindingsvalid. Saved handoff_inert_validation.json SHA
`91c6e302b2e2480eb28b939c8f40fcec03cf787b56ca4757f5e94cd4945dceaa`.
Separate GATE ACCEPTED_WITH_RISK offline handoff only, no blockers,23cases passed
0.29s. Review runtime_packet_v6c/handoff_independent_review.json SHA
`c4ff10fb24cabfc7467d5d39a624dcfa6182f3726dec5ee3d0a51f1cef629831`.
Parent read complete review and verified36bound artifacts/current consumers.
Reviewed source/tests/checkpoint/packet unchanged. No actual token/native source,
receipt reservation, service action or query in this scope.

Runtime remains INCOMPLETE; ready only for explicit decision on ONE future actual
attempt: private internal token reuse, four original research apps graceful
quiesce/rename/detach, four existing prepared apps activation/start, existing
checks and one cited archived-evidence query. Three storage/volumes/trading stay
untouched. Controller600s includes180recovery; pre-controller CLI/source10seach
separate, no whole-wrapper deadline. Owned cleanup/original restoration attempted
on failure, not guaranteed healthy rollback; logs/audit effects may persist.
Only all-checks/query/receipt success leaves replacements running. No automatic
retry, reset, preparation or old-ID adoption. No operation is authorized here.

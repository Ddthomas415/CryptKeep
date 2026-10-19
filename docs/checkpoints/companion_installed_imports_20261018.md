# Isolated installed-interpreter import proof

Date October18 New York. Active role ENGINEER; risk HIGH (temporary-container
lifecycle). Implementation handoff READY_FOR_INDEPENDENT_REVIEW. Installation
and explanation runtime remain INCOMPLETE.

## Authorized objective and preservation

The operator continued the specific proposed next step: create/run/remove
temporary network-disabled import-test containers from the four existing
application images, synthetic settings, no credentials, existing data volumes or
published ports. This is not permission to start the seven original services,
install applications, change storage, trade or create a background collector.
One bounded attempt only after independent preflight and tool permission.

The runner is inert by default. Direct-script execution requires --execute and
the approved runner hash. Before Docker, it checks CLI31ae2d64..., exact baseline
85d226fc..., source manifest973da853..., archive/member hashes and payload bytes.
It uses only stdlib imports; no repo package initialization in direct invocation.
Four source stages contain exact application Python files plus the diagnostic,
not the198-file repo inventory, .env or any actual account/storage data.
All earlier artifacts and application sources remain unchanged.

## Isolation and commands

All four immutable parent images must match the baseline and declare no volumes
or LD_*/GCONV_PATH loader environment. No raw image/container Env is exported.
Each random name must be specifically absent before create. One test per image:

-create --pull=never, --network none, --read-only, --no-healthcheck;
-unprivileged65534:65534, cap-drop ALL, no-new-privileges, pids64, memory512MiB,
 cpu quota1, restart no, no published ports or Docker socket;
-one readonly bind of newly staged public source, and an ephemeral16MiB /tmp
 tmpfs with noexec/nosuid; no preexisting data mount or existing /repo mount;
-explicit /usr/local/bin/python -I -S -B /frozen/import_check.py MODULE,
 bypassing Python env/site/.pth/customization hooks and parent entrypoint;
-start --attach only the confirmed test-owned created ID; no uvicorn, server,
 service lifespan, health check, database call or model request;
-remove only that proven test-owned created/exited container, without force or
 volume flags, and verify its name absent. Never stop/remove an original ID.

The payload clears inherited image environment, inserts only the frozen source
and installed Python3.11 site-packages, blocks socket connect/DNS/bind/listen
and repository imports, and applies a12-second alarm. Synthetic settings use
model_construct rather than reading .env/credential providers. Actual dependency
imports and compiled extensions are not mocked. Each loaded internal module must
come from frozen source and hash-match. No source hook/network attempt may be
silently caught and still yield success. The ordinary dashboard capability is
not removed; it is not exercised in this restricted import smoke test.

Deadlines:180seconds for commands,150work plus30cleanup reserve; default command
10seconds, attach20seconds capped by remaining time. On failure, capture only
safe stage/exception/module identifiers before cleanup; no arbitrary stderr,
exception messages or sensitive payload. Output size is checked after capture,
not a streaming memory bound. Stop with time1 only a proven owned test if still
running, then inspect and remove only when stopped. Ambiguous ownership or a
failed cleanup ends INCOMPLETE, not a forceful global cleanup or retry.
Daemon cancellation is not proved by CLI timeout. The temporary public source
and receipts remain for diagnosis even if a test object cannot be removed.

## Offline proof and frozen hashes

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_companion_installed_imports.py
```
SHOWN:9 passed0.42s. Covers four successful mocked lifecycles, wrong hash/no
calls, unsafe image volumes/loader env, unknown ownership/no destruction,
timeout owned-only cleanup, failed import diagnostics before removal, changed
original inventory and a host-child missing-import control. The latter runs
only the payload with -I/-S in a fresh directory; it does not certify installed
Python3.11. No full suite or actual temporary container used in this proof.

```text
runner scripts/research/prove_companion_installed_imports.py 761aa1e0322031cd11bb7bb3fd5e51169462ba5f0d54816192bd4ab6874453fa
payload scripts/research/companion_import_payload.py e2fad272202a6d9041a0ebe0afb2d9b8f254046d37a490366adc5d332b97f192
tests tests/test_companion_installed_imports.py 05a3b2e6585daa34bd5966f7f411c21b8d4a174e8574864b1fce7f141aa76762
```

Only after preflight and permission:
```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
 scripts/research/prove_companion_installed_imports.py --execute \
 --approved-sha256 761aa1e0322031cd11bb7bb3fd5e51169462ba5f0d54816192bd4ab6874453fa \
 --output docs/review_artifacts/companion_installed_imports_20261018
```

## Acceptance and limits

Four Python3.11 module imports must pass under synthetic settings, loaded source
hashes must match the frozen manifest, all test containers must be removed and
the seven original snapshots must match. This verifies restricted module
initialization, not ordinary repository intelligence, actual SDK connections,
lifespans/storage namespaces, credential wiring, installed four-app replacements,
complete runtime policy or a persistent cited explanation.

At most two material assumptions: trusted CLI/daemon semantics for the pinned
images and flags; no adversarial same-user mutation/restoration of the unique
staged source during execution. Hash checks do not authenticate a hostile host.
No operational policy is auto-approved by a hash or synthetic success. A failed
actual run is diagnostic evidence, not permission for dependency installation,
package upgrades, another run or changes to existing services.

## Independent preflight

Separate AUDITOR ACCEPTED_WITH_RISK the exact frozen preflight, no concrete
blocker for the permission-checked single attempt. Independently9 passed0.39s;
verified runner/payload/test, CLI/baseline/manifest/four archives and all43
application source records; confirmed default inertness and ownership-before-
lifecycle boundaries. No Docker or credential access by reviewer. Daemon
enforcement, actual imports and timeout cleanup were not established offline.
Tool permission then allowed this named attempt; no broader installation,
original-service startup or retry was authorized. Frozen code/tests unchanged.

## Actual attempt: INCOMPLETE

Executed exactly once under the named tool permission at
2026-10-18T08:39:57.887637UTC (October18 04:39:57 New York). No repeat.

| Image/module | Actual outcome |
| --- | --- |
| audit-log / audit_log | PASS: Python3.11, synthetic settings, frozen internal source hashes, no guard hits |
| risk-stub / risk_stub | PASS: same scoped checks |
| memory / memory_retrieval | INCOMPLETE: child exit1, RuntimeError at source_validation |
| orchestrator | Not attempted after memory failure |

The memory module reached source_validation, so this is NOT evidence that a
package was absent or that module import itself failed. The original payload
only emitted the exception type, and the parent did not retain its denial
counters on a failed child. Therefore the specific failed validation condition
(origin check versus activity/deadline guard) cannot be recovered from the saved
receipt. No missing-dependency, network attempt, benign feature probe or service
failure is asserted as its cause. No acceptance condition or guard was loosened.

All three created test containers were removed with name-absence confirmation.
Selected original seven snapshots match, all exited/restarts0/policy no.
No test left running, original service startup, private config access, image
build, account/schedule/strategy/capital/trading change or dependency upgrade.
The runner issued28 calls, all within the approved inspect/create/start/rm
temporary-test scope. No stop command was needed in this actual run.

Receipt SHA256:
223c7217573492834555adb25df74e0b8df942c693e66ec2b8c63d73089e0097.
Executed source snapshot `executed_sources.tar` SHA256:
a8804000ba854faaee1c17205358f398b8685316d6d06204e6f0c5461569659b.
Both are in `docs/review_artifacts/companion_installed_imports_20261018/`, with
the frozen public application stages. Source snapshot contains the original
runner/payload/test matching the preflight hashes above, not the later repair.

## Offline diagnostic correction, not a retry or memory fix

Added one regression for a source-validation failure: it failed on the executed
runner because the category was discarded. The payload now exports only fixed
whitelisted RuntimeError categories; the runner retains those plus strictly
bounded network/repository denial counts before cleanup. No exception messages,
raw stderr, guard/lifecycle/acceptance changes or additional operational calls.
The original9 tests had no such validation-failure diagnostic assertion.

Current offline hashes (not the executed snapshot):
```text
runner 85515300864d4eaa988915800a4ebdfef124e0d3b8d3bb759e838e122a2ea279
payload ec5ca30f3e39a7e49e5327becccd6e3fae875909e7e413fc5380757312886b64
tests dea851d6ca7e15430789110c8d14037006265771e68f2aa5e9153b1d8533b136
```
Same narrow pytest command:10 passed0.42s. This proves diagnostic retention in
fixtures, not resolution of memory validation or completion of installed imports.
The old execution command/hash above is historical and will now refuse current
source; it must not be reused or silently treated as authorization for another
attempt. Separate review covers this narrow correction and the saved failed run.

Next affected operational decision: a further bounded memory-only diagnostic,
followed by the unattempted orchestrator test only if justified, needs explicit
authorization and an exact reviewed selection. Do not repeat the two passing
images just to make a new aggregate count. No further Docker attempt occurred.
Overall restoration and complete installed-import acceptance remain INCOMPLETE.

Separate post-run AUDITOR ACCEPTED_WITH_RISK the saved failed-attempt evidence
and current diagnostic-only delta, no actionable findings. Independently10
passed0.44s plus narrow synthetic category/suppression controls; checked executed
snapshot hashes, two passes, memory failure, unattempted orchestrator, three
removals and seven unchanged selected snapshots. No new Docker or network call
by reviewer. Exact historical guard/root cause remains UNVERIFIED; corrected
diagnostics cannot reconstruct omitted old counters. No reviewed code, tests,
receipt, frozen source or executed snapshot changed after review. No retry,
complete installed compatibility or runtime acceptance follows.

## Authorized targeted continuation

Operator requested the next steps after the explicit memory-first proposal.
Added `--remaining-only`: selected modules are memory_retrieval, orchestrator,
in that order, with the existing stop-on-failure behavior. No audit-log/risk-stub
import or parent image inspection is repeated in this mode. Static source pins
and the seven-original before/after inventory remain mandatory. The receipt
states selected_modules; success applies only to this selection. The runner
now saves its executed runner/payload source archive before Docker calls.

Frozen runner SHA256 ba0ecfb2d1b2528af6193a88dfb6ef935d91280284214faaa79918b8506b61c3;
payload remains ec5ca30f3e39a7e49e5327becccd6e3fae875909e7e413fc5380757312886b64;
tests SHA256 3956761056b2922e9cdb44fede45a028e97edeccc80168226f431cc7685031b8.
Offline18 passed0.87s using the same isolated pytest command. An initial order
assertion exposed synthetic container-ID reuse in the fixture; assigning unique
fixture IDs corrected it. No actual Docker action occurred during those tests.
Guards and payload unchanged. Separate preflight requested before the single
permission-checked invocation; no automatic second attempt if memory fails.
Existing-service restoration remains INCOMPLETE.

## Targeted actual result: INCOMPLETE

Separate AUDITOR preflight ACCEPTED_WITH_RISK, independently18 passed0.53s;
tool permission allowed one exact --remaining-only invocation. Executed at
2026-10-18T08:53:23.592475UTC (04:53:23 New York). Memory imported far enough
to reach source_validation, then reported RuntimeError, fixed category
forbidden_import_activity, denied network=1/repository=0, CLI/child exit1.
Orchestrator was not attempted; the two historical passing modules were not
rerun. No guard or acceptance condition was relaxed and no second attempt ran.

SHOWN: one guarded socket operation was attempted and denied. The counter
combines connect, connect_ex, bind, listen and getaddrinfo; it does not identify
which operation or caller. An import-time IPv6 feature probe is one possible
explanation, UNVERIFIED, not a diagnosed cause or permission to bypass checks.
This is not proof of outbound traffic, attempted credential access, a missing
package or an actual service startup failure.

The only created helper was removed, with name-absence confirmation. Seven
selected original snapshots before/after match, all exited/restarts0/policy no.
12 CLI calls; no original start/stop, build, pull, package change, private config,
account, schedule or trading action. Cleanup was complete within this attempt.
Receipt and executed runner/payload preserved at
`docs/review_artifacts/companion_installed_imports_targeted_20261018/`:

```text
receipt.json ca22ca6956e94a2eb4753fb6d0c28fa114db4711435e38ff2dad44695474f7da
executed_sources.tar 1a003187b22de4ee358b415c929e54b37ee17b780f673f6b63a380d767aca33e
```

Next narrow engineering gap: capture a fixed operation identifier and sanitized
caller attribution for denied calls without relaxing guards, then independently
review before seeking any further actual attempt. No automatic retry or
existing-service authorization is inferred. Overall import proof and restoration
remain INCOMPLETE. Saved evidence submitted for separate review.

Separate AUDITOR ACCEPTED_WITH_RISK the saved targeted evidence, no discrepancy.
Verified both artifact hashes, archive byte identity with reviewed sources,
12 recorded calls, one owned removal/absence confirmation, exact seven-original
selected snapshot match and memory failure details. No independent Docker call
or retest; daemon observations rely on saved runner evidence. Exact operation
and caller remain UNVERIFIED. No further operation authorized by this review.

## Caller-attribution diagnostic preparation

Operator continued the stated next step: identify the blocked caller without
weakening guards. ENGINEER added separate blocking wrappers for connect,
connect_ex, bind, listen and getaddrinfo. Every call still increments the denial
counter and raises without invoking the original socket method. Up to eight
events retain only fixed operation plus syntax-checked module/function identifiers
and bounded line number. No arguments, addresses, local values, file paths,
environment values or raw traceback. Parent validates the exact bounded schema
before preserving events in the failure receipt ahead of cleanup.

No import rule, success condition, lifecycle/ownership/cleanup, deadline or
synthetic-settings change. Historical receipts/source archives remain unchanged.
Targeted27 passed0.74s, including five operation identifiers, suppression of
synthetic private arguments, event cap and rejection of malformed/extra fields.
These are offline fixtures, not installed caller attribution.

```text
runner ae6efd619b1804cd1a101204d2a49eb71ac45fc98e32ec30b08264850a2c446b
payload 2e110e7a1dcd9a0b1f66f157b4a4d4063c24a2520fc179c6d984feee5327aafe
tests f83bf79331a35ebd82eb63e75b2c60db6e6065c496fbb9b62a5ee57be8c6e4fd
```

READY_FOR_INDEPENDENT_REVIEW. Proposed operation after review is exactly one
permission-checked --remaining-only invocation into a new attribution artifact
directory: memory first, orchestrator only on pass, no repeat of passing modules,
no automatic retry. Same network-none/readonly/non-root/synthetic/no-lifespan
scope, existing source pins and seven-original inventory. No existing services,
packages, credentials, accounts, scheduler or trading changes. Interpretation
must distinguish a blocked library feature probe from actual outbound activity;
attribution alone will not justify bypassing the check. Restoration INCOMPLETE.

Independent AUDITOR blocked the initial attribution delta: success results
still expanded the raw payload, so rejected malformed event fields could be
retained there. Offline probe demonstrated the defect with nine records carrying
an extra private marker; no actual secret access or Docker action occurred.
Corrected success handling to require empty validated events alongside zero
denials, and serialize only explicit validated result fields. Added the reported
success-path regression in both selection modes.29 passed1.16s. Re-review
requested; no actual attribution run yet. The initial27-test/hash record above
is superseded for current execution, not erased.

```text
runner 66759d5e62a82c9f31dac1127887a4c816250c2e704b03d6b55108b87eacd2e5
payload 2e110e7a1dcd9a0b1f66f157b4a4d4063c24a2520fc179c6d984feee5327aafe
tests f0819147b15b5f1a0a2b4ff22a5b1f36c4009552c6404b5a813b6ebf8cdb14dc
```

## Actual caller identified; restoration still INCOMPLETE

Separate AUDITOR re-review ACCEPTED_WITH_RISK the correction and narrow
preflight; independently29 passed0.69s and reproduced rejection of malformed
success events in both modes. Tool permission allowed one attribution invocation
at2026-10-18T08:59:45.087451UTC (04:59:45 New York). No automatic retry.

SHOWN by retained caller diagnostics: memory reached source_validation, with
one denied socket operation, `bind`, called by
`urllib3.util.connection._has_ipv6`, line127. No denied repository imports.
The application import returned before the validation guard rejected the
recorded operation. No missing dependency is shown. Orchestrator was not
attempted, and audit-log/risk-stub were not rerun.

The function name points to an IPv6 capability check, but the exact installed
function body and attempted address were not captured. Do not claim its address,
successful network traffic or a production service failure from this receipt.
The existing strict zero-denials rule intentionally still rejects the call;
no guard, success condition or classification was changed to pass this run.
The diagnostic attribution objective is now complete; full installed-import
compatibility and the usable explanation objective are not complete.

One created helper removed with name-absence confirmation. Seven selected
original snapshots match, all exited/restarts0/policy no.12 CLI calls. No
existing-service startup, package changes, image build/pull, private config,
account, scheduler or trading actions. Original failure artifacts preserved.

Artifacts at `docs/review_artifacts/companion_installed_imports_attribution_20261018/`:
```text
receipt.json a0ef66c290b3f5436e847bcabd36aa3051d2f4e370a5fa87a050613ab771a962
executed_sources.tar d142066a44e2de9b53fa7cbe97838652a90a363f6c53d827e78a84ebd802ee83
```

Next decision is the import-test contract for denied local capability probes,
not an unexplained dependency upgrade or repeated diagnostic. Before any such
contract change, verify the exact installed caller code and distinguish it from
outbound connection/DNS attempts. Preserve rejection of actual egress attempts.
Any changed success criterion requires explicit review; no further operation
or original-service restoration is authorized by this result.

Separate post-run AUDITOR found no discrepancy: both artifact hashes and
archived code match, all43 staged source records match the manifest, exact
caller attribution and12 recorded calls agree, one owned helper removed and
seven selected original snapshots unchanged. No independent daemon inspection
or retest; cleanup/state conclusions rely on retained runner evidence. Narrow
ACCEPTED_WITH_RISK evidence disposition unchanged; runtime remains INCOMPLETE.

## Installed caller source inspection

Operator continued the specific next action, verifying the caller before any
acceptance-rule change. AUDITOR performed one bounded, permission-checked
read-only collection: seven-original metadata check, two single-file source
archive reads, final metadata check. No create/exec/start/stop/remove, package,
configuration, credential or service-query action. Four Docker calls total.
Both selected files were regular tar members, statically parsed but not imported.
Seven selected original snapshots match before/after and the pinned baseline.

SHOWN: both stopped containers carry identical urllib3 connection.py bytes,
SHA2562633bbdb69731e5ccb5cf4e4afd65605d86c7979cc5633126f50c92d5ad74a74.
At lines114-138, `_has_ipv6` creates an AF_INET6 socket, attempts bind(host,0),
catches exceptions and closes the socket. The module calls `_has_ipv6("::1")`.
Line127 matches the prior observed blocked bind. There is no connect, listen,
send or DNS operation within this function. The static call is a localhost IPv6
capability test, not an outbound request. Our blocking wrapper prevented the
bind and recorded the denial; urllib3 catches the error and selects false.

UNVERIFIED: copied stopped-container filesystem bytes are not proof of immutable
parent-image-layer equality or the exact bytes loaded in the removed helper.
The prior runtime caller identity/line and matching static source support the
capability-probe diagnosis, but the actual call arguments were intentionally
not recorded. No claim of observed address, full egress tracing or readiness.

Source bodies/raw archives and receipt preserved at
`docs/review_artifacts/companion_ipv6_source_20261018/`.
Receipt SHA2562732598d34c2e3c227bafd34325590732889362453a9898a54b35df51163f8c7.
Tests not rerun: no executable source, guard or acceptance criterion changed.
Read-only evidence submitted for separate review.

Recommendation: preserve the actual socket denial and classify only an exact,
verified localhost capability probe separately from attempted external activity.
Before implementation, the revised contract must pin the code/caller and exact
loopback/ephemeral-port arguments, report the blocked probe visibly, and continue
to reject other bind/listen/connect/DNS/repository attempts. Do not whitelist
the whole library or merely its function name. Alternative: retain zero-denials
and report imports as incomplete; no package upgrade is justified by this finding.
This is a proposed test-contract correction, not implemented or authorized for
execution here. No new import attempt or existing-service restoration occurred.
Explanation runtime remains INCOMPLETE.

Separate AUDITOR ACCEPTED the bounded source evidence, no discrepancy. Verified
receipt/source/archive hashes and bytes, AST/function lines114-134, bind at127,
module invocation at137, and seven matching selected snapshots. Socket close
is conditional after the catch, not in finally. Recorded read-only/zero-lifecycle
claims are consistent with the receipt, not independently recollected. Actual
loaded-byte/image identity and orchestrator imports remain UNVERIFIED. No tests,
Docker calls or collected-source execution by reviewer. No criterion change,
retry or readiness authorized; next proposed contract needs explicit review.

## Optional blocked-local-probe contract: offline implementation

Operator continued the proposed narrow classification review. ENGINEER risk
HIGH implemented an explicit `--allow-blocked-local-probe` option; without it,
the previous zero-denials contract remains the default. No actual invocation,
container inspection/startup, package change or service query in this scope.

Chosen consequence: distinguish one exact blocked IPv6 capability probe from
disallowed import activity without allowing the socket operation. Recognition
requires every condition below at the moment the wrapper is called:

- first socket denial only, operation bind and no keyword arguments;
- actual socket instance, AF_INET6 and SOCK_STREAM;
- exact two-element tuple, string ::1 and integer port0 (not boolean);
- urllib3.util.connection._has_ipv6 at line127 and the exact installed filename;
- source path resolves without redirection, at most64KiB, exact source SHA256
  2633bbdb69731e5ccb5cf4e4afd65605d86c7979cc5633126f50c92d5ad74a74;
- caller code object equals the function compiled from those verified bytes
  using the current interpreter/optimization, without executing the source.

Any verification error returns unrecognized/fatal. Wrapper still increments
network denial and raises; the original bind is never called. A recognized
event stays visibly recorded with fixed classification and source hash, and
network=1 is retained rather than rewritten to zero. Deadline and repository
checks remain. Later probes or any additional operation are fatal.

The parent records import_contract=zero_denials_v1 or blocked_local_probe_v2.
Opt-in accepts either zero events/zero denials, or exactly one exact classified
event/network1/repository0; malformed events, boolean counters, repeated/mixed
attempts or a mismatched child mode are rejected. Explicit validated result
serialization and owned-only cleanup unchanged. This changes the optional test
acceptance contract, not production permissions or the historical failed runs.

Targeted57 passed1.48s with isolated pytest --noconftest -c /dev/null. Positive
fixture executes only the pinned function under a blocking wrapper in a clean
host subprocess; negatives cover strict mode, wrong host, changed source/code,
repeated probes, other operations, mixed denials and malformed diagnostics.
Container behavior remains mocked; Python3.12 fixture proof does not establish
installed3.11 behavior. No full-suite run or import smoke test repeated.

```text
runner d4f575b8ed6dceb392ad1ecd381a449772397599ce0f4f9fe5791315b90ea3eb
payload c62e27b04494eb5dab51fc7d72c3403ea44cec7c72ab5267c4c5dc5c20888a13
tests 8b8725cc70c55132300f4d685b15fb5ad801e61db0eda0579bb5aa733d4a490b
```

Submitted frozen code/tests for independent review. Handoff
READY_FOR_INDEPENDENT_REVIEW; no new actual attempt is authorized by this
implementation. Original services, credentials, schedules, account/trading
state and earlier artifacts untouched. Runtime restoration remains INCOMPLETE.

Separate AUDITOR ACCEPTED_WITH_RISK the three exact hashes above and optional
offline contract, no actionable findings. Independently57 passed1.48s on
Python3.12.10; checked strict-default behavior, source/code/caller and endpoint
constraints, denied-call retention, repeats/mixed activity, explicit parent
serialization and unchanged remaining-only/lifecycle guards. No Docker,
credentials, services or network operations by reviewer. Actual installed3.11
behavior and operational readiness remain UNVERIFIED.

Next execution boundary, if separately authorized: one permission-checked
`--remaining-only --allow-blocked-local-probe` attempt with the reviewed runner
hash and a new exclusive artifact directory. Memory first, orchestrator only
on pass; do not repeat audit/risk, change packages, weaken other guards, start
existing services or automatically retry. Independent offline acceptance does
not itself authorize that attempt. No actual invocation occurred in this step.

## Actual remaining-only v2 import proof

Operator requested the listed next steps in one pass. Tool permission allowed
one remaining-only opt-in attempt on the exact independently reviewed source
hashes above, at2026-10-18T09:23:28.233417UTC (05:23:28 New York).

SHOWN: memory_retrieval and orchestrator both completed actual Python3.11 module
initialization, synthetic settings identity and frozen internal-source checks.
Memory recorded one denied bind, classified using the exact verified source,
caller code and localhost/port0 conditions; network1/repository0 is retained.
Orchestrator recorded zero denied operations and no events. Neither ran its ASGI
lifespan. No repository import or guarded socket call was permitted.

Both temporary helpers removed/absence confirmed; seven selected original
snapshots unchanged, exited/restarts0/policy no.18 recorded Docker calls. No
audit/risk rerun or automatic retry. No package/build/privateconfig/account/
schedule/trading or existing-service lifecycle action. Prior strict failure
receipts remain intact; v2 does not rewrite them as historical passes.

Artifacts in `docs/review_artifacts/companion_installed_imports_probe_v2_20261018/`:
```text
receipt.json 526fcd3f6e8fe42f1a3a7e3cc525b63ae045499c48b7452e5a35399fe054df64
executed_sources.tar 63333917d718b7470917c8b3d1e1ca5b309c92a013c3b54d8e3238e3d9fca314
```

This closes the restricted installed-import check for the two unfinished
modules. Audit/risk retain their earlier strict-v1 passing evidence, not a new
homogeneous four-app v2 run. SDK connections, real configuration transfer,
normal/lifespan initialization, namespace existence, installation and genuine
cited explanation remain UNVERIFIED/INCOMPLETE. No executable installation
manifest or blanket policy acceptance is generated from this result.
Saved-evidence review requested; no executable source changed.

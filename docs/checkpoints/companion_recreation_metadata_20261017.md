# Read-only recreation metadata reconciliation

Client date: 2026-10-17, America/New_York. Active stages: ENGINEER for the narrow
collector, AUDITOR for recorded metadata. Risk HIGH. Implementation handoff:
READY_FOR_INDEPENDENT_REVIEW; executable installation and runtime INCOMPLETE.

## SHOWN

Successful observation at 22:48 New York (2026-10-18T02:48:04 UTC): seven pinned
original IDs/images remain exited, restart count zero, policy no. The two
successful selected inspections match exactly. No Docker mutation was invoked.
Equality was computed by the collector; only the first observation payload was
retained. The second payload cannot be compared independently from these files.

Captured actual StartedAt timestamps, selected preservation metadata, named
mounts, network IDs/aliases/IPAM, loopback ports and known health-check commands.
All seven share network ID
`dc3185b57a728053adc6a25d10baf81fcf9a271bd7cc86df6414807fc0fb2d56`.
Original application aliases contain the container name and service alias; IPAM
configurations are null. App ports are 8009/8008/8007/8002 on 127.0.0.1.
App health checks run every 10s, timeout 5s, retries 10. Their logging driver is
local, without logging options; no selected capability/device/security/ulimit/
sysctl/tmpfs exceptions were found. App user is empty, workdir /app, command
matches the existing uvicorn wrapper. These are selected facts, not exhaustive
container reconstruction certification.

Orchestrator PYTHONPATH matches /app:/repo. Its /repo bind is read-only. This closes
the prior missing effective-path comparison, not import isolation or host-write
protection. BASH_ENV and ENV variables were absent in all seven inspected
environments; this observation does not remove the defensive bash -p requirement.
Container labels count 11 per application; arbitrary label values were deliberately
not exported. No raw environment, credential value or credential hash was saved.

Seven baseline/foundation fingerprints were derived and independently recomputed
locally from the selected observations. A new reconciled review manifest records
the actual baseline snapshots, four observed app configurations and restore alias
options. The old source bundle remains unchanged. Correctly hashed reconciled
bytes are still refused by the executable installer: no fabricated review or
all-true policies, installation_authorized false, non-executable schema retained.

## Commands, verification and diagnostic history

Final successful command:
```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
 -m scripts.research.collect_companion_recreation_metadata \
 --output docs/review_artifacts/companion_recreation_metadata_20261017/capture4
```
Explicit local socket, pinned native CLI hash, empty temporary Docker config,
10s per selected-inspect operation, no retry within a capture invocation.
Unknown command/entrypoint/health text is withheld at the daemon formatter; raw
environment and labels are never JSON-exported. Comparison fields are booleans.

Preserved earlier receipts: initial call failed before Docker because input_bytes
was omitted from the local transport interface. capture2 returned a generic
Refused failure; diagnostic3 identified the formatter's missing optional
HostConfig.Init key. Corrected the argument and signature-matching fixture;
diagnostics export only fixed categories and whitelisted template expressions.
Optional Config/HostConfig lookups now use map indexes. No authentication or
service repair is claimed. These local capture defects were not detected by the
initial four tests; the later live read and corrected tests provide distinct proof.

Final targeted verification:
```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_collect_companion_recreation_metadata.py
```
SHOWN: 6 passed in 0.20s. Additional offline assertions recomputed all seven
fingerprints and verified executable-loader refusal. No full suite, service
execution, namespace query or installed import resolution test.
The separate offline template_alignment.json also binds observation/source hashes
and confirms all four declared port mappings and health test/interval/timeout/
retry definitions match the recorded runtime metadata. This is not full config
equivalence or proof that those health endpoints currently respond.

## Remaining boundary

VERIFIED_ENV: installed CLI and selected current metadata, plus offline Python
fixtures. UNVERIFIED: full replacement creation contract. In particular, label
ownership/preservation is not established by counts; observed local logging is
not pinned by the current create-option allowlist; exact replacement mount/alias
serialization and its preservation digest are not observed facts. This does NOT
prove the replacement would differ; it identifies what is not yet established.
Source imports/SDK policy and strict registry isolation remain separate limits.
The adapter fingerprints cover its existing selected fields, not every newly
recorded user/resource/privilege/logging or environment-comparison field.

Next bounded scope: complete and test the stopped-replacement recipe against this
captured configuration, preserving the existing service/mount capabilities.
Do not replace, start or query services while preparing that offline correction.
No blanket re-audit or new framework is required. Runtime remains INCOMPLETE.

## Independent review

Separate AUDITOR: ACCEPTED_WITH_RISK for selected nonsecret capture and offline
enrichment only; independently 6 tests passed in 0.24s. It recomputed all fourteen
selected digests and verified actual IDs/images/states, enrichment and alignment
bindings against the original source manifest/archives. No Docker/network or
credential operation by reviewer; no blocker in this saved artifact.

Accepted P2 reuse risk: reconcile_manifest trusts receipt flags and supplied
snapshots rather than rechecking baseline identity and recomputing digests itself.
This artifact passed the independent checks, but the helper is not a trust gate
for future operational input. Add those validations before operational reuse.
No source/test/artifact edits followed review; only this disposition was added.

Artifacts under `docs/review_artifacts/companion_recreation_metadata_20261017/`:
```text
capture4/observation.json SHA256 13c51c9f49a1e16cd767e2f51d21c84d045f31e210d238f67fc9c7909d55a78f
reconciled_manifest.json SHA256 2966c5636094f2d08971bd6a10230d7a0fa6794a5b58ba4e007e4517b4878773
```
Source SHA256:
```text
collect_companion_recreation_metadata.py 3111d64de8ef69ec8bf0c21b959e0fb1389d93c4a92fc217cec8c580df350055
test_collect_companion_recreation_metadata.py a3401b298700a661028a1b04e009db884ffd381b2bd1fb364ca1ebbc601a4d82
```

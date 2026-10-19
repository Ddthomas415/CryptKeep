# Stopped-replacement recipe implementation

Client date 2026-10-17. Active role ENGINEER; risk HIGH. Implementation handoff
READY_FOR_INDEPENDENT_REVIEW. No installation, replacement or startup authorized
or performed. Explanation runtime remains INCOMPLETE.

## Implemented

Four review-only recipes now specify the observed loopback ports, health command,
interval/timeout/retries, /app workdir and explicit local logging. Orchestrator
retains the existing read-only /repo bind with private propagation. Existing
application source lists and the three storage targets are unchanged.
`docs/review_artifacts/companion_stopped_recipe_20261017/recipe.json` is NOT an
executable accepted manifest. Installation authorization remains false; expected
replacement fingerprints are explicitly MODELLED rather than observed.

Receipt reconciliation now checks the seven identities against the source
manifest, rejects duplicate/wrong identities or invalid restart state, recomputes
the supplied metadata/foundation digests, and checks a final observation payload
when one is available. Future captures retain that final payload. The old capture
is preserved and still labelled paired_payload_verified=false; no historical
observation has been invented. Legacy fingerprints are supported for artifact
validation only. Newly derived fingerprints use companion-preservation-v2.

Version2 covers selected user, privilege, resource, logging and exception-presence
controls previously outside the adapter fingerprint. It canonicalizes equivalent
ro/empty mount-mode representations only when RW supports that interpretation,
network name versus its recorded ID, and alias order/duplicates. It still detects
changed access, source, propagation, extra aliases or unrecognized mode metadata.
Old accepted hashes/pins must not silently become version2 operational approvals.

Original labels are encoded without printing or persisting their values. The
installation child copies them through a separate inherited anonymous descriptor;
environment values remain on private stdin. The transport drains both inputs and
stdout under the existing deadline and closes descriptors on failure. The child
checks label equality after creation and again during source verification, adding
only the attempt label and any explicitly reviewed public label overrides.
This preserves existing ownership labels rather than silently dropping them.
No actual label or credential values were accessed in this implementation scope.

The query command allowlist was not widened. The installation option allowlist
adds only --log-driver=local. No new service, dependency, migration or background
job was introduced. Private label/environment buffers are not guaranteed forensic
zeroization; their intended lifetime is the disposable worker.

## Verification

Seven-module targeted command:
```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_companion_stopped_recipe.py tests/test_collect_companion_recreation_metadata.py \
 tests/test_companion_installer.py tests/test_companion_install_env.py \
 tests/test_companion_docker_transport.py tests/test_companion_runtime_adapter.py \
 tests/test_companion_runtime_wiring.py
```
SHOWN: 306 passed in 2.29s. An earlier run had 2 failures/304 passes because the
new legacy-receipt comparison treated persisted JSON network lists differently
from equivalent in-memory tuples. Comparison now uses canonical JSON encoding;
no saved observation or hash was changed to satisfy it. Not a full repository run.

Installed CLI against disposable fake Unix sockets only:
```sh
env -i PATH=/usr/bin:/bin CRYPTKEEP_SYNTHETIC_CLI_CHECK=1 \
 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
 -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_companion_installed_cli_interfaces.py
```
SHOWN: 6 passed in 0.58s. Includes actual native CLI parsing of a separate private
label descriptor, whitespace/Unicode and 50KB label value, with no environment
values mixed into labels. Synthetic IDs/HTTP responses only; no Docker daemon or
real container creation. Python pipe tests separately cover simultaneous 50KB
inputs, timeout cleanup and malformed label rejection. Local fixtures are not
server-side preservation or actual-label transfer proof.

Recipe generation used the preserved capture4 observation and original source
manifest via `python -B -m scripts.research.prepare_companion_stopped_recipe`.
All four recipes populated; executable Plan.load refuses the actual recipe bytes
with their correct hash. Recipe SHA256:
`459e9b1864157be09a05d15d13b7928df3af6f2dc2ed32df490cad8561015154`.

## Remaining proof

VERIFIED_ENV: offline Python fixtures and installed CLI/fake sockets. UNVERIFIED:
actual stopped-container reconstruction, source import/dependency isolation,
strict registry isolation and genuine cited explanation. Legacy capture is dated
and unpaired; a fresh paired capture is required before operational reuse.
Source hashes and independent review disposition will be recorded with the final
review snapshot. No production-readiness or profitability conclusion follows.

## Review correction and final proof

Independent AUDITOR reproduced 306 passed in 2.23s and found one protection gap:
verify_sources runs in a separate worker from prepare/create, so their core-dump
limits did not protect its private label reads. The reviewer observed a zero soft
limit on this host; no actual disclosure was shown. The label reader now enforces
soft/hard RLIMIT_CORE=(0,0) before every private inspection and fails before reading
if that cannot be set. A real separate-worker regression and a failure-path
regression were added. Independent narrow confirmation: ACCEPTED for this fix,
3 passed/41 deselected in 0.23s. It did not repeat the native fixture run.

Final eight-module selection added the installed CLI fixture module and enabled
CRYPTKEEP_SYNTHETIC_CLI_CHECK=1: SHOWN 314 passed in 2.74s on the final source.
The earlier counts overlap; they are not summed. No full repository suite or
real Docker daemon was used. Native fixture permission covers disposable Unix
sockets, not service operations. Frozen source/test/recipe hashes are recorded
in `docs/review_artifacts/companion_stopped_recipe_20261017/proof.json`.

Validation proves identity and internal consistency, not authenticity of an
arbitrarily forged self-consistent receipt. Independent provenance and fresh
paired observation remain required before operational reuse. Original labels
may include external-controller ownership; preserving them does not establish
safe interaction with that controller while rollback objects also exist. No
Compose or other controller operation is included or tested here.

Overall independent disposition after that correction: ACCEPTED_WITH_RISK for
the bounded offline slice; the sole confirmed finding is closed. Saved as
review.json beside proof.json. No other concrete blocker from that review;
operational installation/startup remains unauthorized and unverified. The final
314-test run is the parent's proof, not an independently reproduced result.

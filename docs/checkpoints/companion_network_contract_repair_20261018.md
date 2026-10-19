# Explicit stopped-network configuration contract repair

Date: 2026-10-18. Active role: ENGINEER. Risk: HIGH.
Implementation READY_FOR_INDEPENDENT_REVIEW. Operational restoration INCOMPLETE.

## Decision and preserved evidence

The independently confirmed P1 is a contract defect: Docker's stopped/created
network placeholders are rejected during replacement and rollback. The saved
recovery outcome remains INCOMPLETE; the observed raw fingerprints, blank IDs,
receipts and all prior manifests/reviews are unchanged. This repair performs no
Docker commands, private-config reads, lifecycle, storage or trading operations.

Chosen path: explicit opt-in `companion-configured-install-v3`, not a silent
normalization of v1/v2. Its reviewed input must declare `network_contract` with
schema `configured-network-v1`, exact network name-to-ID bindings, and
connectivity_verified=false. Both existing deferred startup policies stay false.
An installation plan is still not a runtime approval. No operational v3 plan is
generated or accepted by this implementation stage.

## Implementation consequence

- Existing v1/v2 retain raw network-ID and metadata checks. Empty network IDs
  remain refused, and configuration fields cannot be smuggled into those plans.
- V3 snapshots retain the raw metadata digest and observed network IDs unchanged,
  and separately expose configured_metadata, configured_networks and provenance
  `(name, verified ID, reported_id/configured_only)`. Neither provenance value is
  a claim of verified connectivity or effective attachment.
- Native inventory verifies every declared mapping using bounded read-only
  `network inspect` on the exact IDs. Unknown names, contradictory explicit IDs,
  missing IDs, daemon mapping mismatch and inconsistent provenance are refused.
- Blank IDs are permitted only for this attempt's owned, created, never-started
  replacement, or a stopped exact original application with unchanged image,
  start time, restart count and no attempt label. Running/foreign/restarted
  replacements are refused. Storage final checks remain exact.
- The separately named configuration digest projects a verified network ID and
  treats empty IPAMConfig={} as no static request, like null. Nonempty static IP
  requests, aliases, mounts, healthchecks and safety comparisons remain in the
  digest. Raw IPAM/ID differences remain in the original raw digest and receipts.
- Lifecycle commands use the verified configured ID, never an observed blank.
  Original image/identity/foundation, ownership, deadlines, source checks and
  rollback limits remain in force; no start, exec or retry path was added.
- Rollback explicitly reports `rollback_scope=configuration_only`, a separate
  `rollback_exact_baseline` result and `network_connectivity_verified=false`.
  Its receipt records configuration and exact-baseline outcomes separately. A
  successful configured rollback can have an exact-baseline mismatch; it must
  not be reported as exact restoration of the historical observation.

Fresh observed baseline and derived v3 expected configuration fingerprints need
independent manifest review before any future operation. Old reviewed artifacts
are not upgraded, rewritten or reused as v3 authorization. The prior incomplete
live recovery is not retroactively accepted by passing synthetic tests.

## Verification

Saved before/after daemon captures are replayed offline: the audit raw mismatch
is preserved, all seven separately projected configuration digests match, and
the input JSON is not mutated. Negative cases cover wrong/missing IDs, unknown
names, endpoint contradictions, wrong mapping, foreign ownership, running state,
restart drift, alias/static-IP/health/mount/safety drift, startup promotion and
legacy opt-in refusal. Fake-backend state-machine cases cover created placeholder
success and create/source-check failure after effects, including owned removal,
original reconnection, exact-storage preservation and honest rollback labeling.
Three runtime tests refuse all installation schemas even with otherwise valid
synthetic runtime review fields. No actual daemon was queried during this work.

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_companion_installer.py tests/test_companion_network_configuration.py \
 tests/test_companion_install_env.py tests/test_companion_docker_transport.py \
 tests/test_companion_existing_controller.py tests/test_companion_runtime_adapter.py
```

VERIFIED_ENV: 396 passed in 2.70s. Targeted local/synthetic proof, not a full suite,
live replacement, private transfer, effective network or runtime proof.

```text
scripts/research/companion_install_docker.py
c0425e0faa668307962eb60acda40d1883d6a6c3dc34c453330414289f1454f2
scripts/research/companion_installer.py
706dd12a69f4421116f764c7d4a1833aa550a5a9e8f5cea35e5adfda5e066e5b
scripts/research/companion_network_configuration.py
c3824743fb08098a35af6966ee9e3345a63e6500f18a5fdd84a02d1114bf39d7
tests/test_companion_installer.py
9b29c5658e9b0ed017e230fb2aa7b274cdbdbdbcb58107bb099ef9a32e4e6333
tests/test_companion_network_configuration.py
83e5dea37145496cda901db03cc89b62e10c701922f8bbf5fbbad5bf22aac77a
tests/test_companion_runtime_adapter.py
af957957660fdae466edd3783146643db7cfedd42c030c14fd3e1923a71103ba
```

## Remaining risk and required proof

Separate review must assess this explicit weaker configuration-only claim and
its guard coverage. Correct namespace binding and configured aliases do not
establish endpoint attachment, DNS or connectivity. Trusted local evidence and
quiescent external lifecycle writers remain required; daemon reads are not an
atomic transaction. No new live operation is authorized. The next operational
artifact must bind a fresh baseline, verified name/ID mappings, expected projected
fingerprints, this reviewed code and the original startup deferrals.

# V3 stopped installation outcome and diagnostic correction

Date: 2026-10-18. Active stages AUDITOR outcome, ENGINEER diagnostics.
Risk: HIGH. Installation INCOMPLETE. No startup/trading authorization.

## Actual authorized attempt

All 39 exact plan-review bindings matched; the exclusive receipt did not exist.
Executed once:

```sh
env -i PATH=/usr/bin:/bin ./.venv/bin/python -E -B -m scripts.research.companion_installer \
 --manifest docs/review_artifacts/companion_install_candidate_20261018/configured_v3/reviewed_configured_plan.json \
 --reviewed-manifest-sha256 f5b044858c3d40881239b77745d0b404c4ac05d2f35a6d043fed8f6ba934bf5f \
 --apply-install \
 --receipt docs/review_artifacts/companion_install_candidate_20261018/configured_v3/installation_receipt_20261018.jsonl
```

Exit 1. SHOWN output: failure_stage=replacement, installed_stopped=false,
rollback_verified=true, rollback_exact_baseline=true,
rollback_scope=configuration_only, services_started=false, startup_authorized=false,
network_connectivity_verified=false, receipt_complete=true, installation_evidence=null.

Receipt records first audit rename/detach/create intentions, failure, owned
replacement removal and original name/network restoration intentions, then
rollback_checks_completed with configuration_restored=true and
exact_baseline_restored=true. This proves neither a successful installation nor
the specific failing replacement predicate or source verification step.

## SHOWN subsequent read-only verification

Two bounded native backend inventories at 2026-10-18T15:48:47.840358Z agree.
All seven selected originals exactly match this v3 plan's current baseline;
no selected attempt-owned objects remain. No private configuration was read by
this check. The baseline already records audit's configured-only blank network
ID. Exact match here does not retroactively restore or accept the older
pre-recovery network observation, whose historical outcome remains INCOMPLETE.
No connectivity or storage-content audit follows from selected snapshot equality.

Artifacts under the existing configured_v3/ directory:

```text
installation_receipt_20261018.jsonl
04bca3641e3da4d0943e4eece1d92091ed597dfebf1ef9069a7cc7e3016bf664
post_attempt_snapshots.json
9535938572b1c0f773790bb2c20b5434726d8a71bac41764410361e3ab58c674
```

## Correction: preserve failure evidence before cleanup

The actual replacement failure remains UNVERIFIED as to cause. No acceptance
criterion is weakened and no speculative environment-order or source-copy fix
is applied. Added finite create/replacement-inventory/replacement-check/source-
verification stages and a replacement_checks receipt containing only booleans
before the assertion and rollback. The same ten predicates still determine
acceptance; missing replacement records present=false. Final validation reuses
that predicate set. No raw values, exceptions, private config or command output
enter this diagnostic. Receipt-write failure still triggers recovery.

Changed hashes:

```text
scripts/research/companion_installer.py
5cdd79674de562cfabfe549b8405ced060cf2ea214ba54b365e46743b2721bf2
tests/test_companion_installer.py
1e2639d0a9cef85d43a8b46216613882b9e0c6f8eb1548d7f8a46fa77ff1017f
```

Targeted command (VERIFIED_ENV):

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_companion_installer.py tests/test_companion_network_configuration.py \
 tests/test_companion_install_env.py tests/test_companion_docker_transport.py \
 tests/test_companion_existing_controller.py tests/test_companion_runtime_adapter.py
```

408 passed in 2.75s. Twelve added cases cover every retained replacement check,
pre-cleanup metadata mismatch, separate source failure, and persistent receipt
failure at the new diagnostic. Updated the expected create stage accordingly.
This is diagnostic proof, not proof the unresolved installation defect is fixed.

Exact source-only diagnostics delta and saved rollback evidence submitted for
independent review. Implementation READY_FOR_INDEPENDENT_REVIEW. Old manifests,
receipts and review records remain unchanged; the prior plan review does not
approve changed installer/test bytes. No further installation/retry occurred.

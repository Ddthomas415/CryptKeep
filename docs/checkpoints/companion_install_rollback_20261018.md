# Installation failure and bounded original-container recovery

Date: 2026-10-18. Active role: AUDITOR. Restoration INCOMPLETE.

The user approved one stopped-only attempt using the independently reviewed path
repair. All 34 combined bindings matched. The exact approved installer ran with
exclusive receipt `installation_receipt_canonical_20261018.jsonl`. It returned
exit 1, failure_stage=replacement, installed_stopped=false,
rollback_verified=false, services_started=false. Receipt records first-app
audit rename/detach/create intentions, then failure. No second install ran.

## SHOWN read-only diagnostic state

Native selected inspection after failure showed:

- Original audit ID fbec9f31369f833ff950307af30c974a48a9ee7fd63eaa4d09db6563225f68fe
  remains exited, zero restarts, original image/start timestamp, now named
  phase1-audit-log-rollback-477659164ab646d6ad658d7d987f699b, networks empty.
- Created replacement audit ID
  709958bfca10891d324809686c31f82afec8f1121674138dda4af600fa24a4f4,
  image sha256:27753fce0270f4718cb4402163c801dfde65c4ef5dadc0a39338ddeae78f8270,
  attempt label 477659164ab646d6ad658d7d987f699b, never started, zero restarts,
  restart policy no. Its known network has configured aliases but NetworkID="".
- The other six original IDs/images/start timestamps/stopped states remain the
  baseline values in the selected inspection. No storage content proof inferred.

Installer `_rows` requires every network ID to be a full hash, including on a
never-started created container. This explains a reproducible rejection of the
observed placeholder and prevents its existing rollback inventory from being
usable. Do not start the container to populate network metadata or broadly relax
ownership validation. The receipt itself has no child exception trace.

## Recovery scope

Existing authorized rollback is remove only this owned never-started replacement,
restore the exact original audit name, and reconnect its exact original bridge
with the original two aliases. No force, volumes, original deletion, image
cleanup, startup or private environment reads. Other originals are not modified.

Separate GATE reviewed this command-plan with explicit guard requirements.
An exact one-purpose implementation is submitted for its source review:
`docs/review_artifacts/companion_install_candidate_20261018/recover_audit_original_once.py`.
It requires the same installation lock, CLI/manifest hashes, complete original
pre-state checks, exact ownership/never-started replacement check, bridge mapping,
parent lineage, per-operation postconditions and two final original captures.
90-second deadline, 10-second operation caps, exclusive sanitized recovery receipt.
Syntax parsed without running it; no tests or operational execution claimed here.

Source initially submitted at SHA256
e169a8780a62915cc90950767e5b65fe71997388384a49d864a4833473f29767.
High-risk source READY_FOR_INDEPENDENT_REVIEW. Recovery execution pending this
review; installation objective remains INCOMPLETE. Source review and any actual
recovery outcome will be recorded separately without rewriting this checkpoint.

## Actual recovery and final saved state

Separate GATE accepted the exact script/non-optimized launch WITH_RISK and bound
it in recovery_review.json, SHA256
1c2624b9aac281f93449c2aa80cdba6b4a93aadd5bd0a3b30eb57b704fc9dee8.
All seven review bindings matched. The one reviewed rollback invocation ran:

```sh
env -i PATH=/usr/bin:/bin ./.venv/bin/python -E -B -c 'import runpy, sys; sys.flags.optimize == 0 or sys.exit("optimized_python_refused"); runpy.run_path("docs/review_artifacts/companion_install_candidate_20261018/recover_audit_original_once.py", run_name="__main__")'
```

Exit 1, rollback_verified=false. Its receipt records passed preconditions,
removal, original rename and network reconnect intentions, then incomplete.
Do not replace that result with a success claim. Subsequent read-only paired
capture and final selected name/ID inventory establish the following:

- All seven original names/IDs, images, exited states, start timestamps, restart
  counts and no-restart policies match the baseline. The attempt replacement ID
  is absent, and no selected rollback name remains.
- Six original snapshots match completely. Original audit's foundation digest
  matches, but its network has the original bridge name and two aliases with
  NetworkID="" and IPAMConfig={} after the stopped reconnect. The prior network
  had a full NetworkID and IPAMConfig=null. Exact network/metadata fingerprints
  therefore do not match. The configured network is restored; attached network
  identity and exact rollback postcondition are not proved.
- No service was started. Storage selected snapshots match, not a content audit.
  Four source-only derivative images were built before replacement per installer
  ordering; no image cleanup/pruning was performed or authorized.

Artifacts under docs/review_artifacts/companion_install_candidate_20261018/:

```text
installation_receipt_canonical_20261018.jsonl
bae423abdc5943117ceb19c779145d6046fe64f962c92cda5745cb55a441c4a2
manual_recovery_receipt_20261018.jsonl
a213af99367e505ac18367c2bdc16c7fe7fba40eb2c9578bbdfbb0deaf7cd7f0
recovery_after_capture/observation.json
9f54adc0321e60958b54721c5f1afd41ffb953ed99aa157f8208a0181c707b09
recovery_final_names.json
cc876f1bc0208093a5ea692b7f76175a599d470f3ff53d8f733aa2cbe0f3ae0b
```

No repeat of installation or the recovery script occurred. The final issue is
the install/rollback contract's handling of real stopped-container network
placeholders. It needs an explicitly reviewed configured-versus-attached network
identity contract, not a hidden normalization, stale-baseline substitution or
starting services just to satisfy a fingerprint. Independent review of these
saved outcomes requested; operational installation/recovery acceptance INCOMPLETE.

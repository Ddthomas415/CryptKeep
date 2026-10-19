# Stopped installation: optional Healthcheck repair

Date: 2026-10-18. Active role: ENGINEER. Risk: HIGH.
State: READY_FOR_INDEPENDENT_REVIEW. Restoration: INCOMPLETE.

## Authorized attempt and actual result

The user explicitly approved the previously named stopped-only installation.
The reviewed installer was invoked once through the elevated execution gate:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m scripts.research.companion_installer \
 --manifest docs/review_artifacts/companion_install_candidate_20261018/reviewed_stopped_plan.json \
 --reviewed-manifest-sha256 a513c458419f01517fec5e771e5be967f85b43391de663dc55c0bcdfb8ac4af4 \
 --apply-install \
 --receipt docs/review_artifacts/companion_install_candidate_20261018/installation_receipt_20261018.jsonl
```

Exit 1. SHOWN result: installed_stopped=false, services_started=false,
startup_authorized=false, receipt_complete=true, installation_evidence=null.
Receipt contains only installation_reserved and installation_failed; no rename,
detach or create phase. rollback_verified=false is not evidence that a rollback
failed: the installer never set its mutation flag. No installation retry ran.

## SHOWN diagnostic evidence

The existing metadata collector performed two read-only inspections and saved
`docs/review_artifacts/companion_install_candidate_20261018/post_attempt_capture/observation.json`.
It reports all seven original IDs/images/stopped states match, complete selected
metadata, and matching paired payloads. Its SHA256 is
ce0547bc4e8e37abd11564eb53c143a5c36b5760cb43b68a9986bdaf07a3d5f0.

A separate read-only check of the exact backend inventory template against the
seven pinned IDs reproduced sanitized category
`metadata_template_error:.config.healthcheck`. No raw stderr or private values
were printed. The proposed single-field index lookup then returned seven rows
and preservation fingerprints matching all seven reviewed baseline records.
These checks show the template defect; the installer's generic receipt alone
does not identify its exception or provide per-command history.

## Minimal correction

Only the install backend's inspection template changes:
`.Config.Healthcheck` becomes `(index .Config "Healthcheck")`. Docker can omit
this optional map key; the corrected template emits null rather than failing.
Other selected fields, credential-presence comparisons, attempt-label identity,
metadata fingerprints and lifecycle guards are unchanged. The runtime adapter
and reviewed manifest bytes are unchanged. Present healthcheck content remains
fingerprinted and cannot silently change.

Changed source SHA256:

```text
scripts/research/companion_install_docker.py
f0635e39eff1cacdba81f8c5837f505a62b2d04e932a63940e548b836b4f1ff8
tests/test_companion_installer.py
14832b6825bf69cd487bc78b4b00f93ab6bdb6ba25dc6c380311506f7d574938
```

Added three regression cases: exact template selection and null/present
healthcheck inventory/fingerprint preservation. Before the source change:
1 failed, 2 passed, 59 deselected. After the source change:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_companion_installer.py tests/test_companion_install_env.py \
 tests/test_companion_docker_transport.py
```

VERIFIED_ENV: 227 passed in 1.44s, local/synthetic tests only. No full suite.

## Next proof and boundaries

Separate reviewer must assess the exact delta and preserved failure evidence.
The prior plan_review.json binds the old backend/test hashes and is not approval
of changed code. Keep it immutable; any accepted supplemental review must name
the new hashes and the preserved plan. No second installation, new receipt
attempt, build or private-config access is authorized by this repair record.
The one-attempt boundary remains; another operational attempt needs its own
approval and fresh precondition checks. SDK/storage startup, source-import
enforcement and genuine explanation acceptance remain unresolved.

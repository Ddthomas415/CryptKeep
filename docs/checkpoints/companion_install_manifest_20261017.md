# Four-service installation source bundle

Date: 2026-10-17, America/New_York. Active role ENGINEER, risk HIGH.
Implementation handoff: READY_FOR_INDEPENDENT_REVIEW. Operational manifest and
explanation runtime: INCOMPLETE. This scope performed no Docker or network call.

## Delivered

`docs/review_artifacts/companion_install_manifest_20261017/manifest.json` records
all four parent image identities from existing evidence, exact application source
hashes, conservative repository import inventories, template-only port/mount/
health declarations, and explicit missing executable fields. Four tar files
preserve the source bytes rather than merely pointing at this dirty checkout.
Old plans, sources, evidence and the prior single-build receipt are preserved.

| Application | Application Python files | Repository Python files |
| --- | ---: | ---: |
| audit-log | 9 | 0 |
| risk-stub | 9 | 0 |
| memory | 11 | 0 |
| orchestrator | 14 | 198 |

These are per-application counts, not unique-file totals or runtime-loaded counts.
The bundle is an offline review format, not a ready-to-execute installation plan.
Its schema differs deliberately from the installer's accepted-plan schema;
installation_authorized is false, and no accepted review/policy is manufactured.
The existing executable Plan loader refuses its actual bytes, even with their
correct SHA256 supplied. Review acceptance must never be inferred from a hash.

## Demonstrated source-list defect corrected

The loader previously accepted an orchestrator plan that omitted imported
shared/answer_metadata.py, shared/prompting.py, shared/__init__.py or the
orchestrator package initializer. Four new omission regressions failed before
the correction. Required application-source paths now share one helper between
the installer and runtime adapter; all four application initializers and the
shared initializer are required, as are both additional orchestrator modules.
No runtime authorization, command allowlist, credentials, limits or service
behavior was relaxed. Existing synthetic pin fixtures were updated accordingly.

New offline preparer statically parses imports without importing the target
modules. It includes transitive static imports, package initializers and imports
inside functions/conditional branches; it flags dynamic loading instead of
pretending to resolve it. Source reads are bounded, regular-file checked and
symlink-rejected. Output must be a new directory, preserving prior artifacts.
Snapshots contain public Python source only, not env files or raw inspect data.
Compose is parsed as a template; credential placeholders are not rendered.

## Verification

VERIFIED_ENV: local Python and filesystem-only fixtures, not installed containers.

Before source changes:
```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_companion_installer.py -k requires_imported_orchestrator_sources
```
SHOWN: 4 failed, 38 deselected, because missing paths were accepted.

After source changes:
```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_prepare_companion_install_manifest.py tests/test_companion_installer.py \
 tests/test_companion_runtime_adapter.py tests/test_companion_runtime_wiring.py
```
SHOWN: 116 passed in 0.96s. Not a full-suite or runtime result.

Generation:
```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
 -m scripts.research.prepare_companion_install_manifest \
 --output docs/review_artifacts/companion_install_manifest_20261017
```
Additional offline assertions verified every archive's SHA256, member count,
regular-file type and per-member source hashes, and that the executable installer
refuses this review bundle. No build or extraction into an installed application.

## Material limits

SHOWN: shared/tools.py imports dashboard.services.intelligence at module scope.
Python package initialization adds dashboard/services/__init__.py and its imports.
The conservative inventory consequently spans 198 repository files and seven
dynamic-loading call sites. This includes lazy/conditional paths; it does NOT
show all these modules execute during a restricted request. It is not proof that
execution code is called. The restricted service profile remains unchanged.

Compose declares PYTHONPATH=/app:/repo and a read-only /repo bind. Those are
template facts; the current installed PYTHONPATH was not verified here. The
source's own path manipulation is included in the snapshot. A read-only bind
does not freeze host writes. Dynamic loading, installed modules, import hooks,
precedence and non-Python data remain outside static closure proof. The current
query transport does not allow /repo archive reads; its allowlist was not widened.
The memory article archive and optional required marker are not in these Python
snapshots; their installed presence/identity must be established separately.

No material environment assumption is used to authorize an operation. In
particular, Compose is not substituted for current container metadata. Recorded
IDs/images are dated observations, not a refreshed runtime inventory.

Missing facts preventing an executable manifest:
- Exact current StartedAt, network IDs/aliases/IPAM and full recreation metadata.
- Expected replacement preservation fingerprints from verified metadata.
- Mounted source/import identity and complete installed dependency review.
- Strict no-pull policy disposition; the prior build only showed prefer-local.

Next bounded action: collect the missing selected nonsecret recreation metadata
read-only, without full inspect/env output, then reconcile it with these frozen
sources. Do not rebuild, replace, access credentials or start services to fill
these fields. No placeholders or template values should be labelled SHOWN runtime
facts. A genuine cited explanation remains a separate operational acceptance.

## Independent review

Separate AUDITOR: ACCEPTED_WITH_RISK for this offline source-manifest scope only,
with no concrete blocker. Independently ran the same selection: 116 passed in
1.03s. Verified all four archive digests and 241 per-application member records
(including repeated common files), sizes, destinations and checkout hashes;
baseline/template hashes also match. Confirmed the candidate remains non-executable.
No Docker/network, credentials or operational action by the reviewer. Runtime
metadata, actual loaded imports, installed compatibility and registry isolation
remain UNVERIFIED. Reviewed code/tests/manifest unchanged after that review.

## Frozen hashes

```text
manifest.json bac2f4636753237279858c2119630be12531d8d27f6967868d72e9cbac940093
companion_runtime_adapter.py dbb6a2edd42641ba7da0258a018be52b5e77bd9b8688269d2180f89d24fddfc2
companion_installer.py 9548085050a5249b30fb3432cb0374582ef5f3e3845395205ec822863f3ddb42
prepare_companion_install_manifest.py 7a591b608c8f08089180462a4584728f38b6fadbf9ba88855b2a4869bd308962
test_companion_installer.py 190945dd9ceba5151d6e3d177d1fea7c28bd3c061be549d3cb610f2f7a49069f
test_companion_runtime_adapter.py af2c370d2f836d067e63b45067126fe09240e774280ac8294a01f8dd8dcfaab9
test_prepare_companion_install_manifest.py 2e0fe3424e9dfc6b21aea86acb4b6033fa236431098f276120b94ee8db49ad2b
```

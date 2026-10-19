# Current-source stopped-installation candidate

Date2026-10-18 New York. Active stages ENGINEER preparation, independent
AUDITOR review. Risk HIGH; READY_FOR_INDEPENDENT_REVIEW. No installation or
startup performed. This extends the existing installer, not a new framework.

## Fixed source binding

The metadata collector previously always bound its receipt to the older source
manifest. Added --source-manifest while preserving the legacy default. Only a
bounded regular manifest.json below docs/review_artifacts is accepted; symlink,
noncanonical, outside, directory and oversized selections fail before Docker
or output creation. Path and bytes hash are retained. Two metadata-only inspect
commands, command allowlist and credential redaction unchanged.

Collector/test hashes:
```text
collect_companion_recreation_metadata.py 3e81a24397eefc770a4cfda9da7a9f74467dbde33321f542286c3431869f7a46
test_collect_companion_recreation_metadata.py 0a7f8eef53070e071d7b78ef0d4950b288415c02901b63c962ca838fb3346a8e
```

Exact offline verification:
```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_collect_companion_recreation_metadata.py tests/test_companion_stopped_recipe.py
```
SHOWN36 passed0.58s, independently the same36 passed0.58s. No full suite.
Separate AUDITOR ACCEPTED_WITH_RISK this delta, no findings; path/open remains
non-atomic under the existing no-hostile-concurrent-writer assumption.

## Fresh actual evidence and artifacts

One tool-permitted read-only capture at2026-10-18T09:39:23.970123UTC
(05:39:23 New York), exactly two selected seven-ID inspections. Both retained
payloads match, identities/images/stopped state agree with original baseline,
all selected metadata present. No raw credentials, full environment/labels,
container lifecycle, image build or service request.

Bound current manifest973da853c3c2aabdce982c677b5b6ab9c6d7cbab5061ec27ab28197b07b3c875
and checked all241 application/repository records against their exact archived
regular members and current checkout bytes. No source regenerated or changed.

Generated with existing compile_recipe from the fresh capture plus current
source manifest: four stopped-replacement recipes, complete modeled options,
network aliases and projected preservation fingerprints. Fingerprints are
MODELLED, not evidence that replacements already exist. Labels/private config
remain intended child-memory transfers, not values collected in this capture.

Artifacts at docs/review_artifacts/companion_install_candidate_20261018/:
```text
capture/observation.json 5207ca9c190e23f639cec5359508d56aed7ec237b1e8c0571d5748f0401f11ec
recipe.json e1099173c1c4c3f190dd3875e60df6b0670d1feb4abf5a6fb15d67f980a50479
plan_candidate.json 3ce6fd12cd29ba3a47b774f03b5c2e4e1a916d79b9a7f6bd7bbdedffdd5a3141
```

plan_candidate.json projects only the existing loader's fields: seven baseline
snapshots, four application recipes and43 pinned application source records.
It has no accepted reviewer, decision remains READY_FOR_INDEPENDENT_REVIEW,
all six policy flags false. Actual Plan.load refuses these exact bytes even
with correct hash, as recorded in validation.json. No acceptance manufactured.

## Review and operational boundary

Requested independent per-policy disposition for the specific stopped-only
installation, separating prerequisites from checks the installer performs as
postconditions and from later startup/query evidence. Existing build/parser/
source/metadata proofs should be reused, not repeatedly rerun or inflated into
full-platform approval. Ordinary /repo source identity and complete SDK/storage
startup must not be silently certified by the restricted import smoke test.

No policy/decision has been promoted by the parent. Historical source bundles,
failed import receipts, storage data, credentials/config, schedules, capital,
strategy and trading state preserved. No image build, replacement or real query.
Actual installation/startup remains INCOMPLETE until this candidate has the
required review/evidence and the named operational scope is authorized.

## Independent policy diagnosis and stopped-only schema proposal

Separate AUDITOR ACCEPTED_WITH_RISK artifact integrity, no discrepancies;
reproduced normalized recipe and candidate projection, all241 source records.
For stopped installation it accepted builder_local_only, env_stdin_lossless,
image_provenance and recreation_complete with stated risks. It did NOT certify
effective credentials or full daemon-side environment equality. Derivative image
and replacement checks are legitimate installation postconditions, not evidence
that must be manufactured before their creation.

sdk_startup_compatible and source_imports_frozen remain INCOMPLETE as named:
intended SDK/lifespan/storage checks and mutable-host /repo import enforcement
belong to later startup/query. The current all-six-true loader cannot express
that distinction; this is the immediate concrete blocker, not another required
backtest or need to repeat the completed import checks.

DIRECTOR decision: add an explicit stopped-installation-only schema while
preserving the legacy contract. ENGINEER implemented companion-stopped-install-v2:
four installation policies must be true, both startup policies must be explicitly
false. They cannot be omitted or represented as accepted by this schema. Plan,
initial reservation, success evidence, result and inert CLI retain the deferred
policy names and startup_authorized=false. No start/exec capability added;
runtime controller/adapter and separate startup approval remain unchanged.
This is a phase-policy change, not evidence that the two missing requirements
have been satisfied. The existing v1 still requires all six true.

```text
companion_installer.py c2cb24ff29412cfb1f985100ef454a131ff1245c86504f9108c242353de85eb2
test_companion_installer.py aab319308245b8779d219fbc64147bf717c7d7e07c2504bd4540f60912555c7f
```

Targeted installer/controller/adapter selection188 passed1.67s, mocked/local
fixtures only. Covers both schemas' stopped behavior, legacy six-policy refusal,
new four-true/two-false enforcement, deferral receipts and create-after-effect
rollback. No actual install, real private configuration, package or startup.
Code submitted for separate review. Candidate/flags not promoted by implementer;
handoff READY_FOR_INDEPENDENT_REVIEW; restoration INCOMPLETE.

Separate AUDITOR ACCEPTED_WITH_RISK exact stopped-schema delta, no findings.
Independently188 passed1.36s plus fixture-only matrix; confirmed both install
schemas are refused as runtime approval. V1 remains strict, v2 preserves
deferrals and false startup authorization; backend/runtime source unchanged.
This resolves the stage-contract blocker, not later startup evidence.

Prepared plan_candidate_v2.json from the preserved candidate, changing only
schema and the four policy flags supported by the independent dispositions.
Decision/reviewer remain pending, two startup flags false, so actual loader
still refuses it. Separate GATE requested to review exact bytes and, only if
accepted, emit its own reviewed stopped-only plan and hash-bound review record.
The parent will not manufacture acceptance or alter the reviewer's final bytes.
Any accepted plan remains installation-only; actual operation needs its scoped
permission and must finish stopped. No existing service or credential action yet.

## Final manifest gate interrupted

The independent reviewer completed the source-contract review above, then its
separate final GATE run returned a usage-limit error before producing the final
manifest acceptance. Directory inspection confirms no reviewed_stopped_plan.json
or plan_review.json was produced. Do not interpret prior code/policy acceptance
as acceptance of unseen final manifest bytes, or retry reviews automatically.

Current pending v2 candidate SHA256:
f30a6a9831b8c306ecc8e44adfc9edc976800057e4332a15ea7f2f6ee824e281.
Its decision/reviewer remain pending; exact loader refusal is preserved. Code
c2cb24ff... and tests aab31930... still match the independently reviewed hashes.
No installation, service lifecycle, credential or storage action occurred.

Next permitted route is independent review when available, or an explicit human
review decision on this exact stopped-only candidate. Human acceptance must
identify the candidate and scope: four application replacements kept stopped,
original application rollback containers retained, three storage containers and
volumes unchanged, private existing service configuration transferred only by
the reviewed bounded mechanism, no dependency installation, startup, model,
exchange/account or trading operation. Both deferred startup gates remain false.
Any subsequent execution still uses the named permission-checked operation.
Artifact READY_FOR_INDEPENDENT_REVIEW; operational objective INCOMPLETE.

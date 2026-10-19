# Offline correction batch: backup count, VOLFC ledger, v1 recipe

Authorized scope: the operator's continuation after the reconciled three-item
batch. Work began October 18 UTC and closed October 19 UTC. No operational
authorization is implied. All verification commands used known local paths
(VERIFIED_ENV).

## 1. Backup workbook correction

SHOWN: a corrected successor is saved at
`docs/review_artifacts/offline_batch_20261018/codex_oct18_audit_corrected.xlsx`.
The original `~/Documents/cryptkeep_data_archive/codex_oct18_audit.xlsx` remains
unchanged (SHA256 `d584d1c3d37c432f68e50bafb5135cf9bfd873e6d613a53d1fa791b6aa6de870`).

Only `Done!B7:C7` changed: 6,414 files in the main `_r2` copy plus seven assets
in the supplement, 6,421 across both. Both source folders are identified. This
does not verify the operator's off-machine upload, which remains CLAIMED.

Artifact Tool authored and rendered the correction. Its first XLSX export
changed unrelated font metadata. A lossless OOXML transfer retained the original
ZIP parts and styles, transferring only the two artifact-authored text values.
Final readback and render passed. All five sheets and five formulas remain
unchanged. Only `xl/worksheets/sheet2.xml` differs at ZIP-part level. Read-only
openpyxl comparison confirms exactly two changed values and zero style changes.
No original workbook was overwritten or source recovery archive changed.

Corrected SHA256:
`1997c5dc2742c8a29bb95ce757e298afa80c643fd0fff828081ff6daa35f7b59`.
Acceptance: ACCEPTED for this narrow documentation correction.

## 2. VOLFC-1 bookkeeping

SHOWN: new `docs/research/trial_ledger_supplement_20261018/` contains a README,
`trial_additions.csv`, `data_reuse_additions.csv` and SHA256SUMS. It records one
candidate configuration, two baselines and the original FAIL verdict. A local
stdlib CSV check matches 214 distinct markets, 4,999 observations and 50 weekly
clusters to saved forecast/weekly files. The supplement preserves these as
different counting units. No effective N, revised DSR or aggregate trial total
is manufactured.

The October 15 files were not edited. Checksum verification passed for both old
ledger manifests, all five members of the frozen study SHA256SUMS and the three
new supplement files. The preregistration and explicitly pinned source hashes
also remain unchanged. Original model inference was not rerun. Model provenance
and the runner's missing pre-run identity enforcement remain UNVERIFIED.
The first-week availability caveat is retained. "Did not qualify" describes the
result accurately. No new market test or model adoption occurred.

Acceptance: ACCEPTED for bookkeeping and provenance disclosure only, not model
execution or financial validation.

## 3. v1 stopped-recipe compatibility

Active implementation role: ENGINEER. Risk: HIGH (installation evidence path).
The parent reproduced the baseline with:

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_companion_stopped_recipe.py
```

Result: exit 1, 22 passed / 2 failed. Saved capture4 snapshots have 11 fields;
current Snapshot serialization adds three default fields. The 11 original fields
match. The narrow repair checks that the three new fields are still defaults,
projects only computed v1 snapshots to the legacy keys, and compares against
the entire saved payload. It does not filter saved evidence or alter v2.

Added 14 regression cases: seven saved-evidence tamper cases, three nondefault
new-field refusals, and four valid/tampered v2 cases. Existing paired/unpaired
semantics remain intact. No frozen capture/manifest changed.

Parent focused command:

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_companion_stopped_recipe.py tests/test_collect_companion_recreation_metadata.py
```

Result: exit 0, **50 passed in 0.55s**. Implementation ended at
READY_FOR_INDEPENDENT_REVIEW. Separate GATE subagent Plato then independently
ran the selection, **50 passed in 0.40s**, verified the evidence binding, and
returned **ACCEPTED_WITH_RISK**, no blockers. Its recorded review is
`docs/review_artifacts/offline_batch_20261018/independent_recipe_review.md`.
This is separate review, not same-thread self-approval.

The diff against the preserved pre-change recovery files is
`docs/review_artifacts/offline_batch_20261018/recipe_compatibility.diff`
(104 lines, SHA256 `89a7859c1c38b664d2db434ae45403c1c2abbb3fc5aa26dbf44a13f42f0c50f6`).
It covers exactly the collector and stopped-recipe tests.

Reviewed hashes:

| File | SHA256 |
| --- | --- |
| `scripts/research/collect_companion_recreation_metadata.py` | `494803eb4e279efeb6c961c4833de43c388a63df7fc5c63382cdb2ce80c0c2ea` |
| `tests/test_companion_stopped_recipe.py` | `f3f750308c6752f5773dac6a15c8500e219586ea64646150323dc1d5687d2c30` |
| unchanged collector tests | `0a7f8eef53070e071d7b78ef0d4950b288415c02901b63c962ca838fb3346a8e` |

## Remaining boundary

This is targeted offline proof, not a full-suite result or current runtime
inspection. Capture4 lacks a retained final payload. Successful internal
reconciliation does not authenticate the original capture, prove runtime
equivalence, authorize an executable manifest or resolve the previous
installation's metadata mismatch.

Companion installation remains INCOMPLETE and its prior attempt consumed.
No Docker/service/start/query, credentials, server, scheduler, strategy, account,
dependency installation, Git lock/commit/push or trading operation changed.
The original study verdict and original recovery evidence remain preserved.
The three-item batch is closed; broader comparison and restoration work remain
separate queue items.

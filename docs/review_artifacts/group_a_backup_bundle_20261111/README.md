# Local selected-evidence backup and restore core

Bot relation: BOT_RULES; runtime trading configuration not checked.

Creation-time state: READY_FOR_INDEPENDENT_REVIEW; self-checked source.
Final source disposition2026-11-11T22:28:43Z:ACCEPTED_WITH_RISK by separate
Rawls GATE; see INDEPENDENT_REVIEW.md. Operating R3/R10 remains INCOMPLETE.
This is local backup/restore code, NOT an installed or complete R10 service.
MEGA remains the selected off-server destination; Git holds source/manifests
and TeraBox is optional. No provider client, account, key or remote was used.

## Implemented outcome

`services/control/group_a_backup_bundle.py` provides three explicit APIs:
`create_bundle`, `verify_bundle` and `restore_to_new`. Given caller-attributed
query-only SQLite connections, frozen byte streams with expected lengths/
hashes, whitelisted public settings and public run-manifest identifiers, the
core creates a private local bundle and checksummed completion manifest.
Verification/restore require a separately retained expected manifest SHA256;
an archive cannot authenticate an edited manifest merely by hashing itself.

Actual temporary fixtures exercised nine synthetic Group A paper databases
in WAL mode, nine decision artifacts, nine public setting snapshots and one
public run-manifest projection:28 selected files plus bundle.json. The local
restore reproduced every selected database byte-for-byte and preserved the
100001-cent fixture values. A separate real concurrent WAL writer test retained
its transaction invariant. These are real SQLite operations on synthetic
temporary data, not existing paper accounts or private broker holdings.

The creator checks all explicit paths/types/declared inputs, uses exclusive
fresh directories/files, folds SQLite WAL via the backup API, verifies copied
hashes/integrity and syncs files and nested directories before publishing the
completion manifest. Partial output is retained on failure; no overwrite,
deletion, lock reset, historical repair or force-restore exists. Verification
rejects extra/missing files and links, malformed manifests and changed bytes.
Restore first verifies the source and then rechecks bytes while copying into
another exclusive new directory; it never restores over an existing ledger.

`storage/sqlite_backup.py` supplies the shared primitives. The two legacy
path helpers were extracted from `scripts/backup_state.py`; its private names
remain aliases. AST comparison against HEAD shows identical executable bodies
and arguments after normalizing function names/docstrings. The existing CLI's
scope, operator-event behavior and unbounded legacy helper semantics are not
silently changed or retroactively claimed to have the new cooperative bounds.

## Evidence and test lanes

First new-feature test run failed collection because the new bundle API did
not exist. The first implemented run was35passed/9failed:intermediate parents
created with mkdir(parents=True) inherited ordinary permissions, and one test
used the word "changed" both as a payload and in a fixed diagnostic. Corrected
the actual directory creation to one component at a time with0700; changed the
fixture to a distinct synthetic secret marker. Existing tests were not weakened.
An additional source review before GATE added nested-directory fsync before
manifest publication, rather than assuming a root-directory fsync covers it.

Pre-review author command uses a fresh temporary CBP_STATE_DIR, bytecode disabled,
plugin autoload disabled and no pytest cache:

```text
.venv/bin/python -B -m pytest -q -p no:cacheprovider
  tests/test_group_a_backup_bundle.py
  tests/test_sqlite_backup.py
  tests/test_state_backup_restore.py
  tests/test_group_a_unit_composition.py
  --junitxml=docs/review_artifacts/group_a_backup_bundle_20261111/pytest.xml
```

SHOWN:**122 passed in2.98s**, zero failures/errors/skips. XML contains54 new
bundle cases,7 shared-helper cases,14 unchanged legacy-backup cases and47
accepted composition cases. This is a focused Mac source test, not the full
suite, CI, Linux namespace/parser, target capacity or a provider restore.
Earlier intermediate focused runs and the121-case pre-alias-check result
were development evidence, not the review binding. No old1616-case
composition rehearsal, market study or broad backtest was rerun.

Coverage includes actual nine-account selected-data round trip; active WAL
writer consistency; busy source and backup-progress deadline; source settings/
transaction preservation; connection aliasing; lengths/digests; directory
prefix collisions; private/traversal paths; duplicates/deep/nonfinite/schema
and Boolean-number ambiguity; source/output links; private directory modes;
oversize/expired inputs; source changes after verification; extra files;
fsync failures before and after completion-marker creation and no clobber.

## Initial review inputs and trust limits

- Bundle module:`6aca52829346337689a0a5ed462ff4c64879016bda3adbfec006563ef47476d9`.
- Shared SQLite module:`9a0fcd1f4894b18f571406e60beb34cf7514d8595d1bb9d564fb8c943d031a6a`.
- Legacy CLI after extraction:`4f540d1dd924fabd8e89a9c395973c07c1c87ad34d7731f4bf22909abedf6bd7`.
- Bundle tests:`7180a9384d1e973d33ddaaa7ed26cd58b98e220f6d5d855840ae5ccab1c04e87`.
- Helper tests:`fe0cc86b8239a0a1ace17c26c7b840e3bdba89101191e40936a2148a02120c7d`.

### Dated correction:2026-11-11T22:28:08Z

Separate Rawls GATE rejected the initial source pending one P2 correction:
verification could return success after its deadline expired during the last
public-metadata validation. It independently matched all five initial hashes,
checked legacy executable AST equivalence, and ran122tests in2.74s. That was
source review, not proof of provider delivery or complete backup operation.

The corrected source adds one final cooperative deadline check before the
verified receipt. The regression expires the deterministic clock immediately
after the last public-config validation:it failed before the source fix
(DID NOT RAISE) and passes after. The first draft of this regression expired
at the run manifest, which was not the last entry, and passed before the fix;
that draft was corrected rather than represented as reproduction evidence.

Final author run repeats the same four-file command with XML output at
`pytest_final.xml`:SHOWN123passed in3.19s,55bundle+7helper+14legacy+47composition,
zero failures/errors/skips. Original122-test XML is preserved. New source SHA256
is`140cf68cd3247c4ab5017dfd1cf976dda9fabaab6e655b9e2d18aba49b520fa1`;
new bundle-test SHA256 is
`e08efb9e62f1e9a9688ab9006c44bb0ca48f937c900889649f60dec5c342845c`.
The other three file hashes above are unchanged. Final XML SHA256 is
`5cabea12797a212f2847369f629ed5a6df4bc16ea02119352daa7544f8877f31`.
Diff-only independent re-review subsequently closed P2 at22:28:43Z, accepting
the corrected local source WITH_RISK. Reviewer reconstructed the old source
in memory, reproduced failing-before/passing-after without editing files,
and verified the final XML/hash. No further source changes. This detects cooperative expiry,
not hard interruption of a blocked OS or SQLite call.

Assumption1:trusted producer supplies correctly attributed read-only source
connections and frozen streams. query_only is checked, not physical read-only
mounts or complete source inventory. Different connections to the same store
are not proved distinct merely by the object-alias check. Hashes establish
captured content identity, not secret clearance, publisher authority or origin.

Assumption2:the caller's owned0700 output parent is not being maliciously
changed concurrently by the same UID. No hostile same-UID namespace/race
isolation is claimed. Operations use cooperative deadline/byte checks, not
kernel-enforced wall-clock or allocation guarantees for blocked disk/SQLite
operations. Deployment still needs bounded supervision and actual namespace/
permissions/capacity evidence.

Public configs are explicitly whitelisted trading-setting projections, NOT
the original private YAML or a complete restored operating configuration.
Unknown/secret settings are refused rather than copied; their values are not
printed. Generic selected data/streams still require producer-side provenance
and secret review. No automatic live-tree crawl, existing database/config
discovery or credentials are part of this API.

All results retain local_verified versus offsite_verified=false,
selection_scope=explicit_inputs_only and atomic_across_databases=false. Each
file records its completion time; this is not a simultaneous nine-account
snapshot. The completion manifest is a content protocol, not proof of remote
durability. Late I/O failure raises a fixed uncertain failure even if a
manifest file exists; it does not return a successful receipt or retry.

## What remains

DONE:local selected-copy/manifest/verify/fresh-restore implementation,
focused tests, legacy helper reuse and separate source review WITH_RISK.
NOT DONE:complete live inventory acquisition, full public operating-config
capture, physical source identity/mount verification, encryption/key management,
MEGA upload/download, quota/account proof, retention/pruning, independent
heartbeat, six-hour foreground entrypoint and real owner-received alerts.
The missing run_group_a_backup.py is deliberately NOT replaced by a local-only
success stub. The accepted compositor and frozen724b... candidate remain
unchanged and still refuse that missing runtime entrypoint.

Source/test failures or source/manifest drift could overturn the local proof;
unattributed inputs, incomplete acquisition, unsupported storage/runtime
behavior or failed encrypted remote restore would block broader conclusions.
No host/Docker/service/provider/credential/account/trading/configuration,
schedule or risk operation, package installation, commit or push occurred.

What do I know that could change the owner's decision that I have not yet said?
There is real local recovery code now, but restoring the selected fixtures
does not establish a complete or encrypted off-server backup. Source acquisition
and the MEGA/encryption/service path remain necessary work, not paperwork or
success labels this module can supply.

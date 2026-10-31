# Corrected Metadata Expectations

Date: 2026-10-21. Active role: ENGINEER. Risk: HIGH.
Implementation/proposal: READY_FOR_INDEPENDENT_REVIEW. Runtime: INCOMPLETE.

## Chosen Repair

Correct four modeled final configuration fingerprints, not the comparator.
The saved actual DNS/ExtraHosts fields are null rather than the empty lists
assumed by the old model. The old model is exactly reproduced by changing only
those two fields and aliases in offline clones of the actual observations.
The corrected model retains observed null fields and substitutes only the
already intended logical aliases. No general null/empty equivalence is assumed.

No installer, preservation-digest, network, lifecycle, transport or runtime guard
code changed. Exact matching still distinguishes null, empty lists and non-empty
values; this repair does not normalize fields or accept multiple alternatives.
Source lists/hashes, policies, original baseline, create options, actual rows,
attempt and namespace bindings remain unchanged. Both startup policies stay false.

Native preparation was executed under the OLD manifest. A proposed derivative
does not claim a new preparation or permission to repeat it. That attempt remains
consumed; the four existing containers must be reused, not rebuilt or recreated.
Original manifest/evidence/receipt/actual-ID review remain byte-for-byte preserved.

## Changed Artifacts

Under `docs/review_artifacts/companion_continuation_20261021/`:

- `reconcile_metadata_20261021.py`: dated offline recipe, pinned inputs only,
  emits an unapproved draft and provenance exclusively; no native operation.
- `metadata_corrected_draft.json`: only four expected fingerprints plus empty
  reviewer/INCOMPLETE decision differ from the original accepted manifest.
- `metadata_reconciliation_proposal.json`: source hashes and old/new predictions.

New test: `tests/test_companion_metadata_reconciliation.py`.
Recipe SHA256: `47fc715729a02ec4730d8637538c9db1b16f045b3d00ec22e49f48d4016816c8`.
Test SHA256: `a770e556e257de5abcb82e1632409caa5c4f4d6140467b800409269499436f16`.
Draft SHA256: `53803e87f12755256edaf097234e3918d5c3997d27f90bb971f0ade1c8a5eb30`.

## Verification

VERIFIED_ENV: isolated local synthetic/saved-file verification, no native access.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tests/test_companion_metadata_reconciliation.py tests/test_companion_staged_update.py \
  tests/test_companion_network_configuration.py tests/test_companion_staged_composition.py \
  tests/test_companion_installer.py tests/test_companion_metadata_diagnostics.py
```

SHOWN:255passed in2.01seconds, exit0; targeted diff-check clean. The tests use
the unchanged real replacement gate and demonstrate four modeled matches while
rejecting original staging aliases, other aliases, non-empty DNS/hosts, different
empty representations, altered flags/ports/mounts and changed review-bound
identity/lifecycle evidence. Drafts cannot pass the accepted-plan loader. Old
evidence cannot bind silently to a new manifest. No full suite/backtest ran.

## Independent Review Boundary

Separate GATE must verify the narrow draft diff and provenance before issuing
an accepted corrected manifest. Any derivative preparation evidence must retain
the identical four actual rows, change only its manifest binding, and explicitly
trace the original executed manifest/evidence/receipt. Its new actual-ID review
must bind the accepted manifest and derivative evidence, not a draft hash.
Original evidence and prior reviews must never be rewritten or represented as
having run under the corrected plan.

This establishes modeled expectations only. Native alias transitions, SDK/source
startup policies, health and a genuine cited explanation remain unverified.
No Docker, credentials, reservation, build, container, service, scheduler, account
or trading operation occurred. Cutover is not ready or authorized; a bounded
operational entry point and final runtime pins remain outstanding.

## Bounded Portability Correction

First GATE disposition: BLOCKED, P2. The recipe/tests depended on a private
Git-ignored `.cbp_state` input; local passing tests did not establish a portable
handoff. The four-fingerprint derivation itself passed review. No acceptance
artifacts were issued. Original draft/proposal and this finding are retained.

Added `prepared_evidence_public_copy.json`, byte-identical public payload with
SHA256 `78726c0b834778934368713e55a7496a91249d17323e3d43c9052895a5e4d8de`.
The original private file remains unchanged. Recipe input location now uses the
public copy; provenance retains the original path/hash. Tests actively reject
any Path.read_bytes access to `.cbp_state`, in addition to native/socket access.
No private values are in the public payload; it contains only the already-reviewed
four public Snapshot records, manifest hash, attempt and schema/state.

Revised recipe SHA256: `9126f9b6c1a8f754a8a12473749e4c0a8d1ba302afd5dbe6ca22540f6e276015`.
Revised test SHA256: `aa2e4dc4bb7bb4b933071b05fa0b775384194e3368a51ec90191ca725d4d09df`.
The `_r2` draft remains byte-identical to the first draft, SHA53803e87f12755256edaf097234e3918d5c3997d27f90bb971f0ade1c8a5eb30.
The `_r2` proposal records the input-location/provenance correction separately;
no metadata criterion or modeled result changed. Corrected review pending.

Corrected same six-file command:256passed in2.02seconds, exit0. The26new cases
run with private-state access forbidden. No broad suite or native call ran.

## Final Independent Disposition

Separate GATE: ACCEPTED_WITH_RISK. R2 closes the portability P2; independently
26tests passed in0.28seconds, four stale-binding combinations refused,43current
source entries matched and diff-check passed. No runtime gate/source change.
Review/provenance: `metadata_reconciliation_review.json` in the October21 folder.

The reviewer issued separate derived artifacts, preserving every original:

| Artifact | SHA256 |
| --- | --- |
| preparation_reconciled_manifest.json | b9594f55b7d409d5815ea318de68c0391943dcafe919326ebedb143821627b11 |
| preparation_reconciled_evidence.json | a8ba9af67beb156b292fd133ad23155a1ad9443889aec4e003f4841f0a7357b8 |
| preparation_reconciled_id_review.json | 80532a1e65c447cc9e9e5fcdbeb63fc1ae321f3842ba0dd714867fb67bcce514 |

These live under `docs/review_artifacts/companion_continuation_20261021/`.
The manifest differs from the reviewed draft only by external decision/reviewer.
Derivative evidence has the identical four actual rows and changes only the
manifest binding. It records offline reconciliation, NOT a new preparation.
Original native preparation ran under the old manifest; its receipt is not
rewritten or represented as executing this corrected manifest.

Parent inert verification: exact artifact hashes, real Plan/ReviewedPreparation
loading, identical four records and stale-evidence refusal all PASS, exit0.
Default preparation CLI validation of the reconciled manifest passed exit0 with
actions_executed=false/startup_authorized=false. This default does not reserve an
attempt; the original consumed marker still forbids another preparation execution.
Original manifest, private evidence/receipt, original actual-ID review and all
four runtime comparator/backend files were rehashed unchanged.

This supersedes pending-review statements for the bounded correction only.
MODELED final expectations are corrected; actual future final-state behavior is
not proven. No native call, credential access, build, container/service change,
startup or cutover occurred. Next: a separately reviewed, one-shot operational
cutover entry point and final runtime pins using these prepared IDs. Existing
API acceptance is not that executable workflow or permission to run it.

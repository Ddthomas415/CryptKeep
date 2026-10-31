# Fresh V6d Stopped-Replacement Proposal

Role: ENGINEER. Risk: HIGH. State: READY_FOR_INDEPENDENT_REVIEW.
Objective: prepare and independently review fresh stopped-replacement inputs,
not create containers or repeat the consumed V6c cutover. Runtime: INCOMPLETE.

## Evidence

Existing read-only collector ran twice-selected-inspect at
2026-10-23 23:11 EDT (2026-10-24T03:11:39Z), exporting only its allowlisted
metadata and environment presence/match booleans, not credential values.
Both full selected observations equal; seven selected rows complete. Original
IDs/images/running state, restart counts, foundation/configured fingerprints
match the prior accepted baseline; only four app start timestamps changed.
Storage snapshots have no deltas. No container exec or lifecycle action.

Collector report preserves INCOMPLETE because its legacy reference expects
exited containers. The new offline recipe explicitly validates running state
and all identity/configuration constraints; it does not rewrite that report.
Docker running flags are not health, volume-byte or explanation-path proof.

## Smallest Reuse Path

New derive_fresh_preparation_v6d.py verifies and imports the exact reviewed
derive_fresh_preparation.py bytes under a non-main name. Only fixed input
identities and a new unused workerprep20261023v6d attempt are supplied to the
existing derivation. Consumed preparation/cutover markers and removed V6c IDs
are preserved. Absence of new marker paths is not a reservation or proof that
future Docker names are available.

The recipe verifies prior input acceptance, failed V6c outcome and the accepted
current nonrecipient correction; 13 current consumer hashes and 43 local app
source entries are bound. It retains the same applications, commands, options,
policies and four recomputed modeled configured fingerprints. Candidate differs
only in attempt, decision/reviewer reset and fresh baseline. It is INCOMPLETE
with an empty reviewer and is refused by Plan.load until separately reviewed.

Historical staged rows are used only as preserved configuration-model witnesses,
not future IDs or observed new replacements. New IDs/images remain null. Changed
consumer applicability is accepted only for preparation inputs, not runtime
policy, a new executable handoff or a cutover.

## Proof

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_fresh_preparation_v6d.py
```

9 passed in 0.26s. Tests forbid native processes and sockets. Inert generator
ran once to write only new candidate/provenance files; no broad rerun, new
preparation, credential copy, reservation, startup or query. Source/old artifact
files remain unchanged. git diff against HEAD includes older dirty-worktree
changes; this proposal adds only its new recipe/test/artifacts and current docs.

SHA256:

```text
derive_fresh_preparation_v6d.py c95c946323f5a53d15c511009a351398cdfaab3eae19ab69eda09529b756a3e2
test_companion_fresh_preparation_v6d.py b2e3cc6dda6f4a402367b361ebaa3eda6d2f1d06382acf5e3637c0f0ee70cbe6
fresh_baseline_v6d_native/observation.json 735f82278f43416a62adbc7a5d23b1f37decbb96bd557a1d34a50d8c9ebc8321
fresh_preparation_v6d/candidate_manifest.json b09d4fca2d0e41b8b16c5e811031b61910af241620cff5d14238fa39c51a0328
fresh_preparation_v6d/provenance.json 450528ec555d61fca4d3bc6defb94bfaf08ef37b170f18db96f7f2fb94691857
```

## Review And Operational Boundary

Independent review must verify exact derivation, consumer lineage, unused
attempt, baseline equivalence, unchanged application scope and honest modeled
predictions. It may create an accepted-input derivative with only review fields
changed; that does not permit any operation. No acceptance is inferred here.

After review, run the existing preparation CLI in default inert mode with
native/reservation tripwires. Then request one explicit stopped-preparation
operation, if the accepted inputs remain applicable. That future operation may
build/reuse four images, copy existing private service configuration into four
new stopped containers and create persistent cache/log/configuration evidence.
It must not start replacements or interrupt originals/storage. Existing controller
budget is 300 seconds including 120 seconds recovery, not a whole-command hard
deadline; cleanup of owned new resources is attempted, not guaranteed.

Exact new IDs/images/sources require review after preparation. An actual cutover,
internal-token handoff and cited query remain separate. Historical V6c cause is
UNVERIFIED and neither the earlier operation grant nor this proposal authorizes
retry, receipt reset, original/container interference or trading.

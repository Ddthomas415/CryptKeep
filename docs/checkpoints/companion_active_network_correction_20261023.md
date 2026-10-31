# Companion Active-Network Correction, October 23

## Scope And Disposition

Active role: ENGINEER. Risk: HIGH. Objective: correct the offline producer,
loader and runtime pin-comparison contract after the consumed v6b failure.
Implementation state: READY_FOR_INDEPENDENT_REVIEW. Runtime: INCOMPLETE.

SHOWN: this work ran only local, synthetic verification and an inert historical
counterfactual. No Docker command, token read, container preparation, startup,
query, reservation reset, scheduler, account or trading operation was performed.
The four removed v6b IDs remain historical; no candidate here can revive them.

The old assembler, reviewed packets, launcher and failure records are unchanged.
New source hashes invalidate their current-source applicability; this correction
does not refresh any old operational approval or authorize another attempt.

## Change

- `companion_network_configuration.final_model/final_subject` are pure shared
  producer helpers. The model binds the reviewed network ID, declared aliases,
  and the existing configured projection's null/empty-IPAM equivalence.
- `derive_active_network_proposal.py` verifies three frozen input hashes and
  derives seven historical MODELLED candidates, explicitly INCOMPLETE, with
  no policy approval. Storage subjects are copied unchanged. This is a
  counterfactual, not a new preparation manifest or executable packet.
- `companion_cutover.load_inputs` uses the same helper for opt-in application
  pins and requires exact agreement with the plan's network bindings.
- New `companion-runtime-pins-v2` reviews must bind `network_configuration`
  (`contract: configured-network-v1`, immutable name-to-ID bindings) in the
  independently trusted review bytes. Unknown schema/contract/fields refuse.
  V1 review semantics and raw preservation digests remain unchanged.
- The adapter uses the configured digest only for V2 application pins, in both
  compatibility and `_target`. Storage pins and raw inventory/installer/recovery
  comparisons remain raw. Wrong names/IDs/images/sources/configurations refuse.
- A blank observed ID is configured-only evidence, permitted only while created,
  never started, zero integer restarts and restart policy `no`. It is not an
  attachment assertion. Running blank IDs refuse; normal recipient checks still
  require actual attachment before HTTP/query, as before.
- V2 configured compatibility returns bounded checks plus the first evaluated
  precondition category/target. The installer allowlists these and records them
  before refusal/cleanup. Exceptions/timeouts get a fixed stage marker without
  exception text. False checks mean not established or not evaluated, not a
  fabricated trace that every underlying predicate failed.

## Alias And Evidence Limits

The complete expected alias set is exactly the operator-declared aliases.
Existing alias ordering/deduplication semantics are retained; no extra alias,
including a daemon-added container name/ID, is silently stripped. Thus an
unexpected daemon alias fails closed, rather than being guessed equivalent.
The lost activated rows do not establish their actual alias set. Future fresh
preparation must establish/review it before an operational packet is accepted.

Only null/empty IPAM is equated. Nonempty static IPAM remains in the fingerprint.
Configuration equivalence is not connectivity, liveness, successful retrieval or
profitability. The original failure's exact runtime predicate remains UNVERIFIED.

## Verification

VERIFIED_ENV, local venv, bytecode/cache writes disabled. Final targeted command:

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_companion_active_network_contract.py tests/test_companion_network_configuration.py tests/test_companion_cutover_inputs.py tests/test_companion_runtime_adapter.py tests/test_companion_staged_composition.py tests/test_companion_running_update.py tests/test_companion_staged_runtime.py tests/test_companion_installer.py tests/test_companion_staged_update.py
```

SHOWN: 434 passed in 2.82 seconds. No full suite or native integration run.
Cases include blank/correct bound IDs and null/empty IPAM, alias order/duplicates,
extra aliases/static IPAM, wrong identity/image/source, altered flags/health,
review/binding tampering, legacy checks, real-adapter synthetic start/query,
raw inventory preservation, and sanitized failure receipts before cleanup.
The initial focused run found two local defects (new producer manifest key and
empty legacy review handling); both were corrected before the final run.

Inert generator command (new output only, old artifacts preserved):

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_worker_preparation_20261023.derive_active_network_proposal
```

Saved under `active_network_correction/historical_counterfactual.json` in the
worker-preparation review folder. Its SHA256 is
`16be0551161056533bb3cceecf2acb6e2c9913df15504b7a34ea2d3873daf6e6`.

## Source Bindings For Review

| Path | SHA256 |
| --- | --- |
| scripts/research/companion_network_configuration.py | 8b9949055152859636e51f2e2695f4388f77ef8e21d26cc535f879b4ee881bd7 |
| scripts/research/companion_runtime_adapter.py | dcc33a6d454c7d6f9970103ad331d97cd88f2a8023f321cd381a729d2e05f7c7 |
| scripts/research/companion_cutover.py | a9af9918fbde648911e640441ecac0540c932f0e6e7cf467a88af6b4f033cd74 |
| scripts/research/companion_installer.py | 4c684b1766fcb2e21b3dc1c03cbe5aa607694f63b9d64c512a19ad6c11792b17 |
| tests/test_companion_active_network_contract.py | 4efaffccc5ac6f611f1e2bf3649f6422a7972756c9ecda31cf42b0ca645a6e25 |
| tests/test_companion_running_update.py | 6080974d4eb2ea917077fd64d85190cb23f49c2d40ac3d87f27607aa9eb8740c |
| docs/review_artifacts/companion_worker_preparation_20261023/derive_active_network_proposal.py | 4ecaf11cf5cff76c0b40fd1dab13e5e56c9ec5a7216e7f50e1c1a783e71b2eae |

Next proof: separate bounded review of these exact sources, not another service
attempt. Any subsequent preparation needs genuinely fresh IDs/evidence; cutover
needs separate explicit authorization and cannot reuse consumed v6b authority.

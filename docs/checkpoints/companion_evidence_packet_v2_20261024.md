# Fresh offline evidence-packet integration, October 24

Role: ENGINEER. Risk: HIGH acceptance-input draft.
Separate GATE: ACCEPTED_WITH_RISK, offline evidence portion only.
Full executable runtime packet: INCOMPLETE. Not activated.

## Result and boundary

The operator approved fresh offline integration and review, not service actions.
The new draft binds original7 plus independently reviewed witnesses5,47,18 to
the unchanged question, body/identity checks and separately reviewed context
guard. It does not overwrite the old approval list or any consumed packet.

The saved V6d outcome says preparation was consumed and replacement IDs were not
preserved; its saved postcheck reports those IDs absent. These are historical
records, not a new runtime observation. Copying those IDs into a supposedly fresh
executable packet would be unjustified. Therefore no runtime IDs, attempts,
network bindings or dependency approvals are invented or inherited as current.

## Integrated artifacts

New directory: `docs/review_artifacts/companion_evidence_packet_v2_20261024/`.

- `topical_candidates.json`: existing canonical adapter representation of the
  four reviewed records, SHA256 `dc3f5678277fb14afb523d54acfc3ef9303627fb810ad075228702054d18505a`.
  A standalone draft input, not an effective approval-list replacement.
- `runtime_review.draft.json`: actual V2 record schema with decision INCOMPLETE,
  empty reviewer/subjects/dependency approvals/network bindings, SHA256
  `1d7c90eafdce57aba1a28bf4f85b29e7c5873b13ba4a3d97213e1a754cf9d6b0`.
  Binds candidate hash but cannot authorize runtime.
- `evidence_acceptance.draft.json`: non-effective evidence integration linking
  both independent reviews, exact guard source, candidate/draft hashes and
  explicit missing runtime proof, SHA256
  `973a056afed244d0b9825925dd5ff67ce37c886a3b46d10a49d688fb281ccbf0`.
- `proof.json`: 34 selected input/source/history bindings and offline results,
  SHA256 `7bd5a886768f7675399c72e93ce2dbff2f0eb579f34bd5e0d70005fe8309d5c1`.

Existing reviews are reused at their exact hashes and scopes, not extended to
current containers or images. No accepted runtime policy or executable handoff
is generated. All artifacts are exclusively created in a new directory.

## Verification

VERIFIED_ENV, isolated offline command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_evidence_packet_v2.py tests/test_companion_witness_proposal.py tests/test_companion_witness_selection.py tests/test_companion_archive_contract.py
```

**19 passed in 1.01s**, including four new integration cases. Full suite not run.
All34bindings matched after generation. Actual adapter methods were exercised
with no transport and default disabled state:

- Topical record shape passes, including the preserved original7 record.
- Runtime policy validation fails on the incomplete draft.
- Runtime identity validation refuses with `reviewed_pins_missing`.
- Operational entry refuses with `adapter_not_authorized_or_not_bounded`.

The unchanged verifier passes saved top-three/witness7 fixtures and refuses
unproposed1/unverified-body25. Positive evidence flags substitute saved original
rows and synthetic transport/risk; they are not current DB or integration proof.
Review-hash drift prevents generation. No native, socket, process, HTTP/DB,
service, credential or reservation operation occurs in these fixture paths.

## Remaining proof

Independent review accepted this evidence portion only. Completing a full
runtime packet requires separately scoped current read-only baseline/exact-ID
evidence and fresh subject/dependency/runtime applicability review. This need
does not imply automatic container creation: first establish the actual current
state. Any later operation still needs its own bounded authorization. Previous
IDs/attempts must not be reset or reused from historical evidence.

No current runtime state, live explanation success, causal finding, profitability
or trading readiness is claimed. Source/query/guard/verifier/campaign/settings
and effective approvals are unchanged by this integration.

## Independent acceptance

Separate GATE ACCEPTED_WITH_RISK, no findings. Review at
`docs/review_artifacts/companion_evidence_packet_v2_20261024/independent_review.json`,
SHA256 `309d6079cc0aee852cba9678ccc0ea77d782d31503edabf53024f3a99ca7b6ef`.
Reviewer checked all34source/input bindings and reproduced four artifacts byte
for byte. Four integration tests independently passed in0.26s. Parent read the
whole review and verified all38listed source/artifact hashes unchanged. The
parent19test slice was not independently repeated; full suite not run.

The accepted evidence portion remains non-effective. The runtime-policy draft
still says INCOMPLETE and has no accepted identities; neither it nor the review
is an executable authorization. No reviewer fields or decisions in that draft
were changed to manufacture runtime acceptance. The scoped offline integration
is complete, but a full runnable packet and real cited query are not complete.

Next boundary: separately authorize a bounded read-only current runtime inventory
without credential-value export or lifecycle changes, then establish whether
existing identities/source/configuration can support the full packet. Do not
assume a rebuild, another preparation or service interruption is required.

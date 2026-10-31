# V6i Preparation Inputs, October 27

Role: GATE closeout of separate review. Risk: HIGH. ACCEPTED_WITH_RISK
for offline preparation inputs only.
Runtime INCOMPLETE. Offline derivation only; no operational authorization.

## Delivered Scope

Continued the accepted restoration objective using the accepted V6i source
proposal and separately accepted two-read baseline. Reused the V6h derivation
logic, fixed model bytes, Snapshot/network projection, original identity and
configuration checks. Added exact V6i source-review and saved-baseline-review
bindings; both must be ACCEPTED_WITH_RISK with no blockers, and baseline review
must grant no operations. All 11 baseline-review artifacts are checked. The
derivation accepts only the exact reviewed receipt path and digest. Existing
validation is factored into a pure helper for synthetic drift tests.

Generated candidate_manifest.json and provenance.json in
docs/review_artifacts/companion_integration_inputs_v6i_20261027/.
The candidate retains decision INCOMPLETE and blank reviewer; the real Plan
loader refuses it. A temporary synthetic accepted test fixture loads through
the existing parser, but is not exported as accepted evidence.

Seven baseline records retain identities, original images and selected
preservation/configuration/network fields. Only the four application start
timestamps change relative to V6h. All other candidate fields equal the fixed
historical manifest except attempt label and the accepted source proposal's
application entries: exactly one memory-source digest changes. Host verifier
binding changes separately in provenance; 13 preparation tools remain unchanged,
20 runtime consumers retain the one accepted verifier delta, 43 application
entries remain present. Original configured replacement recipes are unchanged.

## Preservation and Limits

Prior manifests/reviews/receipts/captures and the V6i source-only proposal remain
unchanged. New image/replacement IDs are null, not borrowed from historical model
rows. Old consumed attempts are not reset. Current marker absence is an advisory
local observation, not a reservation or guarantee of later action.

New memory source requires actual image identity, original parent/source-only
layer/copy evidence and independent SDK-policy applicability review later. This
input proposal grants none. Existing false REQUEST_TIMEOUT_SECONDS comparison
flags in the four original apps are retained, not passing configuration proof.
The capture establishes selected metadata only, not health, connectivity,
installed repaired code, full restoration, storage contents or a usable query.

## Verification

VERIFIED_ENV for local hashes, pure derivation and synthetic tests only:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6i_current_inputs.py
```

SHOWN: 27 passed in 0.45 seconds, no warnings. Actual candidate/provenance
reproduce byte-exact; tests check full candidate recipe preservation, unapproved
Plan refusal, temporary synthetic Plan compatibility, raw/hash/pair/timing/CLI/
source/identity/image/state/command/restart/network/timeout-flag/storage drift,
reviewed receipt path/hash, bound-evidence drift and invalid baseline review.
First run: 26 passed, one test failed because its synthetic mutation used a dict
index on the flag list. Corrected that test to select the flag by key and reran.
No production or derivation behavior changed for that test correction.

Copied validate_default.py byte-for-byte from V6h for eventual inert validation
after independent input acceptance/export. It has NOT run in this scope yet.
No full suite, capture repeat, native/Docker/CLI/token/DB/application/SDK/build/
preparation/service/trading/risk/schedule/account action. No material assumptions.

## Review and Next Boundary

input_derivation_report.json binds the candidate, provenance, derivation source,
tests, reusable default validator and relative derivation diff. Review exactly
these inputs; do not perform native acquisition or service operations. Independent
review may specify a decision/reviewer-only accepted-manifest export, preserving
the INCOMPLETE candidate, and bind its expected bytes/digest. No self-issued
approval. After such acceptance, run only the existing inert default under
external-operation tripwires. Any stopped-preparation action requires separate
explicit operator authorization; existing budget is 300 seconds including 120
for recovery. Runtime/cutover/query remain separately unauthorized.

## Independent Acceptance and Inert Validation

Separate GATE accepted the exact inputs with risk and no blockers. It reproduced
candidate/provenance/diff byte-exactly, independently ran all 27 tests once
(0.37 seconds, no warnings), and verified the unchanged recipe/inventory and
four-start-time-only baseline disposition. Review: actual_input_review.json,
SHA256 90728d085a259a9cd7757de02431f5a42dc772f2c466b733d7b96ada423e05af.
All 68 review-bound files matched before this documentation-only closeout. The
review/report checkpoint digests now identify the pre-closeout text; reviewed
source/tests/candidate/provenance/diff/report remain unchanged.

Exported reviewed_preparation_manifest.json exactly as the independent review
specified, changing only decision/reviewer. SHA256
3c8066b43cf924374f2338907f306aadec25fdb599a2ef28a068ab0a21632a33 matches
its expected value and loads through the real Plan parser. manifest_export.json
binds the finalized independent review; INCOMPLETE candidate remains unchanged.

Ran the byte-identical existing validate_default.validate() once against that
exact export after checking its review, validator, manifest and source bindings.
The real companion_prepare.main default exited zero, opened the manifest once
read-only, reported actions_executed=false/startup_authorized=false, made zero
external-operation tripwire calls and left both absent markers unchanged.
Saved inert_validation_receipt.json. This parent proof is not independent native
execution or preparation evidence. No full suite or operational command ran.

Offline input objective complete. Next is separate operator authorization for
one stopped-preparation action. It may build/reuse four source-only local images
and privately copy existing configuration into four stopped replacements, with
300 seconds including 120 recovery; no starts/cutover/query. Original apps and
storage remain untouched; cache/config/log effects may persist and cleanup is
not guaranteed. Subsequent actual-ID/image evidence requires review before any
separately authorized cutover. Runtime remains INCOMPLETE.

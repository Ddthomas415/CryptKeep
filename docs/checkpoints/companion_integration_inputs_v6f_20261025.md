# Repaired-source integration inputs, October 25

Role: ENGINEER. Risk: HIGH. Implementation and actual preparation inputs
separately ACCEPTED_WITH_RISK. Default inert validation passed; no execution authority.
Runtime remains INCOMPLETE. No preparation/cutover or query authorized.

## Source refresh

Directory: `docs/review_artifacts/companion_integration_inputs_v6f_20261025/`.

`derive_inputs.py` binds the prior accepted preparation manifest, accepted repair
report/review, prior consumer table and historical network configuration models.
It refreshes exactly two memory-service source digests and one installer consumer
digest. All 43 application entries and 13 tool consumers are checked against
current local bytes. Commands, options, policy flags, source paths/destinations
and intended network configuration remain unchanged.

Script SHA256: `a63572220edfef175873e09ca82647e69131b7a7534011c9b6c84593eb36ce22`.
`source_refresh.json` SHA256:
`241a0f23dee830bdcfe438083cab6065ce9ace482c97b47455d197546e44b780`.

The historical source-refresh intermediate is deliberately not a preparation manifest. Its
baseline is null, decision INCOMPLETE and reviewer blank. It grants no permission
and allocates no reservation. Proposed label workerprep20261025v6f is not an
executed attempt. New container and image identities remain unknown/null.

When supplied a genuine hash-bound paired baseline, the derivation preserves
the original identities, images, running state, restart policy/count, foundation
and configured network fingerprints; it recomputes observed snapshots and
checks historical final-configuration models. Model IDs are historical references,
not adopted replacements. Fresh preflights remain mandatory for any later action.
Both prior V6e reservations remain consumed; no reset or retry is made.

## Actual capture failure and remaining permission

The operator approved two read-only selected-container metadata inspections
within 30 seconds, no credentials, application queries or lifecycle operations.
The first native read completed, then my one-off wrapper asserted that each row
had an empty attempt field. The existing reviewed formatter does not emit that
field. This was my validation error, not a confirmed daemon/service problem.
The process exited 1, and no paired baseline was saved. Raw observations cannot
be reconstructed from that failed process and are not invented here.

`initial_capture_failure.json` records this limited parent attribution. Exactly
one native read occurred under that capture invocation; no services changed.
No automatic repeat was made. A fresh two-read capture with the corrected wrapper
was requested separately and was pending at that stage. Subsequent explicit
approval and the successful capture are recorded below.
No current timestamp/metadata claim follows from the old rollback receipt.

## Verification

VERIFIED_ENV offline:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_integration_inputs_v6f.py
```

SHOWN: 13 passed in 0.34 seconds. Synthetic paired-baseline fixtures only, not
actual new preparation evidence. Legitimate rows without an attempt field pass.
Tests cover exact three-source delta, strict original-state/configuration
constraints, paired/CLI/completeness drift, source/review drift, consumed proposed
label refusal and rejection of an unreviewed candidate by the real Plan loader.
Network/subprocess tripwires remain active, including the consumed-label test.
Full suite not run; old source-bound runtime packet tests were not rerun because
their deliberate source mismatch is already documented.

## Remaining boundary

Implementation/source-refresh review is separate from actual input readiness.
Do not produce a reviewed preparation manifest or call default input validation
with invented timestamps. The formerly missing paired baseline is supplied and
reviewed below. No build, create, private-config copy, reservation,
startup, cutover, endpoint query, trading or scheduling change is authorized here.

## Independent implementation review

Separate GATE ACCEPTED_WITH_RISK for source refresh/derivation implementation
only, no blocking implementation findings. At that review, actual inputs were
INCOMPLETE and the missing paired baseline was an explicit input blocker. Review:
`independent_review.json`, SHA256
`188969cd3a5b439c5fb5d72026795b47808935b2475bb86a16e237d34fa3fabd`.

Reviewer verified five fixed input pins, recomputed all source-refresh entries
and the exact three-path delta, and independently ran 13 synthetic tests in
0.30 seconds. No native capture, actual candidate publication or service action.
Parent read the complete review and verified its five directly listed hashes.
Reviewed source/tests/refresh/failure artifacts remain unchanged.

This completes implementation proof, not the requested real input derivation.
The earlier failed capture remains a parent-attributed error; independent review
does not certify that discarded observation or authorize its replacement. The
corrected capture permission was pending then; later approval is recorded below.

## Approved corrected capture and actual proposal

The operator separately approved the corrected two-read capture. That supersedes
the pending permission statement above, without rewriting the preserved failed
capture record. Exactly two native read-only inspections completed in 0.083 seconds
under a 30-second total and ten-second per-call bound. Existing hash-checked
formatter, fixed seven original IDs, pinned CLI and temporary isolated CLI config
were reused. No service, credential-value, endpoint, DB or lifecycle operation.

Saved each sanitized raw response exclusively before parsing or validation:
`capture_1.jsonl` and `capture_2.jsonl`, both SHA256
`9f363da9f6ea2f802e775f0c5f39270002d26a6add79aa237f2d1055e3e8e0fb`.
`baseline_observation.json`, SHA256
`4795ccaab3368196bfd85fa869ba61bbaaf5dc936f6db64c901222a3c7e0f81a`,
retains the equal seven-row pair, input hashes, UTC capture times and limitations.
No absent attempt field was required or invented. Sequential selected-field
equality is not atomic state, current health or a post-capture guarantee.

The accepted derivation then ran offline against the exact saved baseline:

- `candidate_manifest.json` SHA256
  `7349a21872ebf6536ffadbfc459e935ea4f94a5bf1f9d5ff2608952112c4e311`.
- `provenance.json` SHA256
  `b8c685aac89efc0661a2635e97855b997e8fc77cbd9ab2b029b667f4da3377a7`.

SHOWN from that derivation: original IDs/images/configuration/restart counts and
the three storage snapshots satisfy prior constraints; only the four application
start timestamps changed. Two repaired application source hashes and one repaired
installer consumer hash are updated. All 43 application source entries and 13
consumers match current local files. Commands/options/policies and intended
configuration models remain unchanged. Candidate decision INCOMPLETE, reviewer
blank, no new container/image identities or reservation. `source_refresh.json`
remains the historical source-only intermediate and is not overwritten.

No implementation changed or full test suite reran for this actual capture and
derivation. Capture counts and timings remain parent-observed provenance; the
reviewer verifies saved records, not the original native actions.

## Actual-input acceptance and inert CLI verification

Separate GATE ACCEPTED_WITH_RISK, preparation inputs only, no blocking findings.
`actual_input_review.json` SHA256:
`14372031283e3ae9f9728bc2c68ae6657bf518d750d5752659b7155affc76f4c`.
Reviewer compared both raw captures to the complete observation, checked helper
and input hashes, recomputed the candidate/proof exactly and verified baseline,
source-delta, policy and historical-model constraints. No native call or new test
run was performed by the reviewer. Prior implementation review remains unchanged.

Reviewer produced `reviewed_preparation_manifest.json`, changing only decision
and reviewer from the candidate, SHA256
`a7854b1660ae2c321f8edb62d3ac2b7ab60350deb62df91bdde774e8c2ea1588`.
This accepts inputs, not execution. The four originals' inherited timeout
comparison flags remain false in the captured metadata; acceptance does not
claim every runtime compatibility predicate passes. Fresh downstream checks
remain required, not waived or silently reported fixed.

Parent read the entire actual-input review, verified 50 unique bound files and
the exact allowed manifest delta. Actual `companion_prepare.main` DEFAULT was
then invoked with native/process/socket/backend/token/reservation/lock tripwires
and only one permitted read-only manifest open. Exit 0, actions false, startup
false; proposed preparation/cutover markers absent before and after.
`inert_validation_receipt.json` SHA256:
`40e25254092943f17fc035b9bdba2377211cc67d3434ca91f55f80727ff6ce27`.
The receipt contains the full inert argv and exact result; no execution flag.

The requested capture and offline input/review objective is complete. No new
image/container exists or has an accepted ID. Next decision is separate approval
for ONE stopped preparation using these inputs: four source-only local images
and four new stopped containers, with private existing configuration copied only
through the reviewed mechanism; originals and storage remain running/untouched.
Controller budget is 300 seconds including 120 seconds for recovery. Cache,
configuration and log effects may persist; cleanup is not guaranteed. No pull,
network build access, startup, cutover, query, trading or automatic retry/reset
is implied. Runtime remains INCOMPLETE.

# Actual V6f runtime attempt, October 25

Role: ENGINEER, followed by separate GATE review. Risk: HIGH.
Runtime INCOMPLETE. Saved evidence ACCEPTED_WITH_RISK; no operational acceptance.

The operator's continuation directly followed the explicit one-attempt request;
treated as approval for that exact scope. One reviewed fixed-handoff invocation
in execution session 80673. No automatic retry, preparation repeat, marker reset
or unrelated repair is authorized.

## Scope and preflight

Private reuse of the existing internal service token, graceful stop of four
original research applications, activation/start of the four actual prepared
replacements, existing fresh checks and one frozen-question cited query.
Three storage services/volumes, trading, accounts and schedules stay outside
the mutation scope. Complete success alone permits leaving replacements running;
failure invokes existing owned cleanup/restoration, not guaranteed recovery.

Controller budget 600 seconds including 180 seconds for recovery; separate
ten-second CLI verification and source-token inspection precede it. This is not
a whole-wrapper 600-second wall guarantee. Log/audit writes may persist.

VERIFIED_ENV file/input preflight: 31 independent-handoff-review bindings and
current consumers match, actual pure loader passes, native CLI digest matches
and V6f cutover marker is absent. Existing current identity/source/configuration/
SDK/namespace/recipient/health/archive/lineage/citation gates are not waived.

Exact invocation, once:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6f_20261025.execute_reviewed_v6f --execute-once
```

## Actual result

SHOWN: session 80673 exited 1. The controller reports one query attempted, query
not passed, services started, receipt complete, configuration rollback verified,
exact baseline restoration false and no unresolved tracked recovery actions.
Preparation is consumed and replacement IDs were not preserved. No repeat,
reset, recreation or additional live inspection was performed.

The 96-event receipt shows companion HTTP 200 with five citations and execution
disabled, followed by the dashboard normalizer's foreign_asset rejection and
selection of dashboard_fallback. No evidence_verification_checks event exists:
this attempt failed explanation acceptance before the stored-evidence verifier.
My initial interim description, "failed evidence acceptance again", was too
broad; it must not be read as a second failure inside verify_evidence.

Recovery receipt: configuration_restored true, exact_baseline_restored false,
network_connectivity_verified false. Original restart intentions and the final
configuration comparison do not establish post-recovery health, connectivity,
volume-byte identity or exact restoration. No successful explanation or
profitability claim is made.

## Preserved evidence and offline diagnosis

Files under
`docs/review_artifacts/companion_integration_inputs_v6f_20261025/actual_runtime_v6f/`:

- receipt.jsonl: byte-identical copy of the consumed cutover receipt, SHA256
  9fdc6a9823d45777e591a25b108be4da7bfeadea296daeb50492481cb3acf555.
- outcome.json: explicitly attributed parent transcription of the tool result,
  not independently captured process output.
- diagnose_saved_attempt.py and diagnosis.json: reproducible public-archive
  correlation and three synthetic guard cases with input/source hashes.

Command (VERIFIED_ENV, exit 0):

```sh
env PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6f_20261025.actual_runtime_v6f.diagnose_saved_attempt
```

SHOWN: five saved citation ID/URL hash pairs map to frozen documents 5, 47, 18,
5 and 26; citation names hash-match keyword_5, keyword_47, keyword_18, past_1 and
future_1. The earlier unmatched-document problem is absent from this receipt.
Hashes alone do not establish response prose, field types or topical validity.

SHOWN offline: the real guard recognizes the labelled keyword passage containing
the mixed BTC/ETH title of document 5. Putting the same title in past_precedent
causes foreign_asset rejection; keyword-only and BTC-only-past controls pass.
Current code exempts only the exact current_cause passage, not past_precedent or
future_catalyst. This is a demonstrated compatibility gap. Its status as the
unique runtime triggering field remains UNVERIFIED because prose was not saved.
No raw-runtime replay, SQL/vector ranking, fresh service or DB proof is claimed.
Socket/subprocess tripwires are active during this local diagnostic.

No production source, gate, witness, archive, frozen question or evidence
criterion was changed. No full suite was run for this evidence-preservation task.

## Separate review and next boundary

Independent GATE decision ACCEPTED_WITH_RISK for saved evidence only, with no
blocking findings. Review saved as actual_runtime_v6f/independent_review.json.
The reviewer independently read all 96 events, checked receipt-byte equality,
matched citation/archive hashes and reproduced diagnosis.json exactly under the
offline tripwires (exit 0). Parent rechecked all 17 review hash bindings. No new
native, service, credential, health or query operation was part of this review.

The useful next implementation scope
is a narrow offline contract repair for cited past/future headline context with
negative tests for unsupported foreign-asset narratives, not weakening the guard
or launching another attempt. Any high-risk implementation requires independent
review; another runtime attempt requires separate authorization and fresh inputs.

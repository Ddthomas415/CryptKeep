# Interrupted Claim TTL Correction

Active role: ENGINEER. Risk: HIGH. State: READY_FOR_INDEPENDENT_REVIEW.

Subsequent human decision: operator replied "Approved" when submitting rev57
after this bounded handoff. The bounded TTL correction is ACCEPTED by human
review. This does not accept the remaining 0045 retry risks, integrate either
correction into the supplied series, or authorize merge/deployment.

Objective: close the reproduced 0045 inference that a created claim proves an
order was never sent. Change exists only in the isolated rev56 candidate.
Generated patch: `docs/review_artifacts/shared_submission_review_20261004/rev56_created_claim_ttl_correction.patch`.

A created claim is now treated as possibly sent. An aged intent without a
remote ID in its reason but with unresolved dedupe evidence is held: no TTL
cancellation, no submit, no overwriting of its reason or dedupe row. With no
claim, ordinary expiry still applies. Existing error-state handling is unchanged.

SHOWN: the original real-client/dedupe fake-venue interruption probe passes.
Three repeated-turn tests cover created, unknown and submitted claims, preserving
pending status, reason and dedupe data with zero new exchange calls. Existing
fresh-intent, ordinary-expiry and known-remote tests still pass.

VERIFIED_ENV: local Python 3.12.10, `/private/tmp/cryptkeep-rev56.3fTGQR`.
Command with `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python`:
`-m pytest -q tests/test_codex_rev56_review_probe.py tests/test_live_executor_intent_ttl.py tests/test_live_submit_ambiguous_classification.py tests/test_live_executor_latency_safety_integration.py tests/test_intent_state_machine_contract.py --tb=short`
Result: 62 passed in 1.10s. The independent probe is preserved separately as
`rev56_created_submit_probe.py`; copy into isolated tests under the command's
probe filename. No real venue order, process-kill or operational restart tested.

## Review Boundary

This does not accept or fully repair 0045. Fresh created claims can still reach
the existing retry path, and generic error rows are still considered unsent by
the original helper. Those require separate submission-state/reconciliation
proof. No autonomous resolution of unknown orders is introduced.

The earlier human-accepted remote-ID recovery-before-gates correction is not
included in this patch; this candidate follows the supplied rev56 series.
Integration must preserve both corrections, not silently overwrite either.

Independent reviewer must inspect the hold branch, prove ordinary unsent expiry
and no unknown resubmission, and assess these residual retry-state risks before
broader acceptance. Full suite, CI, remote host and real reconciliation remain
UNVERIFIED. No main source changes, push, merge, deployment or config/account
mutation. No same-thread approval.

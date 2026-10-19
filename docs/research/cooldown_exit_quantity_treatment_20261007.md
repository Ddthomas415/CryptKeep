# Cooldown exit quantity treatment

Independent review outcome: Hume ACCEPTED_WITH_RISK for the combined migration,
runner exception, four-status lookup and quantity correction. No remaining
finding in bounded scope. Reviewer inspected source/tests but did not execute
the111-test run; that remains implementing-agent execution proof. No source or
test edits after review. Deployment/live execution not authorized by acceptance.

ENGINEER, HIGH risk. Isolated candidate:
/private/tmp/cryptkeep-cooldown-review-9wbPbN, based on accepted381bd4776 plus
supplied0001/0002/0006. Original dirty source/index and campaign state untouched.

## Change

Before: held0.1/configured0.5 with full-position false allows0.5 sell through
cooldown. After: exception refused, not silently resized or counted as exit.
_cooldown_exit_quantity requires finite positive held and proposed quantities,
rejects booleans/malformed values, and proposed <=held. Full-position mode uses
held quantity. Submission reuses the authorized quantity exactly.
Non-cooldown sizing, buy transitions, cooldown countdown, accounting and
downstream safety policies unchanged.

## Verification

Original venv Python -m pytest -q -p no:cacheprovider on five isolated files:
test_kill_cooldown_sessions.py, test_kill_gate_protective_exit.py,
test_strategy_runtime_runner.py, test_cooldown_review_protective_probe.py,
test_downstream_exit_review.py:111 passed in5.98 seconds.
Previously failing oversize case now expects no intent and no loss bookkeeping.
Valid full/partial quantities and malformed/zero/negative/nonfinite/bool cases
tested. Downstream tests still show locks block sells, not end-to-end exit proof.

## Limits and handoff

Observed paper holding is not an atomic reservation or independently reconciled
live position. No claim that concurrent runners cannot double-sell. Exception
is bounded locally, not a complete executor risk-reduction authority.
No full suite, real credentials, venue calls, merge, deployment or state reset.
Independent Hume review requested; READY_FOR_INDEPENDENT_REVIEW.
Next stage must resolve review findings before publishing; downstream verified
reduction authorization remains a separate incomplete objective.

# Spot-exit receipt identity checkpoint

Active role: ENGINEER. Objective: bind terminal receipts to durable exchange
order identity in the unwired reservation prototype.

SHOWN: isolated implementation checks order_dedupe venue, intent, symbol and
remote order ID, rejects ambiguous remote ownership, preserves immutable
receipts, and rechecks identity before settlement. Actual-schema fixtures use
OrderDedupeStore. Focused verification: 28 passed in 0.42s.

Candidate: /private/tmp/cryptkeep-cooldown-review-9wbPbN.
Command: original .venv/bin/python -m pytest -q -p no:cacheprovider
tests/test_spot_exit_real_schema.py tests/test_spot_exit_reservations.py.
VERIFIED_ENV: existing interpreter and isolated candidate; temporary test DBs.

UNVERIFIED: exchange provenance, reconciler integration, production bypass,
all-writer coordination, unique position revision, live or full-system behavior.
Receipt observations still come from a trusted internal caller; matching a
stored identity does not authenticate an exchange response. No collector,
config, account, live source, deployment or publication changed.

Acceptance: READY_FOR_INDEPENDENT_REVIEW. Reviewer Hume requested.

Review outcome: Hume found post-settlement receipt replay incorrectly required
an active reservation. Corrected ordering, added replay assertion; 28 tests
passed in 0.38s. Hume re-reviewed correction: ACCEPTED_WITH_RISK, static review
only. This accepts the bounded correction, not live integration or deployment.

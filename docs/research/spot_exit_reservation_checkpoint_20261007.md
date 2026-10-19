# Spot exit reservation checkpoint

## Bounded review correction

Re-review: ACCEPTED_WITH_RISK for the two corrections, no new scoped finding.
Reviewer inspection only;17-test execution remains implementing-agent proof.
Remaining integration limits are unchanged. Nothing published or deployed.

Operator acceptance received, but independent reviewer rejected initial safety
acceptance: retry skipped capacity recheck; infinite freshness bound accepted.
Both corrected in isolated candidate. Retry now rechecks all outstanding
capacity without counting itself twice. Time inputs require nonboolean,
nonnegative integer milliseconds and max age strictly positive.
17 tests passed0.20seconds. Re-review requested; no live wiring or deployment.
User acceptance is recorded, not represented as approval of later corrections.

ENGINEER. Operator continued the recommended verified-reduction scope.
Isolated /private/tmp/cryptkeep-cooldown-review-9wbPbN only; no live bypass.
New storage/spot_exit_reservations.py and tests/test_spot_exit_reservations.py.

One SQLite BEGIN IMMEDIATE checks pending live sell identity, fresh trusted
reconciliation evidence matching local fill-ledger quantity/version, reserves
quantity durably, and accounts for existing reservations and other nonterminal
sell intents. Unknown/error states consume capacity. Exact retries idempotent.
No caller reduce_only metadata used as proof.

10 tests passed0.17seconds. Concurrent connection test with two0.6 pending
sells against1 holding refuses both, not a liveness/fairness claim. No crash
injection/full-suite/live verification. Tests use minimal fixture schema.

Important limits: evidence recording is an internal trusted-reconciler API,
not independently verified venue proof. Producer not wired. No terminal-release
or partial-fill settlement API: retained reservations intentionally strand
capacity until a later reviewed lifecycle treatment. Existing ledger updated_ts
is a provisional version contract. Component not complete authority to bypass
any gate, migrate an operating account or run live.

Independent review requested. HIGH; READY_FOR_INDEPENDENT_REVIEW.

# Approved durable loss-event ordering

Active role ENGINEER. Risk HIGH. READY_FOR_INDEPENDENT_REVIEW.

## Decision and implementation

Operator selected the recommended durable-recording-order contract after the
choice between receipt order and exchange-time order. Order is the canonical
journal's committed insertion order, per symbol across venues, matching the
existing counter scope. Exchange timestamps do not reorder prior decisions.
Late new fills append; duplicate fills retain their existing identity/order.

Canonical sink requires ordered application. Inside the counter/marker's
BEGIN IMMEDIATE transaction, require the matching journal identity and refuse
application when an earlier nonlegacy same-symbol row lacks its loss marker.
No later profit/loss can leapfrog an unresolved earlier event. Duplicate marker
replay remains idempotent. Legacy identities remain excluded by approved cutover.
No history replay, new policy thresholds or lock-expiry semantics introduced.
Low-level direct store calls retain their unordered default; the production
canonical sink explicitly enables the guard. Other callers are not claimed fixed.

## Proof

Actual threaded paused-profit test fails before guard. Afterward newer losses
remain incomplete until the profit settles. Restart with reverse retry order
cannot skip pending losses; ordered retry reaches streak3+lock. Duplicate older
profit replay cannot clear that lock. Expanded seven-file slice: 110 passed,
25 existing datetime warnings, 1.82 seconds.
VERIFIED_ENV: fake venue/temp SQLite, clean environment/null keyring, network
and operator-home data/writes denied except dependency reads.
Candidate/JUnit: /private/tmp/cryptkeep-order-treatment-20261007/source and
/private/tmp/cryptkeep-order-treatment-20261007/order_results.xml.

## Limits

An orphaned/unreplayable earlier fill blocks later symbol-loss updates rather
than guessing. Sink returns not-ok and existing unhealthy-accounting flag;
reconciler durable retries remain necessary. No new orphan repair tool or
automatic journal drain. Position-cost-basis and daily-risk effects have separate
transactions; this bounded correction orders symbol-loss effects only.
No revised full suite/CI/host/power-loss proof. Independent review requested.
No accounts/config/credentials/cohort/process/orders/publication/deployment change.

## Independent GATE

Hume ACCEPTED finding2 correction, bounded to symbol-loss effects in durable
journal recording order, after read-only source/JUnit inspection. No independent
test execution claimed. Reviewer retained the stated orphan, direct-call and
position/daily ordering limits. No new finding within this change.
All three original findings now have separately accepted bounded corrections;
this does not approve their assembled publication candidate or deployment.
Next proof: freeze a revised candidate and run its exact isolated full suite,
then candidate CI and an explicit release decision.

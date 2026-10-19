# Protective exit boundary probes

AUDITOR. Isolated combined0001/0002/0006 review tree only. No venue credentials,
network execution, original source edit or state reset. Fake submission client
raises if invoked; all fixture databases temporary.

## SHOWN

Executor probes: test_downstream_exit_review.py, 2 passed in1.39 seconds.
Pending sell qty0.1, stop_loss reason and reduce_only metadata remains pending
under either canonical symbol lock or market-quality veto. No submission.
This confirms gating behavior, not that the declared metadata proves a real
position reduction. No authoritative position was provided to these probes.

Runner sizing: corrected exit-stack action exit, held qty0.1, configured qty0.5,
sell_full_position false, active cooldown. Runner writes sell qty0.5.
Bounded-size assertion fails:1 failed/1 passed in0.21 seconds. Independent
review identified the same source issue. Intent oversizing confirmed, not
exchange oversell or real-money loss.

## Treatment recommendation

First constrain the runner cooldown exception to finite positive sell quantity
no greater than verified held quantity. Preserve original configured quantity
outside this exception unless explicitly scoped; do not silently cap/change
entry sizing, retry or crossover behavior. Test zero/negative/nonfinite/unknown
positions and quantities, full-position and partial exits, and unknown queue.

Then separately define canonical executor verified-reduction authorization:
exact venue/symbol reconciled holdings, outstanding sell reservations and
concurrency-safe quantity bounds. A side=sell or reduce_only metadata claim
alone must never bypass a risk lock. Keep authentication, arming, reconciliation,
order validity and global emergency policy explicit. Market-quality entry veto
is not automatically equivalent to every hard stale-data safety requirement.

Do not deploy combined patch until these boundaries are addressed and reviewed.
Existing protections are not disabled by these tests. Overall INCOMPLETE.
No full suite, actual venue submission, live protective exit or deployment proof.

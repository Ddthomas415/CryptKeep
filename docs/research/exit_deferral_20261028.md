# Preservation-first exit planning: offline implementation

2026-10-28. ENGINEER stage, HIGH risk financial/retry logic.
Status ACCEPTED_WITH_RISK after separate review of the exact pure, unwired
offline planner. Original Fix2 runtime repair INCOMPLETE.

## Adopted Scope

Operator continued the explicit proposal to implement preservation-first exits
offline with explicit freshness/retry bounds. This adopts the model contract,
not numerical operational settings, execution wiring, a schedule or trading.
No market exit may be silently converted, repriced, marked filled or discarded.

Added services/execution/exit_deferral.py and tests/test_exit_deferral.py. No
existing callers, order router, cache, state schema or retry helper changed.
The existing retry helper sleeps/imports SDK; this pure planner does neither.

## Contract

ExitPolicy requires positive integer metadata receipt-age limit, base retry
interval, retry ceiling and maximum attempts. No live defaults are supplied.
The ceiling cannot be below the base. Fixture numbers are not live settings.
Progress must match venue, product and intent identity. Exact nonnegative
quantities reject floats, booleans and nonfinite values; rational arithmetic
preserves tiny remainders. Original intent/type/price/progress stay unchanged.

- Unknown, stale, future-dated, wrong-product or malformed metadata defers.
- Offline/disabled/view-only/cancel-only defers. Limit-only defers market exits;
  an already specified limit exit may be reassessed unchanged. Auction/post-only
  modes are unsupported and deferred, with no invented auction/maker policy.
- Open/uncertain orders require existing reconciliation regardless of budget.
- Caller-confirmed cancelled partial fills are reassessed only for their exact
  remainder. Full quantity requires caller-confirmed terminal filled outcome.
- Prior attempts impose capped exponential waiting. Exhaustion requests operator
  attention without expiry, liquidation or abandonment. Planning never counts
  as a submit or increments attempts.

Plan statuses are DEFER, RECONCILE, NEEDS_OPERATOR, COMPLETE and
ELIGIBLE_FOR_EXISTING_GATES, not new persisted order states. Every output has
request=null, execution_authority=false and evidence_authenticated=false.
Deferred/reconcile/operator outputs include an alert event value with
delivery_verified=false. No event is persisted/delivered. Existing arming,
risk/funding/ownership/precision/dedupe gates remain required.

## Proof And Limits

VERIFIED_ENV, repository venv, synthetic inputs, socket/DNS guards:

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_exit_deferral.py

Author final41passed0.20s,exit0; initial38passed0.19s before three identity cases.
Coverage includes modes/clocks/schema/identity, unchanged deep copies, retry
boundaries/count ceiling, uncertain/partial/terminal cases, a 10^-30 remainder
and saturated exponent. No full suite, backtests or existing72case rerun.

Two caller assertions are NOT independently proved: metadata origin/receipt
clock quality, and durable/reconciled progress/fill correctness. Identity fields
detect mismatches, not authenticity. Receipt age is not exchange publication
age or proof a cached payload is current. Counter reset, stale fill evidence,
concurrent workers/crashes need durable integration; this pure function cannot
enforce real attempt budgets or exactly-once alerts. No transport/recipient
policy is supplied because nothing is fetched. Live numbers, alert persistence
and deduplication remain open. A sell label is not proof of ownership/reduction.
Do not submit the original full quantity after a partial fill; no request is
built. Malformed inputs raise ValueError, not an eligible result.

No account/credential/network, service/scheduler/pilot, capital/risk setting,
trading, schema/migration, dependency, commit or push action. Freeze source/tests
and this checkpoint under review_artifacts/exit_deferral_20261028/ for separate
GATE. No runtime integration or original funding-rate Fix3 repair follows.

## Actual Independent Acceptance

Reviewer01a11481-515d-7473-8ee3-7f6864c6d40b, submission
01a18427-5a10-75d1-8e60-f55708926013, returned ACCEPTED_WITH_RISK for the exact
pure, unwired offline planner. No material blocker found. Verified all eight
bindings/reproduced new-file diff; independently ran the bound command once:
41passed0.18s. No edits/private/network/SDK-client/runtime operations.

Accepted source SHA256:
22dd6c99b34a0cdf011aea601bb46a878e8aa012e962e2d29f25e5bbdb446679.
Accepted tests SHA256:
a9f97e2562a5ac1cd1cb2949287bfb33fa54247cf8a6027b8159abcbb31c23b0.

No reviewed code/tests changed afterward. Submitted checkpoint and original
BINDINGS are preserved; CLOSURE records the later disposition. Reviewer retains
caller-assertion, durable-counter/fill/clock and confirmed-remainder limitations.
This acceptance is not live settings, alert delivery, execution wiring or a
completed runtime Fix2 repair. Original funding-rate Fix3 remains open.

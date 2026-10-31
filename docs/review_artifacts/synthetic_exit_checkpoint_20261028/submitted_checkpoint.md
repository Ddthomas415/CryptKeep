# Exit checkpoint prototype: isolated SQLite state

2026-10-28. ENGINEER stage; HIGH risk concurrency/financial state.
Status READY_FOR_INDEPENDENT_REVIEW. No production integration.

## Authorized Implementation

Operator continued the explicit request for an isolated-key checkpoint
prototype using disposable databases only, testing atomic reservation/restart
recovery without changing existing databases or execution wiring.

Added scripts/research/synthetic_exit_checkpoint.py and
tests/test_synthetic_exit_checkpoint.py. Reuses the accepted plan_exit function
unchanged and the existing live_consumer_state(k,v) schema/BEGIN IMMEDIATE
transaction pattern. It does not import production store constructors, locate
a database, create/alter tables, modify intent metadata or call an SDK/client.

## State Contract

Keys have a synthetic_exit_checkpoint prefix plus explicit venue/account/intent
scope. Stored intent and policy are retained; progress is bound to that identity.
All schema/state fields must exist. Missing or corrupt state never initializes
or resets a counter. initial_fixture_state returns test seed data only, with
no write operation or authority to initialize historical/live intents.

On an eligible plan, one transaction reserves a conservative potential attempt,
increments the persisted count and records unknown outcome plus a scoped token
before returning. This count includes reservations that never result in a send.
That can consume budget conservatively; it is not an observed-submission count.
Two cooperating writers serialize through SQLite. A compare-and-update checks
that the same row was written. A reserved outcome remains uncertain across
restart; no elapsed-time release or reset/reconciliation API is implemented.
Only a future separately reviewed reconciliation integration may settle it.

Deferrals/operator/reconciliation decisions retain alert event records keyed by
scope/event/attempt. Repeated identical events do not replace their first-recorded
time. delivery_verified stays false; no channel, consumer or acknowledgement
protocol is implemented. State input/output byte budgets are explicit and reject
oversize data rather than truncate it. Corrupt evidence is left unchanged.

No eligible/reserved result is returned before successful commit. A write error
returns INCOMPLETE without a token. An uncertain commit acknowledgement also
withholds success; a committed reservation remains unknown on the next read.
Only an owned transaction is rolled back; caller transactions are not reset.
Rollback failure raises a sanitized error rather than reporting success.

All results have request=null and execution_authority=false. Original intent
is preserved, while confirmed remaining units are separate. A future caller
must never send the preserved full quantity after a partial fill. This prototype
does not create an order, authorize a reducing sell or independently prove fills.

## Verification

VERIFIED_ENV: repository venv, actual SQLite in temporary fixture paths only;
invented account/metadata/fill state and socket/DNS refusal:

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_synthetic_exit_checkpoint.py

Author final23passed0.39s,exit0; initial19passed0.27s. Includes two real SQLite
writers on separate connections, reconnect, account isolation, missing/corrupt/
duplicate-key state, policy/clock regression, unowned transaction, byte budgets,
partial-fill fixture, exhausted attempts, alert deduplication, failed and
uncertain commit acknowledgements. Two bounded child processes exit at code73
immediately before/after COMMIT; before-commit state rolls back, after-commit
state requires reconciliation. Each child has a five-second timeout and network
entry-point guards; neither is a service/background job. Not an OS power-loss,
production-PRAGMA or distributed-node durability test.

## Remaining Limits

Two material assertions remain unproved: caller scope/metadata/fill truth, and
exclusive cooperation with this state protocol. A malicious or unreviewed
writer can rewrite/delete valid state. Row hashes/tokens bind content, not
authenticated account identity. Actual execution DB/KV co-location, cross-store
atomicity, startup/cutover/initialization, dedupe/remote-order linking and durable
reconciliation remain INCOMPLETE. SQLite wait behavior comes from the supplied
connection; no hard operation deadline is imposed by this prototype.

All numeric policy/state-size values are explicit fixture inputs, not live
defaults. No real database, migration, account/credential/network request,
services/scheduler/pilot, trading/capital/risk setting, dependency/commit/push
changed. Existing accepted source/prototypes remain unchanged. Original Fix2
runtime repair and original funding-rate Fix3 are still INCOMPLETE. Freeze new
source/tests/checkpoint and exact diff/hashes for one separate GATE review.

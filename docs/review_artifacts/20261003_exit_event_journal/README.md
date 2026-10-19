# Ordered exit-event journal prototype

GATE / HIGH. Storage primitive: ACCEPTED_WITH_RISK by explicit human approval
on 2026-10-03, not same-thread independent review.
Accepted prototype.patch SHA256:
`e7b83d2277dab4bbc09dff2cbcdb106fa7365b780f8e1402d3e9a9a1e618d470`.
Overall rev29 correction: INCOMPLETE. This is NOT wired into the runner and
does NOT resolve the end-to-end failure yet. Do not deploy as a finished fix.

prototype.patch applies on the rev29 isolated tree. It adds an event table
alongside strategy state with unique intent identity, ordered pending events
per scope, immutable payload checks, and an applied/unwritten marker.
Counter calculation and event settlement share one SQLite write transaction.
The reducer reads current counters, not precomputed absolute totals.
No stop-state reset or protective-order suppression is introduced here.

Verification: Python 3.12 in /tmp/cryptkeep-rev29.HusaTo,
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1:
`python -m pytest -q -p no:cacheprovider tests/test_exit_event_journal.py`
6 passed in 0.16s: two-event recovery with third-loss kill in a simplified
reducer, replay, ordering, scope independence, unknown confirmation rejection,
unwritten event, conflict and reducer-failure behavior.

These tests use real SQLite but a simplified counter reducer. They do not
prove production kill-policy equivalence, queue confirmation, power-loss
durability, concurrent runners, or engine integration. Existing SQLite NORMAL
synchronous policy is inherited. No data was migrated on the operator account.

Required next work after this bounded human acceptance:
- Integrate validated reference-price facts and actual performance reducer.
- Preserve legacy pending evidence without silently dropping malformed plans.
- Resolve ambiguous queue outcomes; do not equate unavailable with unwritten.
- Ensure unavailable journal/recovery does not prevent protective orders while
  unresolved performance authority continues to block new exposure.
- Test failure after queue commit, after counter commit, failed journal writes,
  multiple unresolved events, stop ownership and restart with real stores.
- Rerun the original runner-level lost-kill probe; it still fails on this tree
  because runner integration is intentionally not yet performed.

No main production code/config/state/deployment changed. This checkpoint is a
reviewable storage component, not acceptance of 0018 or a claim of completion.

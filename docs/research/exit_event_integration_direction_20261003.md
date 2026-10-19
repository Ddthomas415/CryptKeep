# Unified exit-event integration direction

DIRECTOR / HIGH. Design recommendation, not implementation acceptance.

Read Claude's exit_event_journal_review_claude_20261003.md and supplied
claude_review_probe.patch. Agree with F1/F2 as integration gaps and retain F3-F5
as requirements. External 13-test results were not rerun in this reconciliation.
Probe p9 kills the child during reducer evaluation before returned counter
updates are written; it does not alone demonstrate a kill after the first SQL
counter update. Probe p2 separately tests rollback after partial updates.

Status correction: rev30/0019 WAS reviewed, with disposition INCOMPLETE in
rev30_restart_review_20261003.md. Restart simulation emitted a buy after a
third losing sell's event was left only in intent metadata. The primitive's
bounded human acceptance does not override that runner-level failure.

## One implementation direction

Use the row-per-event journal as the storage foundation. Adapt 0019's useful
runner behavior and failure tests, not its JSON-list persistence or volatile
degraded-state protection. Preserve the original patches/reports as evidence;
do not stack two independent accounting systems or deploy either as complete.

Required contracts:

1. Durable confirmation independent of reduction order. A later intent can be
   confirmed written while an earlier event remains unresolved. Counter
   application remains ordered with permanent per-event applied markers.
2. Explicit quarantined evidence. Preserve raw malformed data and expose its
   unresolved status; do not call it unwritten to unblock the scope. Quarantine
   is not permission for later events to bypass uncertain accounting order.
3. Startup reconciliation from intent metadata before new exposure. A state
   store outage must not erase risk authority on restart. If complete evidence
   or authoritative ordering cannot be established, refuse entries while
   retaining the protective-exit path. Missing queue evidence is not automatically
   proof that a write never committed (retention and queue authority matter).
4. Restrict the production reducer to validated performance-counter keys and
   values. It must not alter stop ownership, risk thresholds or unrelated scopes.
5. Counters and permanent event markers commit in one transaction, calculated
   from the counters within that transaction. Labels remain provisional
   intent-reference-price metrics, never reconciled realized PnL.

Proof must cover the rev28 failed-write probe, rev29 lost-kill probe, rev30
restart-bypass probe, later confirmation before earlier resolution, malformed
payload preservation, replay beyond 50 events, failure after a counter SQL
write, ambiguous commit, multiple symbols and protective exits during faults.
Use real stores and actual child-process restart tests where appropriate;
stub-only equality is not end-to-end acceptance.

Stop-basis and position-identity issues remain separate. No new acceptance of
0017-0019, campaign launch, account reset, merge or deployment is recorded.
Next engineering scope: extend and independently review this single journal
contract, then integrate against all three failure probes. No parallel competing
runner repair should be started merely to keep another agent occupied.

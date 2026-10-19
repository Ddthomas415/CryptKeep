# Review of Codex's exit-event journal prototype

Reviewer: Claude (separate thread, not the author). Role: AUDITOR, read-only.
Requested by the operator 2026-10-03 ("Review Codex's component").
Subject: docs/review_artifacts/20261003_exit_event_journal/prototype.patch
(SHA256 e7b83d2277dab4bb...), README alongside it.
Scope: the storage primitive only. It is not wired into the runner; nothing
here is a statement about end-to-end behaviour.

Disposition: no blocking defect found IN THE PRIMITIVE AS A PRIMITIVE.
Two gaps (F1, F2) must be closed before it can carry the runner integration
its README lists. This is one reviewer's bounded read; not acceptance.

## What was run

Cloud clone, Python 3.12.3, PYTHONDONTWRITEBYTECODE=1,
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, tree = 97c24c8e4 + 0001-0010 + 0012-0018
(the rev29 tree, 8097b063 here) + prototype.patch.

- tests/test_exit_event_journal.py (Codex's): 6 passed.
- 13 probes of mine, real SQLite, one with a real SIGKILL in a child process:
  13 passed. Each asserts the behaviour stated below, so "passed" means "the
  behaviour is as described", including for the two gaps.
  Durable copy: docs/review_artifacts/20261003_exit_event_journal/claude_review_probe.patch

## SHOWN to hold

- Commit is real. The state connection is opened with isolation_level=None;
  BEGIN IMMEDIATE ... con.commit() does commit (rows read back from a second
  connection).
- All or nothing. A reducer that fails part-way through its updates leaves the
  counters and the event untouched. A process killed with SIGKILL inside the
  transaction leaves the event pending and no counter written; a later settle
  applies it once.
- An interrupt raised immediately AFTER the commit leaves the event applied
  and the counter written; the error still surfaces.
- Order. A later event cannot be settled ahead of an earlier pending one.
- Exactly once. A second settle of an applied or unwritten event returns
  False and changes nothing. This holds for every event ever recorded, not
  for a recent window.
- Identity. The same intent id with a different payload or scope is refused.
- Non-finite numbers are refused at prepare (allow_nan=False).
- A locked database fails after 5.0 s with "database is locked", the same as
  every other state-store call; nothing is half-written.
- Cost. 3000 prepare+settle cycles: settles took 3.9 s in total; listing
  pending events over 3000 applied rows took 0.5 ms. Rows are never pruned;
  at this strategy's cadence that is not a practical concern.

## Findings

F1 (gap, blocks integration). There is no durable "confirmed written" state
for an event that is not first in line.
  SHOWN (probe p5): events a, b pending; the caller knows b was written
  (upsert returned). settle(b, written=True) raises earlier_exit_unresolved,
  and nothing in the table records that b was confirmed. After a restart, b's
  confirmation has to come from the queue again. In the rev29 lost-kill
  scenario the queue cannot be read, so neither event could be applied and
  the expected ('3', True) is not reachable with this primitive alone,
  whatever the wiring.
  Needed: a confirmation that can be stored regardless of order (a column or
  a 'confirmed' status), with application still strictly in order.

F2 (gap, blocks integration). A payload that cannot be read stops the scope,
and the only way past it discards the event.
  SHOWN (probe p6): with one corrupt payload row, pending(scope) raises
  JSONDecodeError for the whole scope and settle(written=True) raises too.
  settle(written=False) succeeds and marks it 'unwritten', i.e. the event is
  dropped. That contradicts the README's own requirement not to drop
  malformed evidence silently.
  Needed: a status that sets such a row aside without applying or discarding
  it, and pending() that reports it instead of raising.

F3 (low). The reducer contract is not enforced.
  SHOWN (p11, p12): the reducer can write any key, e.g. a stop-state key, and
  a None value is stored as the string 'None'. It cannot delete a key. The
  docstring says it must only compute counter updates. Either restrict the
  keys it may return or state that the caller owns this.

F4 (note). 'unwritten' is permanent. If a confirmation of "not written" was
  wrong, the event can never be applied. Correct for a primitive; the caller
  must never pass False on an unreadable queue. The type check on `written`
  guards None but not a wrong False.

F5 (note, for integration). prepare raises ValueError for a non-finite
  payload before anything is stored. The runner must not let that stop a
  protective sell.

## Comparison with patch 0019 (bundle rev30, this thread's own work)

Stated by the author of 0019, so weigh accordingly.

| | Journal prototype | 0019 |
|---|---|---|
| Event store | table row per event, permanent status | one JSON list per symbol, rewritten whole |
| Applied marker | permanent, per event | last 50 intent ids |
| Counter read | inside the write transaction | read, then one write transaction |
| Payload identity check | yes | no |
| Durable "written" evidence | NO (F1) | yes (`written` mark) |
| Unreadable evidence | stops the scope (F2) | set aside under its own key |
| Non-finite PnL | refused at prepare | set aside, never counted |
| Wired into the runner | no | yes |
| Entries refused while unsettled | n/a | yes |
| Failure tests at runner level | none | 43, plus Codex's two probes |
| Reviewed by Codex | own work | not yet |

The journal is the better store. 0019 has the two things the journal lacks
(F1, F2) and the runner wiring, on a weaker store. They are not rivals: the
sound result is the journal, extended for F1 and F2, carrying 0019's wiring.
That is a recommendation for the operator, not something this review does.

## Not verified

Runner integration, the production reducer, kill-policy equivalence, queue
confirmation, power-loss durability (synchronous=NORMAL, inherited),
concurrent writers beyond a single lock test, Hetzner, CI.

No production code, configuration, account, campaign or deployment changed.
Two files were added to the operator's checkout: this document and the probe
patch. Codex's files and the work log were not edited.

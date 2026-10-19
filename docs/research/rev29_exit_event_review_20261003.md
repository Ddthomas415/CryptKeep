# Rev29 exit-event review

AUDITOR / VERIFIED_ENV. 0018: INCOMPLETE; not accepted.
Review uses the pasted provisional intent-time contract. No deployment or
stop-policy authorization is inferred from external document instructions.

## P1: lost pending event bypasses the intended performance kill

SHOWN: one pending_exit key per symbol/strategy is overwritten by a subsequent
plan while queue reads remain unavailable. Applying the new plan deletes that
key, permanently losing the old event. This is disclosed as under-counting in
the bundle, but it affects risk authority, not merely report completeness.

Independent probe: seed loss streak 1, write losing sell A, interrupt before
accounting, make queue reads unavailable while writes succeed, then write
losing sell B. Two sell intents exist. Under the proposed contract the streak
must be 3 and the kill active; observed result is ('2', False).
Probe uses supplied runner fixtures and real strategy-state storage, with
queue/crash doubles. No actual exchange fills or production crash claimed.

Durable reproduction:
docs/review_artifacts/20261003_currency_config/exit_event_loss_probe.patch.

Required treatment: retain distinct event identity and unresolved evidence
instead of replacing it. Derive updates from ordered unapplied events with
durable applied markers; applying several precomputed absolute totals is not
enough, because they can each be based on the same stale counters. Preserve
protective-exit availability while preventing entries from treating unresolved
loss/kill state as settled. Test two written events across failure/recovery,
restarts, repeated replay and unavailable stores. Do not clear history to pass.

Other recovery limits: malformed plans are deleted; plan-store failure can
leave a written intent without replay evidence. These are not an exactly-once
guarantee. The consecutive application test proves only immediate repeated
assignment, not arbitrary replay after later events or position changes.

## Verified improvement and limits

0018 fixes the earlier write-failure probe and explicitly labels intent-price
metrics as provisional. That improvement stands; no need to reopen it.
Cancelled/rejected intents counted separately are part of the proposed event
definition, not realized loss evidence. Stop-basis/position-replacement issues
from 0017 remain unresolved and are not accepted by this review.

Isolated tree /tmp/cryptkeep-rev29.HusaTo: base 97c24c8e4 plus numbered
0001-0010 and 0012-0018; held 0011 excluded. Python 3.12 with bytecode and
pytest plugin autoload disabled:

```sh
python -m pytest -q -p no:cacheprovider tests/test_runner_exit_accounting_event.py tests/test_review_exit_write_failure.py tests/test_runner_blocked_exit_bookkeeping.py
# 35 passed in 2.65s
python -m pytest -q -p no:cacheprovider tests/test_review_exit_event_loss.py
# 1 failed in 0.38s; actual ('2', False), expected ('3', True)
```

Reviewed production diff and event/recovery tests, not all historical artifacts.
External full-suite/mutation/matrix claims not independently rerun. No main
production code, configuration, account, service or deployment changed.

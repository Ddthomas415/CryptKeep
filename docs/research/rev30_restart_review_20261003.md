# Rev30 exit-event recovery review

AUDITOR / VERIFIED_ENV. 0019: INCOMPLETE. No deployment acceptance.

## P1: process-local degraded flag loses entry protection on restart

SHOWN using a focused restart simulation: seed two losses; fail pending-event
writes and atomic state apply; write the third losing sell. Its event remains
only in intent metadata. Restore storage, clear _EXIT_ACCOUNTING_DEGRADED
(emulating a fresh process), mark the queued sell filled, and supply a new buy
signal. Actual emitted sides: ['sell', 'buy']; expected: ['sell'] until event
recovery establishes the counters and owed kill. The evidence exists but there
is no queue-metadata replay on startup. The disclosed limitation therefore
allows new exposure past unresolved risk state; it is not merely lost reporting.

The test uses real strategy state with supplied queue doubles and an emulated
restart, not a killed OS process or real exchange. Durable reproduction:
docs/review_artifacts/20261003_currency_config/restart_degraded_probe.patch.

Required next correction: discover/reconcile intent-carried unapplied events
before permitting entries after restart, using durable event identity and
ordering. If replay evidence cannot be established, entries remain refused;
protective exits must remain available. Do not count an uncertain queue write
as fact, discard evidence, or change stop policy to make the test pass.

## Improvement and implementation distinction

The earlier lost-event/kill probe passes now, as does the queue-write probe.
0019 keeps an ordered JSON list and recent applied IDs in strategy_state. It
does not integrate the separate accepted ExitEventJournal storage prototype.
That component's acceptance cannot be transferred to this implementation.
The 50-ID retention policy is not an unlimited replay guarantee; this review
does not assert a newly reproduced old-event replay failure.

## Proof and limits

Clean archived 97c24c8e4 plus numbered 0001-0010,0012-0019 in
/tmp/cryptkeep-rev30.uPUi4E; held 0011 excluded. Python 3.12, bytecode and
plugin autoload disabled, pytest -q -p no:cacheprovider:

- tests/test_runner_exit_accounting_event.py tests/test_review_exit_event_loss.py
  tests/test_review_exit_write_failure.py: 45 passed in 3.52s.
- tests/test_review_restart_degraded.py: 1 failed in 0.46s as above.

Reviewed the production diff and event/failure tests. External full-suite,
mutation and matrix counts remain CLAIMED. No CI, actual process-death,
multi-symbol or Hetzner proof. Set-aside resolution, stop-basis and prior
position-identity risks remain open. No production/config/account/deployment
changes. Next scope is restart replay, not another unrelated feature.

# Rev28 exit bookkeeping review

AUDITOR / VERIFIED_ENV. 0017: INCOMPLETE; not accepted for deployment.
0016 retains its prior ACCEPTED_WITH_RISK disposition. Its unreviewed label
in the external handoff is stale.

## P1: queue failure still records an unwritten exit

SHOWN: 0017 moves the open-intent scan ahead of loss/stop bookkeeping but
leaves that bookkeeping before qdb.upsert_intent. In an isolated regression,
upsert_intent raises an injected write failure: no sell is emitted, but
loss_streak is already '1'. The claim that bookkeeping occurs only for a
written sell is false. This failure mode is inherited, not newly introduced;
0017 narrows one trigger but does not satisfy its stated write-success contract.

Durable probe: docs/review_artifacts/20261003_currency_config/exit_write_failure_probe.patch.
It uses the delivered holding fixture and actual strategy-state storage with
a mocked failing queue write. No real exchange fill or production failure claimed.

## Accounting and behavioral boundary

The new tests call these counters realized PnL, yet they update on intent
creation using a reference price. A queued order is not a reconciled fill.
Moving updates after enqueue alone would still not establish realized PnL or
crash-safe exactly-once processing across separate stores.

Before acceptance, define these as explicitly provisional intent metrics or
derive realized performance from reconciled fills, with stable event identity
and idempotency. Do not silently change kill-policy semantics under a small
ordering patch. Add failure/restart and reconciliation tests for the chosen
contract, while preserving protective-exit eligibility.

Retaining stop state is deliberate but is not proof that the stored reference
belongs to the current position. The external 39 lost-sell and replaced-position
cases require position-identity/stop-basis review; those matrix counts remain
CLAIMED here. No approval to silently choose a different stop basis is inferred.
Held-back signal sells, duplicate-sell detection and stuck rows remain separate.

## Verification and scope

Clean archived base 97c24c8e4, numbered 0001-0010 and 0012-0017 applied in
/tmp/cryptkeep-rev28.xv5Unu. Held 0011 excluded. Python 3.12, bytecode disabled,
plugin autoload disabled, pytest -q -p no:cacheprovider.

- test_runner_blocked_exit_bookkeeping.py, test_runner_entry_open_intent.py,
  test_review_pending_statuses.py, test_runner_multi_symbol.py:
  84 passed in 6.37s.
- test_review_exit_write_failure.py: 1 failed in 0.45s, as above.

Reviewed production diff and supplied blocked-exit tests. External full-suite,
6762-cell matrix and 73/75 differential results were not independently rerun.
No production code, config, account history, service or deployment changed.
Next: resolve the exit-performance event contract and write-failure recovery
before accepting 0017; do not call the isolated blocked-intent fix full repair.

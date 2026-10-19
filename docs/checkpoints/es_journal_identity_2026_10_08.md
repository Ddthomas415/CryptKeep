# ES journal identity checkpoint

Implementation role: ENGINEER. Separate GATE: ACCEPTED_WITH_RISK.

This bounded slice preserves original paper-order identity alongside newly
journaled fills. It adds `journal_fill_identity` in the same SQLite database,
with fill and sidecar inserted in one transaction. Duplicate fill delivery
does not modify the first evidence or retroactively label historical rows.
Existing journal schema/rows remain readable without identity.

Reconciliation uses the original paper order, not current runtime config or
mutable queue metadata. It validates payload/self-hash and order market, then
marks the copy `journal_identity_status: order_policy_only` and
`fill_cost_policy_verified: false`. Malformed identity produces an invalid
marker, not a trusted payload. Legacy absent metadata adds no identity field.

This is not propagation of the fill logger's verified-cost label: that logger
and the journal follow different paths. Durable fill-time policy verification
must be established before treating journal identity as qualified evidence.
No strategy qualification gate was changed and no cohort was activated.

SHOWN: 40 targeted tests passed in 0.89 seconds using isolated state:

```sh
CBP_STATE_DIR=/private/tmp/es-journal-identity-20261008 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest --noconftest -q -p no:cacheprovider tests/test_journal_execution_identity.py tests/test_intent_reconciler.py tests/test_intent_reconciler_fill_journal_order.py tests/test_paper_fill_identity.py tests/test_paper_engine_integration.py
```

Tests include real queue, paper-fill and journal SQLite databases; matching,
mismatching and absent identity; replay; serialization-failure transaction
rollback; corrupted sidecar JSON; and initialization against legacy schema.
The outcome logger is mocked; the producer/consumer and fill-JSONL chain are
not exercised end to end by these tests. No operator database was opened.

UNVERIFIED: concurrent writers/crash injection, durable fill-cost verification,
qualification-gate exclusion, full suite, CI and deployment. New sidecar storage
failure can prevent journal insertion/queue completion, but does not undo or
block the already completed paper fill. Reconciliation can retry; insertion is
atomic and idempotent. No cleanup, destructive migration or historical backfill
is authorized. Independent review required before dependent implementation.

Separate GATE Averroes subsequently reproduced 40 passed in 0.82 seconds and
accepted this journal slice WITH_RISK. The operator then supplied
`INDEPENDENTLY_REVIEWED AND ACCEPTED`. Neither accepts cohort activation,
deployment, or the still-unverified durable fill-cost bridge.

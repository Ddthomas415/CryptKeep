# Durable paper-fill identity: storage slice

ENGINEER; HIGH risk; READY_FOR_INDEPENDENT_REVIEW. No deployment or activation.

The prior engine added verified cost-policy identity only to best-effort JSONL
after accounting. This slice stores the same detached evidence in the existing
paper_state table under fill_execution_identity:<fill_id>, in the transaction
that creates the fill and updates cash/position/order status. No schema change.
Only new fills receive evidence. Retry paths cannot relabel an existing fill;
legacy absence stays absent. A getter returns an invalid-storage marker for
corrupt content, not a verification claim.

Engine-generated invalid identity remains an invalid marker, not an order veto.
Database or evidence serialization failure rolls back the whole transaction;
the accounting write must not succeed while claiming evidence was persisted.
This means storage failure can delay a paper fill, including a paper exit.
This is not a new live execution path and does not bypass any protective exit.

Evidence still means agreement with declared paper fee/slippage policy, not
real exchange costs, actual slippage, authenticity or promotion eligibility.
The existing reconciler still emits order_policy_only; journal transfer and
gate eligibility remain separate unfinished work. No historical backfill.

VERIFIED_ENV: isolated temporary SQLite tests. Command:

```
./.venv/bin/python -m pytest --noconftest -q -p no:cacheprovider tests/test_paper_fill_identity_durability.py tests/test_paper_fill_identity.py tests/test_journal_execution_identity.py tests/test_paper_engine_integration.py tests/test_paper_engine_limit_and_status.py
```

46 passed in 1.05s. Covers reopen, retry, legacy no-upgrade, corrupt reads and
serialization rollback, alongside existing engine and journal tests. Full suite,
power-loss durability, deployment and end-to-end gate qualification unverified.

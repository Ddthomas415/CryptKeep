# ED-002 comparison carry: bounded correction

2026-10-27. Active role ENGINEER. Risk HIGH. READY_FOR_INDEPENDENT_REVIEW.

## Finding And Decision

The operator approved the submitted synthetic comparison. On checking the pending
independent review, its decision was REJECTED for ED002-COMPARISON-01. Approval
was not treated as waiving a subsequently read, reproduced correctness blocker.
The accepted ledger, delay bridge, signal policies and original economic studies
remain unchanged. This correction is within the submitted wrapper's scope.

SHOWN: the resumed wrapper trusted `comparison_entry.status` alone. Copying the
cash control's empty-set ACCEPTED marker into failed BTC/mix benchmark states
could incorrectly make the comparison economically usable. This is inconsistent
caller carry metadata, not spontaneous failure of ordinary full/split execution.

## Minimal Correction

Before any arm runs, derive intended control components from the bound recipe,
recompute each arm's entry evidence from its actual carried trade list at the
original first-execution timestamp, and require the entire stored record to equal
that evidence with ACCEPTED status. A failed benchmark, missing proof, copied
cash proof, wrong clock or contradictory component lists is refused. Do not retry
the control, manufacture trades or change the original entry result.

Moved the existing control recipe before carry validation and added this
reconciliation only. No new state-signing framework, ledger replay, simulator,
financial assumption or scope expansion. Existing shared-ledger resume checks
still validate the financial state; this is a consistency check, not a claim
of tamper-proof storage or independently verified exchange fills.

## Proof And Preservation

Five new synthetic regressions failed before source correction:

- Copied empty cash proof on failed BTC/mix entries was not refused.
- Four contradictory expected/entered/clock/missing fields reached an arm runner
  before validation; the regression explicitly prevents any simulation then.

Before command, exit 1, 5 failed / 23 deselected in 0.59s:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_delayed_research_comparison.py -k 'copied_cash_entry_proof or reconciles_full_entry_record'
```

Final corrected source, VERIFIED_ENV, exit 0, **185 passed in 7.06s**:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_delayed_research_comparison.py tests/test_delayed_signal_bridge.py tests/test_frozen_signal_bridge.py tests/test_shared_cash_research.py tests/test_next_open_research.py tests/test_harness_contracts_wp4.py
```

This comprises 28 comparison cases and 157 existing cases; no full-suite or
market study. Ordinary full/split equality, fresh benchmark checks and all prior
timing/accounting tests remain passing. No new economic results or calibration.

Original rejected source/tests/checkpoint/bindings/review and review probe are
preserved in `../review_artifacts/ed002_comparison_rejected_v1_20261027.tar`,
SHA256 `341f40a2d0101988dc542b4234f040fc1634442b405c749894eec8a33832f535`.
The original review and binding files are not rewritten to suggest acceptance.
Generated before/after diff:
`../review_artifacts/ed002_comparison_carry_fix_20261027.diff`, SHA256
`2ddbf57f3cc05a00d9c3f5b011dec49f0f466f1a32413bbf668a78ed599b6e45`.
Current exact-source bindings accompany this correction note.

## Boundary

Separate re-review must close ED002-COMPARISON-01 on the corrected sources.
No same-thread financial acceptance. No market data/network, account/credential,
service/schedule, capital/risk, trading, commit or push operation. Caller-supplied
economic inputs, future protocol and run authorization remain separate. The
operator's approval is recorded, but no approval of unreviewed subsequent scope
or a market experiment is inferred.

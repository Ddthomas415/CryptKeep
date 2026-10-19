# Combined existing cooldown and protective-exit review

AUDITOR. Isolated accepted381bd4776 tree, existing rev87 patches0001,0002,
0006 source/tests only. Historical patch logs not replayed; originals untouched.

## SHOWN

All three supplied patches applied without conflicts.0002 includes accepted
SQL existence lookup;0006 covers queued/submitting/submitted/held with no
newest-row limit. Runner cooldown pass-through requires held positive quantity,
sell action, no duplicate emission, no open or unreadable strategy intent.
Entries remain blocked and transitions consumed under existing contract.

Targeted run with original venv Python, -m pytest -q -p no:cacheprovider:
test_kill_cooldown_sessions.py, test_kill_gate_protective_exit.py,
test_strategy_runtime_runner.py, test_cooldown_review_protective_probe.py.
89 passed in5.64 seconds. No full-suite/production proof.

## Correction to prior probe

Earlier standalone review probe supplied exit-stack action sell; correct adapter
contract is action exit. Withdraw that test as proof of the specific stop-loss
path. The unconditional gate defect was separately supported by source.
Corrected probe uses action exit, stop_loss reason and an explicitly readable
queue with no open intents; it passes in the combined tree. No corrected
before-patch run claimed. Raw earlier failure is retained as history, not proof.

## Remaining integration boundary

Canonical executor _executor_submit.py checks market quality and symbol lock
before side-specific handling. The symbol-lock branch sets pending and continues
for all intents, including sells. Loop-based runner cooldown and canonical
timestamp lock are independent. PR605 accounting does not write runner
kill_until keys; do not claim a migration conflict between those stores.
Combined runner tests therefore do not establish end-to-end protective exits.
Live executor-side bypass is not silently added in this review; hard safety,
position provenance and permitted reduction must remain explicit.

## Disposition

Combined runner behavior locally verified; overall treatment INCOMPLETE pending
independent combined review and downstream protective-order gate assessment.
Next bounded action: prove whether a position-reducing intent is held by the
canonical timestamp/market-quality gates, then scope entry-only policy enforcement
without disabling reconciliation, auth or order-validity checks.
No integration, deployment, state reset, config/account change or new strategy.

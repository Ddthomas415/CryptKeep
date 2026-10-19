# Live enable rollback review - 2026-10-05

Reviewer: Claude. Scope: `services/execution/live_enable.py`,
`services/admin/live_enable_wizard.py`. Result: patch 0069 (`1c2e7768`), bundle rev80
folder 77. READY_FOR_INDEPENDENT_REVIEW, LIVE-PATH (failure handling only). Not pushed.

## Checked first, no patch

The capped-live gate's expectancy check (filed earlier as "averages buy rows"): the
pass/fail is the sign of the average, which is the sign of total PnL, so zero-PnL buy rows
do not change the verdict. They halve the displayed average and let 5 round trips meet the
"10 fills" minimum. Nothing produces live orders, so the gate has never run for real.

## Findings (P2)

Probe: real config editor, arming state, system guard and journal; the journal accepts the
config-save event, then refuses every later write.

1. The rollback saved the previous config through the audited save, which needs the same
   journal. When that failed too it restored the bytes it found: the enabled config.
   Result on the previous code: reason `..._live_enable_rolled_back`, `rollback.save.ok`
   false, `execution.live_enabled: true` on disk. Live was disarmed, so no order could go
   out; `resume_if_safe` arms on an existing `live_enabled` and never writes it.
2. If writing the arming state raised, both paths raised with `live_enabled: true` saved.

## Patch 0069

- Snapshot the config bytes before the change; rollback tries the audited save, then
  restores the snapshot without needing the journal.
- Every rollback step runs even if an earlier one failed.
- `..._rolled_back` only when the config is back and live is disarmed (wizard: and the
  guard halted); otherwise `..._rollback_incomplete` with each step's result.
- A failed arming write returns `live_arm_failed_live_enable_*` instead of raising.

9 tests, 8 fail on the previous code. Full suite: 4859 passed, 33 skipped, 0 failed.

## Not fixed

- Dashboard Settings and strategy-config rollbacks use the same audited save (not live-path).
- A token consumed by a failed enable stays consumed.

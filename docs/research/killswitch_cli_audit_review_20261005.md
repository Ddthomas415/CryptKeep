# Operator action audit, kill-switch command: independent review (deferred live-money item 14)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW. Patch 0062 (`4a5d112b`), bundle rev73,
folder `70_killswitch_cli_records`. Not pushed, not applied to this checkout.

Scope: the slices of item 14 that bear on stopping and starting trading (the
live enable/resume audit fail-closed slice and the arm-to-halt replay).

## What holds

The enable, wizard-enable and resume paths append a required event and undo
what they changed when it cannot be written. The disable paths record best
effort and are not blocked. The replay passes only on an arm followed by a
halt.

## Finding (P2; shown by test with the real kill-switch file, journal and replay)

`scripts/killswitch.py` (`make kill-switch-on`, `make kill-switch-off`)
recorded nothing, although `docs/OPERATOR_ACTION_AUDIT_COVERAGE.md` lists
"kill-switch changes" among the actions that must be auditable.

- Releasing the switch lets orders through again; it was the one such action
  with no record and no fail-closed rule.
- An emergency stop made with this command left no halt in the journal, so
  the arm-to-halt replay could not be satisfied by it.

## Correction (`scripts/killswitch.py` only)

- Arm: switch set first, then a best-effort `live_halt` event. Never blocked
  by the journal.
- Disarm: required `kill_switch_disarm` event. Without it the switch is armed
  again and the command exits 2.
- Status records nothing.

## Facts, not changed

- In the enable and wizard paths the reason says "rolled_back" whether or not
  the rollback writes succeeded.
- `resume_gate` and the dashboard call the kill-switch module directly.
- The kill-switch state file is not written atomically; a torn file reads as
  armed.

## Verification

5 new tests, 4 fail on the previous code. The existing CLI tests now point
the journal at a temporary directory; without that, running the suite would
append events to the real state directory. Full suite with the tooling on
the right interpreter: 4801 passed, 33 skipped, 0 failed.

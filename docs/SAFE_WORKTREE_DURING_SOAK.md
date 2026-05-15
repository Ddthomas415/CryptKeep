# Safe Git Work During Active Soak

**Last updated:** 2026-05-13

This note defines the safest Git workflow while a supervised paper soak is
running from another checkout.

## Safe default rule

When a supervised paper soak is active:

- keep the active soak checkout read-only except for status/report commands
- do code edits, docs work, tests, and PR prep in a separate clone or worktree
- do not restart, stop, or reconfigure the running soak from the side worktree
  unless an explicit cutover decision has been made

## Safe in the side worktree

- source code edits
- docs and checklist work
- dashboard/UI work
- unit and integration tests that do not target the active soak runtime state
- PR slicing, commits, and branch publication

## Not safe by default

The following can disturb the current soak if they are pointed at the shared
runtime state:

- `scripts/start_bot.py`
- `scripts/stop_bot.py`
- `scripts/run_bot_runner.py`
- any command that writes into `.cbp_state/runtime/`
- any command that mutates the active paper/live SQLite stores

If runtime experimentation is needed from the side worktree, isolate it first
with a separate state path and treat that as a different environment.

## Recommended operator workflow

1. Use the active soak checkout only for read-only checks:
   - `python scripts/bot_status.py`
   - `python scripts/run_ai_alert_monitor.py --status`
   - `python scripts/report_supervised_soak_status.py`
2. Do repo work in a separate clone or worktree under `/private/tmp` or an
   equivalent side path.
3. Defer merge/cutover decisions until the soak window or an explicit review
   point.

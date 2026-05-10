# Safe Git Work During Active Soak

**Last updated:** 2026-05-10

This note defines the safest in-repo workflow for making Git-side progress
while a supervised paper soak is still running from another checkout.

## Current shown setup

- active soak checkout:
  - path: `/Users/baitus/Downloads/crypto-bot-pro`
  - branch: `codex/runtime-hardening-ai-alert-monitor`
- side audit worktree:
  - path: `/private/tmp/cryptkeep-audit`
  - branch: `codex/full-audit-pass-1`

The side worktree is a separate filesystem checkout of the same repository. It
shares Git object history, but it does not share the active working tree files
that the current soak is executing from.

## Safe default rule

When a supervised paper soak is active:

- keep the active soak checkout read-only except for status/report commands
- do code edits, docs work, tests, and PR prep in a separate Git worktree
- do not restart, stop, or reconfigure the running soak from the side worktree
  unless an explicit cutover decision has been made

## What is safe in the side worktree

- source code edits
- docs and checklist work
- dashboard/UI work
- unit and integration tests that do not target the active soak runtime state
- PR slicing, commits, and pushes

## What is not safe by default

The following can disturb the current soak if they are pointed at the shared
runtime state:

- `scripts/start_bot.py`
- `scripts/stop_bot.py`
- `scripts/run_bot_runner.py`
- any command that writes into `.cbp_state/runtime/`
- any command that mutates the active paper/live SQLite stores

If runtime experimentation is needed from the side worktree, isolate it first
with a separate state path and treat that as a different environment.

## Python environment note

The side worktree does not automatically inherit the primary checkout's local
untracked `.venv/` directory. Until a separate environment is created, use the
existing interpreter from the active checkout:

```bash
/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q
```

## Recommended operator workflow

1. Keep the active soak checkout open only for:
   - `python scripts/bot_status.py`
   - `python scripts/run_ai_alert_monitor.py --status`
   - `python scripts/report_supervised_soak_status.py`
2. Do repo work in `/private/tmp/cryptkeep-audit`.
3. Commit and push from the side worktree branch.
4. Defer merge/cutover decisions until the soak window or a deliberate review
   point.

## Generic setup command

If another side worktree is needed later:

```bash
git -C /Users/baitus/Downloads/crypto-bot-pro worktree add /private/tmp/cryptkeep-audit-2 -b codex/full-audit-pass-2
```

## Cleanup command

After the side branch is no longer needed:

```bash
git -C /Users/baitus/Downloads/crypto-bot-pro worktree remove /private/tmp/cryptkeep-audit
```

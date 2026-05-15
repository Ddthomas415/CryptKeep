# AI Copilot Monitoring Gap — 2026-05-15

## Status

Deferred follow-up. Do not treat as part of the current ES evidence-window runtime work.

## Problem

Operator expectation: the repo copilot should be able to monitor an active runtime task and surface meaningful changes without requiring repeated manual check-ins.

Current repo truth does not meet that expectation.

## SHOWN

- `services/ai_copilot/alert_monitor.py` is a continuous runtime incident monitor.
- `services/ai_copilot/oversight_watch.py` and `scripts/run_ai_oversight_watch.py` are read-only and one-shot, not persistent monitors.
- `docs/AI_COPILOT_BOUNDARY.md` and `docs/AI_COPILOT_OPERATING_RULES.md` define the copilot layer as advisory.
- There is no shown repo surface that:
  - watches a specific paper-evidence objective like `next fill` or `position closed`
  - persists a user/task-level watch definition
  - pushes a follow-up notification back into the operator conversation

## Current fallback

Use a local watcher loop for observation only:

```bash
cd /Users/baitus/Downloads/crypto-bot-pro
while true; do
  clear
  date
  echo "== status =="
  python3 scripts/bot_status.py || true
  echo
  echo "== health =="
  python3 scripts/check_system_health.py || true
  python3 scripts/check_risk_accounting_invariant.py || true
  echo
  echo "== recent runner evidence =="
  tail -n 80 .cbp_state/runtime/logs/pipeline.log 2>/dev/null || true
  sleep 300
done
```

This observes. It does not notify, schedule, or mutate.

## Desired outcome

One canonical copilot-side monitoring surface that can:

1. watch concrete runtime triggers
2. persist monitor definitions locally
3. emit operator-facing reports when triggers fire
4. remain read-only with respect to live trading control

## Suggested scope

Start with one narrow monitor family:

- paper evidence window monitors
- trigger examples:
  - new fill written
  - position opened
  - position closed
  - collector stopped unexpectedly
  - runner enters a repeated blocked state

## Acceptance criteria

- operator can register a local watch for a named runtime condition
- monitor evaluates canonical runtime state and evidence files on an interval
- trigger events write durable incident or watch reports under `.cbp_state/runtime/ai_reports/`
- CLI and dashboard expose current watch status and most recent trigger result
- no live control mutation, no config writes outside the explicit watch surface, no direct trading authority

## Non-goals

- no auto-arming
- no order submission
- no automatic branch merges
- no chat-thread wakeup assumption unless a separate automation surface exists

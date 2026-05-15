# AI Copilot Monitoring Gap — 2026-05-15

## Status

Substantially closed on `fix/p1-pre-live`.

## Problem

Operator expectation: the repo copilot should be able to monitor an active runtime task and surface meaningful changes without requiring repeated manual check-ins.

Current repo truth now partially meets that expectation, but not completely.

## SHOWN

- `services/ai_copilot/alert_monitor.py` is a continuous runtime incident monitor.
- `services/ai_copilot/oversight_watch.py` and `scripts/run_ai_oversight_watch.py` are read-only and one-shot, not persistent monitors.
- `docs/AI_COPILOT_BOUNDARY.md` and `docs/AI_COPILOT_OPERATING_RULES.md` define the copilot layer as advisory.
- `services/analytics/paper_sim_monitor.py` now provides a persistent local monitor for paper-sim/evidence windows.
- `scripts/run_paper_sim_monitor.py` now supports:
  - `--register-watch`
  - `--list-watches`
  - `--delete-watch`
  - `--status`
  - `--once`
- `services/analytics/paper_strategy_evidence_service.py` now auto-supervises `paper_sim_monitor` during managed paper evidence campaigns, so the monitor no longer needs a separately started loop for that workflow.
- Trigger events now write durable watch reports under `.cbp_state/runtime/ai_reports/`.
- The Operations dashboard now shows current paper-sim watch status and the most recent trigger result.
- There is still no shown repo surface that:
  - pushes a follow-up notification back into the operator conversation
  - wakes the operator asynchronously without a separately running local monitor process

## Current fallback

Managed paper evidence campaigns now start the local paper sim monitor automatically.

Run the paper sim monitor directly only when you want standalone monitoring outside the managed paper evidence workflow:

```bash
cd /Users/baitus/Downloads/crypto-bot-pro
./.venv/bin/python scripts/run_paper_sim_monitor.py --register-watch next_fill --watch-trigger new_fill
./.venv/bin/python scripts/run_paper_sim_monitor.py --interval-sec 300
```

Lower-level shell loops remain available for observation only:

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

The paper-sim monitor persists watch definitions and writes trigger reports, but it still does not wake the chat thread or push an external notification by itself.

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

Status against those criteria:
- `met`: local watch registration
- `met`: interval evaluation of canonical runtime/evidence state
- `met`: durable watch reports under `runtime/ai_reports`
- `met`: CLI and dashboard status surfaces
- `met`: managed paper evidence campaigns auto-start the local monitor
- `met`: read-only with respect to trading control
- `not met`: autonomous operator notification outside the local monitor runtime

## Non-goals

- no auto-arming
- no order submission
- no automatic branch merges
- no chat-thread wakeup assumption unless a separate automation surface exists

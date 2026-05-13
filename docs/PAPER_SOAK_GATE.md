# Paper Soak Gate Interpretation

**Last updated:** 2026-05-13

This document defines the current Section 4.1 policy for supervised paper-soak
evidence. It is a companion to [LAUNCH_CHECKLIST.md](./LAUNCH_CHECKLIST.md):
the checklist is the compact gate surface, while this note records the current
runtime interpretation and the operator decisions for the active soak model.

## Shown runtime truth

- Section 4 is the **Paper trading gate**.
- The current canonical supervised paper topology uses:
  - `pipeline`
  - `executor`
  - `ops_signal_adapter`
  - `ops_risk_gate`
  - `ai_alert_monitor`
- In paper mode:
  - `intent_consumer` is not expected to run
  - `reconciler` is not expected to run when `with_reconcile=false`
- The paper-soak state is evaluated from the running supervised runtime:
  - `runtime/flags/bot_runner.status.json`
  - `runtime/flags/pipeline.status.json`
  - `runtime/flags/intent_executor.status.json`
  - `runtime/health/ai_alert_monitor.json`

## Section 4.1 counts when

- the supervised runtime is in paper mode
- the running services match the expected paper topology
- the running soak symbol set is internally aligned across:
  - `bot_runner.status.json`
  - `pipeline.status.json`
  - `intent_executor.status.json`
- the soak continues to advance:
  - `pipeline.loops` increases over time
  - `intent_executor.loops` increases over time

Section 4.1 is therefore not blocked merely because:

- `intent_consumer=false`
- `reconciler=false`

Those are expected in the current paper supervised path.

## Recorded operator policy

**Date recorded:** 2026-05-13

### Recovered external API/network warnings

**Policy:** recovered external Coinbase API/network warnings annotate the soak
window and do **not** reset the Section 4.1 clock.

**Applies when all are true:**
- the event is an external network/API failure such as `RequestTimeout` or
  `NetworkError`
- the next supervised cycle recovers normally
- the paper topology remains intact
- loops continue advancing
- the event is warning quality, not a service-collapse incident

**Clock-reset triggers instead:**
- topology break
- managed-service restart/churn in the paper path
- loops stop advancing
- operator intervention is required to recover
- a critical incident shows real service unavailability or corrupted runtime truth

### Scanner symbol drift

**Policy:** scanner-selected symbol drift annotates the soak window and does
**not** reset the Section 4.1 clock, as long as the running soak symbol set
remains internally aligned and the supervised runtime continues advancing.

**Interpretation:** the running soak symbol set is the evidence anchor for the
current Section 4.1 window. Current scanner output is an operator observation,
not an automatic clock-reset condition.

If the operator deliberately changes the live-intended symbol set and restarts
the supervised paper stack onto a different symbol window, that decision point
starts a new soak window.

## Recommended evidence surface

Use:

```bash
python scripts/report_supervised_soak_status.py
```

That read-only surface summarizes:

- elapsed Section 4.1 time
- paper topology
- running-vs-current symbol state
- loop progression
- pipeline error count
- AI monitor incident summary

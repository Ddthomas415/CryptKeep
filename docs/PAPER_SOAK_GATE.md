# Paper Soak Gate Interpretation

**Last updated:** 2026-05-10

This document defines what current repo/runtime truth already supports for
Section 4.1 of the launch checklist, and it records the remaining operator
policy decisions that are still required before Section 4 can be signed off.

It exists as a companion to [LAUNCH_CHECKLIST.md](./LAUNCH_CHECKLIST.md)
because that checklist file is a compact gate surface, while the current repo
needs a more explicit interpretation note for supervised paper-soak evidence.

## Shown repo truth

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
- The paper-soak status should be evaluated from the **running soak state**:
  - `runtime/flags/bot_runner.status.json`
  - `runtime/flags/pipeline.status.json`
  - `runtime/flags/intent_executor.status.json`
  - `runtime/health/ai_alert_monitor.json`
- The current scanner-selected symbol set may drift away from the running soak
  symbol set. That drift does not, by itself, prove the soak is invalid.

## Current interpretation for Section 4.1

Section 4.1 counts when all of the following are true:

- the supervised runtime is in paper mode
- the running services match the expected paper topology
- the running soak symbol set is internally aligned across:
  - `bot_runner.status.json`
  - `pipeline.status.json`
  - `intent_executor.status.json`
- the soak continues to advance:
  - `pipeline.loops` increases over time
  - `intent_executor.loops` increases over time

Section 4.1 is therefore **not blocked** merely because:

- `intent_consumer=false`
- `reconciler=false`

Those are expected in the current paper supervised path.

## Current non-proof

The following claims are **not** currently supported by visible repo truth:

- that the Section 4.1 clock resets on any recovered transient exchange/API
  timeout
- that the Section 4.1 clock continues unchanged after any recovered transient
  exchange/API timeout
- that scanner-selected symbol changes must automatically replace the running
  soak symbol set during the same 7-day window
- that the running soak symbol set must remain frozen for the full 7-day window

Those are policy decisions, not settled repo facts.

## Open operator decisions

Before Section 4 can be signed off cleanly, the operator should explicitly
choose:

1. **Symbol-window policy**
   Does Section 4.1 freeze the running symbol set for the entire soak window,
   or allow scanner-driven symbol rotation during the same window?

2. **Recovered-timeout policy**
   Do recovered transient pipeline market-data/API errors count as acceptable
   warnings within continuous operation, or do they require the Section 4.1
   clock to restart?

## Safe default until policy is chosen

Until those decisions are written into the checklist itself:

- continue the paper supervised soak unchanged
- do Git-side repo work from a separate checkout, as documented in
  [SAFE_WORKTREE_DURING_SOAK.md](./SAFE_WORKTREE_DURING_SOAK.md)
- use `python scripts/report_supervised_soak_status.py` as the operator-facing
  evidence surface
- record the current running soak state, not only the current desired scanner
  state
- do not mark Section 4.1 as `PASS` solely because elapsed time reaches 7 days
- require explicit human review of:
  - the final runtime topology
  - symbol drift during the window
  - pipeline error history
  - AI incident history

## Recommended evidence command

```bash
python scripts/report_supervised_soak_status.py
```

That script is read-only and is the current lowest-risk way to capture:

- elapsed Section 4.1 time
- running paper topology
- symbol alignment
- loop progression
- pipeline error count
- AI monitor incident summary

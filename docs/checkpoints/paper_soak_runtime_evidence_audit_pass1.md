# Paper Soak and Runtime Evidence Audit — Pass 1

**Date:** 2026-05-10  
**Section:** 2. Paper Soak and Runtime Evidence  
**Status:** IN PROGRESS

This pass covers what current repo and runtime evidence actually support for the
paper-soak gate, without changing the running soak or defining new gate policy.

## Scope

- Section 4.1 gate wording
- supervised paper-soak interpretation note
- read-only soak reporter behavior
- current runtime evidence from the active soak
- AI incident/report surfaces used as soak evidence

## Evidence reviewed

- `docs/LAUNCH_CHECKLIST.md`
- `docs/PAPER_SOAK_GATE.md`
- `scripts/report_supervised_soak_status.py`
- `scripts/run_pipeline_loop.py`
- `scripts/run_intent_executor.py`
- `tests/test_report_supervised_soak_status.py`
- live read-only status from:
  - `python scripts/bot_status.py`
  - `python scripts/report_supervised_soak_status.py --json`
  - `python scripts/run_ai_alert_monitor.py --status`
  - `.cbp_state/runtime/logs/pipeline.log`
  - `.cbp_state/runtime/ai_reports/*.json`

## Checklist status

- [x] Verified that the active supervised runtime is in expected paper topology.
- [x] Verified that the soak reporter is the current canonical read-only evidence surface.
- [x] Verified that current runtime symbols are internally aligned across run-state surfaces.
- [~] Verified that current desired scanner symbols can drift from the running soak state.
- [~] Verified that timeout / warning handling remains policy-dependent rather than checklist-defined.
- [~] Verified that AI incident count is available, but not yet calibrated as a unique-failure count.

## SHOWN findings

### 1. Section 4.1 gate wording is underspecified relative to current supervised paper-soak truth

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `docs/LAUNCH_CHECKLIST.md` defines Section 4.1 only as
  `≥ 7 days of continuous operation`.
- `docs/PAPER_SOAK_GATE.md` explicitly states that current repo truth does not
  decide:
  - whether recovered API timeouts reset the clock
  - whether the clock continues unchanged after recovered API timeouts
  - whether scanner-selected symbol changes must replace the running soak set
  - whether the running symbol set must remain frozen for the full 7-day window

Impact:

- the launch checklist alone is not sufficient to determine Section 4.1 pass
  semantics for the current supervised paper runtime.
- final sign-off still depends on explicit operator policy, not just elapsed
  time.

### 2. The read-only soak reporter can mark `counts_for_paper_gate=true` while important soak-quality questions remain unresolved

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- `scripts/report_supervised_soak_status.py` sets `counts_for_paper_gate` from:
  - paper mode
  - not live-enabled
  - topology matches run state
  - runtime symbols match run state
- it does not include:
  - `pipeline.errors`
  - `ai_alert_monitor.incidents_written`
  - symbol drift versus current desired scanner state
- `tests/test_report_supervised_soak_status.py` explicitly asserts
  `counts_for_paper_gate is True` even when current desired symbols differ from
  the running soak symbols.
- current live report shows:
  - `counts_for_paper_gate: true`
  - `runtime_matches_current_desired_state: false`
  - `pipeline.errors: 3`
  - `ai_alert_monitor.incidents_written: 9`

Impact:

- `counts_for_paper_gate` currently means “this is the correct paper-soak lane”
  rather than “Section 4.1 is clean or pass-ready.”
- operators could over-read that field unless they also inspect the rest of the
  report.

### 3. Current AI incident totals overstate unique paper-soak failure events

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- current AI monitor status reports `incidents_written: 9`.
- current pipeline status reports `errors: 3`.
- current `pipeline.log` contains 3 `run_once_failed` lines.
- the latest two AI reports represent the same failure family:
  - one report captures a traceback/error burst for Coinbase network failure
  - the next report captures the summarized `run_once_failed` line for that
    same failure episode

Impact:

- raw AI incident count is not a clean proxy for unique soak failures.
- incident history is decision-useful only when paired with log-family review,
  not as a simple total.

## SHOWN current runtime state

- active paper topology is correct:
  - `pipeline=True`
  - `executor=True`
  - `ops_signal_adapter=True`
  - `ops_risk_gate=True`
  - `ai_alert_monitor=True`
  - `intent_consumer=False`
  - `reconciler=False`
- current soak report:
  - `result: IN PROGRESS`
  - `elapsed_hours: 70.14`
  - `remaining_hours: 97.86`
  - `run_state.symbols: ["B3/USD", "B3/USDC"]`
  - `current_desired_state.symbols: ["BILL/USD", "BILL/USDC"]`
  - `symbols.runtime_matches_run_state: true`
  - `symbols.runtime_matches_current_desired_state: false`
  - `pipeline.errors: 3`
  - `pipeline.last_ok: true`
  - `ai_alert_monitor.last_severity: warn`
  - `ai_alert_monitor.reason: no_new_events`

## UNVERIFIED points

- whether the 3 recovered pipeline errors should reset, pause, or merely annotate
  the 7-day clock
- whether scanner-driven symbol drift during the same soak window is acceptable
  for final paper-gate sign-off
- whether all 9 incident reports collapse into exactly 3 unique failure episodes
  across the full monitored run

## Highest-leverage next evidence action

Keep the soak unchanged and gather a classification ledger for the existing
incident/report set:

1. unique failure family
2. first occurrence time
3. repeated duplicate report count
4. whether the event affected topology, only warning quality, or neither

That evidence is more decision-useful than adding more runtime changes before
Section 4 policy is settled.

## Handoff

- Active role: `AUDITOR`
- Acceptance state: `INCOMPLETE`
- Improvement from this pass:
  - clarified what the current paper-soak gate does and does not prove
  - separated run-state validity from gate-pass semantics
  - showed that incident totals are noisy evidence rather than a unique-failure counter
- Proof required next:
  - incident-family classification for the current soak
  - explicit operator decision on symbol-window policy
  - explicit operator decision on recovered-timeout policy

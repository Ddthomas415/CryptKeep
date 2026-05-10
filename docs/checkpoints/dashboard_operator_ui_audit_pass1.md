# Dashboard and Operator UI Audit — Pass 1

**Date:** 2026-05-10  
**Section:** 6. Dashboard and Operator UI  
**Status:** IN PROGRESS

This pass audits the operator-facing dashboard surfaces against the current
runtime-truth and paper-soak evidence surfaces. It does not change the UI.

## Scope

- Operations page runtime-truth surfaces
- operator service-control wrappers
- copilot incident/report presentation
- existing dashboard test coverage for these surfaces

## Evidence reviewed

- `dashboard/pages/60_Operations.py`
- `dashboard/services/operator.py`
- `dashboard/services/copilot_reports.py`
- `dashboard/services/view_data.py`
- `docs/CURRENT_RUNTIME_TRUTH.md`
- `scripts/report_supervised_soak_status.py`
- `tests/test_dashboard_pages_compile.py`
- `tests/test_dashboard_page_runtime.py`
- `tests/test_dashboard_copilot_reports_page.py`
- `tests/test_dashboard_operator_service.py`
- `tests/test_operations_page_role_passthrough.py`
- `tests/test_operations_page_redacts_store_path.py`
- current read-only soak evidence from:
  - `python scripts/report_supervised_soak_status.py --json`
  - `python scripts/run_ai_alert_monitor.py --status`

## Checklist status

- [x] Verified that the Operations page compiles and the current dashboard test slice passes.
- [~] Verified that Operations shows generic service health and AI monitor state.
- [ ] Verified that Operations surfaces the canonical Section 4.1 paper-soak evidence.
- [ ] Verified that Operations service controls align with the canonical managed runtime service set.
- [~] Verified that copilot report presentation exists, but incident counts are not normalized to unique failure families.
- [ ] Manual browser/UI smoke was not performed in this pass.

## SHOWN findings

### 1. Operations does not surface the canonical supervised paper-soak evidence view

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `docs/CURRENT_RUNTIME_TRUTH.md` states that the current read-only evidence
  surface for the paper gate is `python scripts/report_supervised_soak_status.py`.
- `dashboard/pages/60_Operations.py` loads:
  - `get_operations_snapshot()`
  - AI monitor runtime status
  - crypto-edge runtime summaries
  - paper strategy evidence runtime
- no visible Operations-page code imports or calls
  `report_supervised_soak_status.py`, and repo search shows no dashboard usage of:
  - `report_supervised_soak_status`
  - `counts_for_paper_gate`
  - `runtime_matches_current_desired_state`

Impact:

- the main operator page does not expose the canonical Section 4.1 evidence
  that currently determines:
  - elapsed paper-soak time
  - counts-for-paper-gate truth
  - running-vs-current desired symbol drift
  - current Section 4.1 wording block

### 2. Operations service controls are still scoped to a stale service model

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `dashboard/services/operator.py` defines:
  - `DEFAULT_SERVICES = ("tick_publisher", "reconciler", "intent_consumer")`
  - `ALLOWED_OP_ARGS` only for `tick_publisher`, `reconciler`, and
    `intent_consumer`
- `docs/CURRENT_RUNTIME_TRUTH.md` defines the canonical managed service set as:
  - `market_ws`
  - `pipeline`
  - `executor`
  - `intent_consumer`
  - `ops_signal_adapter`
  - `ops_risk_gate`
  - `reconciler`
  - `ai_alert_monitor`
- `tests/test_dashboard_operator_service.py` and
  `tests/test_dashboard_page_runtime.py` still exercise `tick_publisher`-shaped
  service listings and controls as the normal Operations service-control model.

Impact:

- the operator-service wrapper layer remains centered on a legacy or partial
  runtime shape rather than the current canonical supervised runtime.
- even if the broader repo runtime truth is correct, the Operations page’s
  direct service-control lane is not aligned with that truth.

### 3. Operations shows raw AI incident totals without the current unique-failure context

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- `dashboard/pages/60_Operations.py` renders:
  - `AI Monitor`
  - `Incidents = incidents_written`
  - `Last Report = last_report_stem`
- current live AI monitor status reports:
  - `incidents_written = 9`
- the incident ledger in
  `docs/checkpoints/paper_soak_incident_ledger_pass1.md` shows that the current
  supervised soak window has:
  - `3` unique pipeline failure episodes
  - each represented by `2` persisted reports
  - plus `3` pre-window historical reports on disk

Impact:

- the Operations page’s raw incident total is not a decision-useful proxy for
  current-soak unique failure count.
- operators can see that incidents exist, but not whether the current window is
  accumulating new failure families versus duplicate monitor output.

### 4. Current dashboard tests do not cover the canonical paper-soak evidence integration path

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- dashboard page tests pass:
  - `34 passed in 0.81s`
- current test coverage for Operations focuses on:
  - role passthrough
  - action wiring
  - warning rendering
  - tick-publisher-shaped service lists
- no visible Operations-page test imports or asserts:
  - `report_supervised_soak_status.py`
  - `counts_for_paper_gate`
  - `elapsed_hours`
  - `remaining_hours`
  - `runtime_matches_current_desired_state`

Impact:

- the current dashboard test slice is useful for structural safety, but it does
  not protect the operator-facing paper-soak truth surface.

## SHOWN strengths

- Operations enforces authenticated operator role at entry.
- role passthrough coverage exists for Operations actions.
- store-path redaction coverage exists for the research surface.
- dashboard compile/runtime smoke coverage exists and currently passes.

## UNVERIFIED points

- whether the rendered UI visually misleads operators in browser usage, beyond
  what the source and tests show
- whether any non-Operations page currently surfaces the supervised soak report
  in a usable operator form
- whether the `op.py list` output in a live dashboard session still returns the
  legacy `tick_publisher` shape or a newer service set

## Highest-leverage next evidence action

Audit the actual runtime-facing dashboard digest surfaces next:

1. Overview / digest runtime truth cards
2. whether any page already exposes soak-gate evidence outside Operations
3. whether the dashboard presents runtime truth consistently across pages

That will show whether the Section 4.1 truth is absent everywhere or merely
missing from the Operations page.

## Handoff

- Active role: `AUDITOR`
- Acceptance state: `INCOMPLETE`
- Improvement from this pass:
  - established that the dashboard has operator safety scaffolding and tests
  - established that the main Operations page is not yet the canonical paper-soak evidence view
  - established that direct service controls are still modeled around a stale service subset
- Proof required next:
  - digest/runtime-card audit
  - browser/UI smoke if visual/operator clarity needs confirmation
  - determination of whether supervised soak evidence is absent globally or only absent from Operations

# Runtime + Dashboard Audit TODO

**Last updated:** 2026-05-10

This checklist is the recommended starting point for a thorough runtime and UI
dashboard audit without disturbing the active local paper soak.

## Current baseline

**SHOWN**

- Current supervised runtime is the paper soak path:
  - `pipeline`
  - `executor`
  - `ops_signal_adapter`
  - `ops_risk_gate`
  - `ai_alert_monitor`
- `intent_consumer` and `reconciler` are intentionally absent in paper mode.
- Section 4.1 is still `IN PROGRESS`.
- The read-only soak evidence command is:

```bash
python scripts/report_supervised_soak_status.py
```

- Current dashboard verification slice passed:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_dashboard_pages_compile.py \
  tests/test_dashboard_operator_role_guard.py \
  tests/test_dashboard_copilot_reports_page.py \
  tests/test_dashboard_page_runtime.py
```

Result at last check: `24 passed`.

## Recommended start order

1. Runtime truth and soak visibility in the dashboard
2. Dashboard fallback/data-coherence audit
3. Operator controls and role-guard audit
4. Manual browser smoke for the highest-risk pages
5. Docs/checklist alignment after UI truth is confirmed

## Phase 1 — Runtime Truth in UI

- [ ] Add a read-only supervised soak panel to the Operations page using `scripts/report_supervised_soak_status.py` or shared service logic derived from it.
- [ ] Show the current Section 4.1 state directly in the dashboard:
  - result
  - elapsed hours
  - remaining hours
  - counts-for-paper-gate flag
- [ ] Surface the difference between:
  - running soak symbol set
  - current desired scanner-selected symbol set
- [ ] Surface pipeline error count trend and AI incident count trend together so operators can tell:
  - stable/noisy but recovering
  - degraded
- [ ] Decide whether Operations page should explicitly label:
  - `paper supervised soak`
  - `not a full live-path rehearsal`

Why start here:

- Current repo truth already distinguishes running soak state from current
  scanner-selected desired state.
- The CLI reporter shows that drift clearly.
- The dashboard does not yet make that operator distinction obvious.

## Phase 2 — Fallback and Data-Coherence Audit

- [ ] Audit Home page data sources and fallbacks:
  - `dashboard/app.py`
  - `dashboard/services/view_data.py`
  - `docs/dashboard/home_digest_sources.md`
- [ ] Verify that fallback/sample messaging is explicit anywhere mock/static data can appear.
- [ ] Check whether watchlist, signal, and detail panels can silently show stale or static data without a visible banner.
- [ ] Confirm structural-edge panels clearly distinguish:
  - live-public snapshot data
  - fallback/static summary data
- [ ] Review the dashboard pages that depend on market research helpers:
  - Markets
  - Signals
  - Research
  - Symbol Scanner
  - Copilot Reports

## Phase 3 — Operator and Safety Audit

- [ ] Review Operations page for separation between:
  - read-only intelligence
  - state-changing controls
- [ ] Confirm operator actions remain role-guarded and allowlisted.
- [ ] Verify there is no path from the AI copilot sections to arming live trading or mutating runtime state.
- [ ] Confirm service-control buttons and repair flows remain explicit about scope and side effects.
- [ ] Check whether the Operations page should show the current paper-soak interpretation note from `docs/PAPER_SOAK_GATE.md`.

## Phase 4 — Manual UI Smoke

Run only after the repo-side test baseline is green.

- [ ] Open the dashboard locally and verify page load for:
  - Overview
  - Operations
  - Copilot Reports
  - Markets
  - Signals
  - Settings
- [ ] Confirm there are no obvious layout regressions on desktop.
- [ ] Confirm the Operations page can be understood without reading raw JSON.
- [ ] Confirm the Copilot Reports page distinguishes:
  - report kind
  - severity
  - generated time
  - read-only nature
- [ ] Confirm the current soak status can be read quickly by a human operator.

## Phase 5 — Checklist and Docs Alignment

- [ ] After UI/runtime truth is confirmed, update the launch checklist safely once the swap-file situation is resolved.
- [ ] Decide and document:
  - symbol-window policy during Section 4.1
  - recovered-timeout policy during Section 4.1
- [ ] Align:
  - `docs/LAUNCH_CHECKLIST.md`
  - `docs/PAPER_SOAK_GATE.md`
  - `docs/CURRENT_RUNTIME_TRUTH.md`

## Suggested commands

Runtime truth:

```bash
python scripts/report_supervised_soak_status.py
python scripts/bot_status.py
python scripts/run_ai_alert_monitor.py --status
```

Dashboard baseline:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_dashboard_pages_compile.py \
  tests/test_dashboard_operator_role_guard.py \
  tests/test_dashboard_copilot_reports_page.py \
  tests/test_dashboard_page_runtime.py
```

Broader dashboard slice:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_dashboard_pages_compile.py \
  tests/test_dashboard_page_runtime.py \
  tests/test_dashboard_view_data.py \
  tests/test_dashboard_operator_service.py \
  tests/test_dashboard_copilot_reports.py \
  tests/test_dashboard_copilot_reports_page.py
```

## Best next move

If the goal is highest leverage with zero soak disturbance, start with:

- [ ] Add the supervised soak panel to `dashboard/pages/60_Operations.py`
- [ ] Add a focused UI/service test for the new soak summary surface

That gives operators one authoritative place to read:

- current paper-soak status
- symbol drift
- error/incident posture
- Section 4.1 progress

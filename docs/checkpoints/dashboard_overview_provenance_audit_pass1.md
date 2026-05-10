# Dashboard Overview Provenance Audit — Pass 1

**Date:** 2026-05-10  
**Section:** 6. Dashboard and Operator UI  
**Status:** IN PROGRESS

This pass audits how the Overview page builds and labels its top-level runtime
summary. It stays in evidence mode only and does not change the UI or the
running soak.

## Scope

- `dashboard/services/view_data.py` facade path
- `dashboard/services/views/summary_view.py`
- `dashboard/services/views/_shared_ops.py`
- Overview status/provenance rendering
- existing `view_data` and Overview page test coverage

## Evidence reviewed

- `dashboard/services/view_data.py`
- `dashboard/services/views/summary_view.py`
- `dashboard/services/views/_shared_ops.py`
- `dashboard/services/views/_shared_shared.py`
- `dashboard/app.py`
- `dashboard/components/summary_panels.py`
- `tests/test_dashboard_view_data.py`
- `tests/test_dashboard_page_runtime.py`

## Checklist status

- [x] Verified where `get_dashboard_summary()` gets its initial payload.
- [x] Verified how local runtime/config overlays rewrite that payload.
- [x] Verified how Overview labels summary provenance today.
- [x] Verified that `get_overview_view()` forwards a mixed-source page model.
- [x] Verified that the current `view_data` / Overview page test slice passes.

## SHOWN findings

### 1. Overview summary truth is a composed payload, not a single-source runtime snapshot

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `dashboard/services/views/summary_view.py:19-43` builds `get_dashboard_summary()`
  from one of three starting payloads:
  - API: `/api/v1/dashboard/summary`
  - mock bundle: `dashboard.json`
  - static fallback: `_default_dashboard_summary()`
- before provenance is attached, each payload is passed through
  `_apply_local_summary_overrides(...)`.
- `dashboard/services/views/_shared_shared.py:21-35` attaches provenance only as:
  - `source`
  - `fallback`
  - `message`

Impact:

- the final Overview summary is a composed object assembled from multiple
  potential sources, not a raw one-source runtime snapshot.
- the top-level provenance badge is accurate at a coarse level, but it does not
  describe field-by-field origin after overlays are applied.

### 2. Local overlays can materially rewrite runtime mode, risk, watchlist, and connectivity truth

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `dashboard/services/views/_shared_ops.py:175-311`
  `_apply_local_summary_overrides(...)` can rewrite:
  - portfolio from `_load_local_portfolio_snapshot`
  - watchlist prices/source/exchange from `_get_market_snapshot`
  - mode / `execution_enabled` / `approval_required` from local config
  - `kill_switch` from local runtime state
  - `connections` from `_load_local_connections_summary`
  - `risk_status`, `active_warnings`, `blocked_trades_count`, exposure, leverage
    from `_load_local_risk_overlay`
  - `system_guard_state` and warning set from `_load_local_system_guard_state`
- `dashboard/services/views/_shared_ops.py:41-57` defines a static fallback
  summary with hard-coded portfolio and watchlist rows.
- `tests/test_dashboard_view_data.py:24-98` explicitly proves that an API payload
  can be rewritten to:
  - `mode == "live_auto"`
  - `execution_enabled is True`
  - `kill_switch is True`
  - `system_guard_state == "halting"`
  - `risk_status == "caution"`
- `tests/test_dashboard_view_data.py:334-385` proves local connection overlays
  replace the API `connections` block.

Impact:

- Overview status cards can reflect a hybrid of API payload and local runtime
  overlays even when the provenance line says `api_with_local_overlays`.
- this is not inherently wrong, but the surface is an operator composition layer,
  not a pure API mirror.

### 3. Overview shows only one top-level provenance message even though the page model mixes multiple source families

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- `dashboard/services/views/summary_view.py:47-78` returns the Overview page
  model as:
  - `summary`
  - `recent_activity`
  - `watchlist_preview`
  - `signals`
  - `selected_asset`
  - `detail`
- `dashboard/app.py:49-89` renders:
  - `summary` through `render_overview_status_summary(...)`
  - Home Digest through `load_home_digest(summary)`
  - structural-edge summaries from separate services
  - signal/detail content from `get_signals_view(...)`
- `dashboard/components/summary_panels.py:217-247` builds the Overview truth
  message only from `summary["data_provenance"]`.

Impact:

- the Overview page combines several different source families but exposes only
  one provenance message for the summary block.
- operators do not get comparable provenance labeling for signals, recent
  activity, or the digest sections that share the same page.

### 4. Current tests protect fallback labeling and overlay behavior, but not multi-surface provenance clarity

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- `tests/test_dashboard_view_data.py:6-21` proves fallback/sample provenance is
  explicitly attached as:
  - `source: "dashboard_fallback"`
  - `fallback: True`
- `tests/test_dashboard_page_runtime.py:175-329` proves the Overview page passes
  the `summary` object into the page and calls `load_home_digest(summary)`.
- `VERIFIED_ENV`:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_dashboard_view_data.py tests/test_dashboard_page_runtime.py`
  - result: `68 passed in 0.41s`
- no visible page/runtime test asserts that operators can distinguish:
  - summary provenance
  - signal provenance
  - digest provenance
  - structural-edge provenance
  on the same Overview screen

Impact:

- the current tests are good at proving the summary composition mechanics.
- they do not prove that the UI communicates those mixed origins clearly enough
  for operator judgment.

## SHOWN strengths

- fallback/sample data is explicitly labeled in the summary payload.
- local runtime overlays are intentional and tested, not hidden accidental drift.
- Overview page runtime tests already prove that the page consumes the shared
  summary object and digest entrypoints without crashing.

## UNVERIFIED points

- whether operators interpret `api_with_local_overlays` as a safe shorthand or
  as stronger proof than the page actually provides
- whether Markets, Signals, and Trades pages expose clearer per-surface
  provenance than Overview does
- whether any browser-level wording or layout mitigates this mixed-source model
  better than the source code alone suggests

## Highest-leverage next evidence action

Audit the remaining read-oriented dashboard pages for provenance carry-through:

1. Markets page data-source labeling
2. Signals page / recommendations provenance
3. Copilot Reports provenance and trust framing

## Handoff

- Active role: `AUDITOR`
- Acceptance state: `INCOMPLETE`
- Improvement from this pass:
  - established that Overview summary truth is intentionally composed from API,
    mock, fallback, and local runtime overlays
  - established that the current provenance label is coarse, not field-granular
  - separated summary provenance from the broader mixed-source page model
- Proof required next:
  - page-level provenance audit outside Overview
  - determination of whether operator-visible wording is sufficient in practice

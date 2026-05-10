# Dashboard Markets, Signals, and Copilot Provenance Audit — Pass 1

**Date:** 2026-05-10  
**Section:** 6. Dashboard and Operator UI  
**Status:** IN PROGRESS

This pass audits provenance and trust framing on the remaining read-oriented
dashboard pages most likely to influence operator judgment outside Home and
Overview. It does not modify the UI or the running soak.

## Scope

- `dashboard/pages/10_Markets.py`
- `dashboard/pages/30_Signals.py`
- `dashboard/pages/65_Copilot_Reports.py`
- `dashboard/services/views/market_view.py`
- `dashboard/services/views/signals_view.py`
- `dashboard/services/views/_shared_signals.py`
- `dashboard/services/copilot_reports.py`
- `dashboard/components/asset_detail.py`
- related tests

## Evidence reviewed

- `dashboard/pages/10_Markets.py`
- `dashboard/pages/30_Signals.py`
- `dashboard/pages/65_Copilot_Reports.py`
- `dashboard/services/views/market_view.py`
- `dashboard/services/views/signals_view.py`
- `dashboard/services/views/_shared_signals.py`
- `dashboard/services/copilot_reports.py`
- `dashboard/components/asset_detail.py`
- `tests/test_dashboard_asset_detail.py`
- `tests/test_dashboard_copilot_reports.py`
- `tests/test_dashboard_copilot_reports_page.py`
- `tests/test_dashboard_page_runtime.py`
- `tests/test_dashboard_view_data.py`

## Checklist status

- [x] Verified whether Markets surfaces quote and reasoning provenance.
- [x] Verified whether Signals surfaces recommendation-source provenance.
- [x] Verified Copilot Reports trust framing and artifact classification path.
- [x] Verified the current Markets/Signals/Copilot page test slice passes.
- [ ] Manual browser/UI smoke was not performed in this pass.

## SHOWN findings

### 1. Markets detail surfaces selected-asset provenance, but the broader watchlist view strips source context

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- `dashboard/services/views/market_view.py:89-98` reads selected-asset quote
  provenance into:
  - `exchange`
  - `snapshot_timestamp`
  - `snapshot_source`
- `dashboard/services/views/market_view.py:251-326` normalizes explain output
  into `assistant_status` with explicit provider/fallback metadata.
- `dashboard/components/asset_detail.py:60-85` renders a `Source` metric from:
  - `snapshot_source`
  - `exchange`
  - `snapshot_timestamp`
- `dashboard/components/asset_detail.py:31-57` and `137-176` render reasoning
  provider and fallback message from `assistant_status`.
- `tests/test_dashboard_asset_detail.py:41-66` proves the asset-detail source
  row is shown from snapshot metadata.
- `tests/test_dashboard_view_data.py:1288-1355` proves `get_markets_view()`
  preserves `detail["snapshot_source"]` for both `api` and `local_ws`.
- but `dashboard/pages/10_Markets.py:109-126` builds the watchlist table with:
  - `asset`
  - `price`
  - `change_24h_pct`
  - `signal`
  - `confidence`
  - `regime`
  - `category`
  - `opportunity_score`
  and does not include `snapshot_source`, `exchange`, or reasoning-provider data.

Impact:

- the selected asset has meaningful operator-visible provenance.
- the broader watchlist grid does not show where each row’s market state came
  from, so source visibility drops as soon as the operator leaves the focused
  detail view.

### 2. Signals page loses recommendation-origin provenance before the queue reaches the UI

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `dashboard/services/views/_shared_signals.py:274-348`
  `_load_local_recommendations()` starts with explicit local-source metadata:
  - signal inbox rows carry `source` / `author`
  - evidence-store rows carry `source_id`
- but those rows are normalized to:
  - `summary`
  - `evidence`
  - `status`
  with no dedicated `source` field preserved.
- `tests/test_dashboard_view_data.py:516-591` proves this collapse directly:
  - inbox `source="tradingview"` becomes `evidence="tradingview"`
  - evidence-store `source_id="partner_feed"` becomes
    `evidence="partner_feed"`
- `dashboard/services/views/signals_view.py:19-45` maps API recommendations to:
  - `asset`
  - `signal`
  - `confidence`
  - `summary`
  - `evidence`
  - `status`
  and also drops any dedicated origin/provenance field.
- `dashboard/pages/30_Signals.py:95-111` renders the Signal Queue without any
  recommendation-source column.

Impact:

- Signals can show current execution state and market-derived detail, but they do
  not expose whether the underlying recommendation came from:
  - local inbox
  - local evidence store
  - API recommendation feed
  - fallback/default recommendation set
- recommendation provenance exists at lower layers, but it is collapsed before
  operators see it.

### 3. Signals inherits selected-asset snapshot and reasoning provenance from Markets, but not recommendation-source truth

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- `dashboard/services/views/signals_view.py:133-154` resolves selected signal
  detail from `get_markets_view(selected_asset=resolved_asset)` and then merges
  score/regime fields from the signal row.
- `dashboard/pages/30_Signals.py:118-134` renders `render_asset_detail_card`
  against that `detail` payload.
- `dashboard/components/asset_detail.py:137-176` and `193-236` therefore show:
  - quote `Source`
  - reasoning provider
  - fallback message
  for the selected signal detail.
- `tests/test_dashboard_page_runtime.py:645-709` proves the Signals page pulls
  its detail contract from `get_signals_view()` and that detail can include
  execution context.

Impact:

- the selected signal detail inherits Markets-style provenance for quote and
  explain data.
- this does not solve the separate provenance gap for the recommendation queue
  itself, so the page mixes good detail provenance with weak recommendation-origin
  provenance.

### 4. Copilot Reports is clearly read-only, but its top-level report truth is a local artifact summary built from heuristic classification

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- `dashboard/pages/65_Copilot_Reports.py:17-18` enforces operator auth and
  labels the page with `Read-Only AI`.
- `dashboard/pages/65_Copilot_Reports.py:33-45` explicitly frames the page as
  "Evidence Packets, Not Control Buttons."
- `dashboard/services/copilot_reports.py:50-77` lists reports by scanning all
  local `*.json` files under `report_root()`.
- `dashboard/services/copilot_reports.py:21-34` classifies report kind by
  payload-shape heuristics, for example:
  - `monitor_name` + `events` -> `incident_monitor`
  - `risk_tier` + `changed_files` -> `repo_review`
  - `selected_strategy` + `top_rows` -> `strategy_lab`
- `dashboard/services/copilot_reports.py:96-113` summary badges/counts are built
  from the entire local report set, not a current-run or current-window slice.
- `dashboard/pages/65_Copilot_Reports.py:97-141` shows:
  - kind
  - severity
  - file stem
  - generated timestamp
  but does not distinguish current-window vs historical artifacts.

Impact:

- the Copilot Reports page is disciplined about read-only boundaries.
- its top-level counts and "latest kind" are local artifact-browser truth, not a
  scoped current-runtime truth surface.
- operators can inspect exact payloads, but the page-level summary should not be
  read as a current-window operational count without deeper inspection.

## SHOWN strengths

- Markets selected-detail view exposes quote-source provenance and reasoning-provider/fallback status.
- Signals selected-detail view reuses that selected-asset provenance path.
- Copilot Reports is explicit about read-only posture and provides raw JSON payload inspection.
- `VERIFIED_ENV`:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_dashboard_asset_detail.py tests/test_dashboard_copilot_reports.py tests/test_dashboard_copilot_reports_page.py tests/test_dashboard_page_runtime.py`
  - result: `29 passed in 0.52s`

## UNVERIFIED points

- whether the current table layouts make the source gaps obvious or easy to miss
  in browser use
- whether operators are currently relying more on selected-detail provenance or
  queue-table summaries when making decisions
- whether historical Copilot report aggregation is acceptable for operator usage
  on this page, or whether that summary is being over-read as current-runtime truth

## Highest-leverage next evidence action

Audit the remaining operator-facing runtime pages where source/truth could still
be overstated:

1. Trades page source provenance vs live/paper/audit rows
2. Automation/Settings runtime truth framing
3. manual browser smoke only if page-level clarity needs direct proof

## Handoff

- Active role: `AUDITOR`
- Acceptance state: `INCOMPLETE`
- Improvement from this pass:
  - separated page-level provenance strengths from remaining source gaps
  - established that Markets/Signals detail provenance is stronger than queue-level provenance
  - established that Copilot Reports page summary is a local artifact browser, not a current-window truth surface
- Proof required next:
  - source audit for Trades and automation-facing surfaces
  - browser/UI smoke if operator-clarity proof is required

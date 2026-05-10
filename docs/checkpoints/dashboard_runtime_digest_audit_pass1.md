# Dashboard Runtime Digest Audit — Pass 1

**Date:** 2026-05-10  
**Section:** 6. Dashboard and Operator UI  
**Status:** IN PROGRESS

This pass audits the dashboard digest and overview surfaces against the current
supervised paper-soak evidence path. It does not change the dashboard or the
running soak.

## Scope

- Home Digest page
- Overview page digest summary
- Help page runtime snapshot
- digest builders for runtime truth, freshness, and incidents
- current dashboard digest/runtime test coverage

## Evidence reviewed

- `dashboard/pages/00_Home.py`
- `dashboard/app.py`
- `dashboard/pages/05_Help.py`
- `dashboard/components/digest.py`
- `dashboard/components/summary_panels.py`
- `dashboard/services/digest/builders.py`
- `dashboard/services/operator.py`
- `scripts/report_supervised_soak_status.py`
- `docs/CURRENT_RUNTIME_TRUTH.md`
- `tests/test_dashboard_home_digest.py`
- `tests/test_dashboard_page_runtime.py`
- `tests/test_dashboard_pages_compile.py`
- repo search in `dashboard/` and `tests/` for:
  - `report_supervised_soak_status`
  - `counts_for_paper_gate`
  - `runtime_matches_current_desired_state`
  - `elapsed_hours`
  - `remaining_hours`

## Checklist status

- [x] Verified that Home, Overview, and Help all depend on the digest builder lane.
- [x] Verified that the digest builder lane does not consume the canonical supervised soak reporter.
- [x] Verified that freshness and incident cards are built from collector/runtime summary inputs rather than supervised soak evidence.
- [x] Verified that the current digest-related dashboard test slice passes.
- [ ] Manual browser/UI smoke was not performed in this pass.

## SHOWN findings

### 1. The Home Digest "Runtime Truth Strip" is not the canonical paper-soak truth surface

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `dashboard/pages/00_Home.py:31-55` builds the page entirely from
  `build_home_digest()` and renders `render_runtime_truth_strip`,
  `render_freshness_panel`, and `render_recent_incidents`.
- `dashboard/services/digest/builders.py:1420-1491` builds that digest from:
  - merged runtime config
  - system guard / live guard state
  - strategy evidence
  - collector runtime
  - crypto-edge live snapshot
  - `get_operations_snapshot()`
- `dashboard/services/digest/builders.py:337-389` defines the runtime-truth
  content around:
  - mode
  - kill switch
  - system guard
  - live boundary state
- `dashboard/components/digest.py:138-170` renders only these pills:
  - `mode`
  - `live_order_authority`
  - `kill_switch`
  - `system_guard`
  - `collector_freshness`
  - `leaderboard_age`
  - `copilot_trust_layer`
- repo search across `dashboard/` and `tests/` found no dashboard usage of:
  - `report_supervised_soak_status`
  - `counts_for_paper_gate`
  - `runtime_matches_current_desired_state`
  - `elapsed_hours`
  - `remaining_hours`

Impact:

- the digest page’s "Runtime Truth Strip" is a config/governance/runtime-boundary
  summary, not the canonical Section 4.1 supervised paper-soak evidence view.
- operators cannot see elapsed soak time, remaining time, counts-for-paper-gate,
  or running-vs-current desired symbol drift from this primary digest surface.

### 2. The digest freshness and incident cards are built from different evidence than the supervised soak gate

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `dashboard/services/digest/builders.py:1101-1196` builds the freshness panel
  from:
  - collector runtime timestamp
  - live-public structural-edge snapshot timestamps
  - strategy artifact timestamps
  - `operations_snapshot.last_health_ts`
- the same builder hardcodes:
  - `paper_pnl` -> `status: "missing"`
  - `caveat: "No paper PnL timestamp is exposed yet."`
- `dashboard/services/digest/builders.py:1273-1317` builds recent incidents from:
  - `overview_summary.active_warnings`
  - `collector_runtime.errors`
  - `operations_snapshot.attention_services`
- `dashboard/components/digest.py:445-466` presents those incident rows as
  "Recent Incidents / Operational Notes"

Impact:

- the Home Digest freshness and incident sections do not represent the current
  supervised paper-soak gate evidence.
- they do not expose:
  - `pipeline.errors`
  - `intent_executor` loop progression
  - `counts_for_paper_gate`
  - unique current-soak incident-family counts from the incident ledger

### 3. Overview and Help inherit the same digest omission, so the gap is broader than Operations

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `dashboard/app.py:70-89` loads `home_digest = load_home_digest(summary)` and
  renders `render_home_digest_summary(home_digest)`.
- `dashboard/components/summary_panels.py:260-349` renders that summary using:
  - runtime truth pills
  - runtime mode
  - live boundary
  - collector freshness
  - leaderboard age
  - attention-now items
  - next-best-action
- `dashboard/pages/05_Help.py:144-150` also loads `home_digest = load_home_digest()`
  and then combines it with paper evidence runtime and collector runtime.
- `dashboard/pages/05_Help.py:237-260` shows "Current Runtime Snapshot" rows for:
  - runtime mode
  - live-order authority
  - paper evidence campaign
  - collector loop
- none of these surfaces call the supervised soak reporter or expose Section 4.1
  fields directly.

Impact:

- the omission is not limited to `60_Operations.py`.
- the main read-oriented dashboard surfaces also omit the canonical supervised
  soak gate evidence.

### 4. Current digest tests validate config-driven paper truth, not supervised soak integration

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- `tests/test_dashboard_home_digest.py:37-118` verifies paper truth through:
  - `_load_trading_cfg`
  - `get_system_guard_state`
  - `is_live_enabled`
  - `live_allowed`
  - strategy/collector stubs
- the same test asserts:
  - `payload["runtime_truth"]["mode"]["value"] == "Paper"`
  - `payload["runtime_truth"]["live_order_authority"]["value"] == "Healthy"`
  - `payload["next_best_action"]["title"] == "Runtime is paper-first"`
- no visible digest/page test asserts:
  - `counts_for_paper_gate`
  - `elapsed_hours`
  - `remaining_hours`
  - `runtime_matches_current_desired_state`
  - supervised paper-soak Section 4.1 text
- `VERIFIED_ENV`:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_dashboard_home_digest.py tests/test_dashboard_page_runtime.py tests/test_dashboard_pages_compile.py`
  - result: `30 passed in 0.42s`

Impact:

- the current digest test slice is structurally healthy but does not protect the
  operator-facing supervised soak evidence path.

## SHOWN strengths

- the Home/Overview/Help digest surfaces compile and their targeted test slice passes.
- the digest path clearly labels mode truth, live-boundary status, and collector freshness.
- Help already distinguishes paper evidence runtime from live-order authority, so the UI has some boundary discipline even if it lacks Section 4.1 truth.

## UNVERIFIED points

- whether any browser-rendered UI layout visually implies that the digest cards
  are equivalent to the supervised soak gate
- whether any page outside the reviewed digest/overview/help/operations set
  exposes Section 4.1 evidence indirectly
- whether operators are currently relying more on the dashboard or the CLI soak
  reporter during the active paper gate

## Highest-leverage next evidence action

Audit the remaining dashboard truth surfaces that may affect operator decisions:

1. `dashboard/services/view_data.py` and overview summary provenance
2. Copilot Reports and Markets/Signals runtime-truth carry-through
3. manual browser smoke only if visual/operator clarity proof is needed

## Handoff

- Active role: `AUDITOR`
- Acceptance state: `INCOMPLETE`
- Improvement from this pass:
  - established that the dashboard omission is broader than Operations
  - established that Home/Overview/Help digest surfaces are not the canonical
    supervised paper-soak evidence view
  - separated digest/runtime-boundary truth from supervised soak-gate truth
- Proof required next:
  - provenance audit for `view_data` / overview summary inputs
  - determination of whether any remaining dashboard surface already carries
    Section 4.1 evidence

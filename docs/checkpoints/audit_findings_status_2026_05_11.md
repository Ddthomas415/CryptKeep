# Audit Findings Status Overlay — 2026-05-11

**Date:** 2026-05-11  
**Purpose:** prevent historical audit notes from drifting into stale blocker lists  
**Scope:** overlay current status on top of historical pass notes without
rewriting the original evidence record

This file is the current status ledger for major audit findings. Historical
pass notes remain valid as evidence of what was true when they were written.
They are **not** the authoritative source for current blocker status once a
remediation branch exists or a finding has been independently accepted.

## Status vocabulary

- `OPEN_IN_ACTIVE_BRANCH`
  - finding is still present in the active soak checkout
- `ACCEPTED_FIX_NOT_LANDED`
  - independently accepted remediation exists on an isolated branch/worktree
  - the active soak checkout has intentionally not been modified yet
- `READY_FOR_REVIEW`
  - isolated remediation branch exists but has not yet been independently accepted
- `HISTORICAL_ONLY`
  - finding was accurate when written, but should no longer drive current
    prioritization without checking this overlay

## Major finding ledger

| Finding | Historical source | Current status | Accepted / review branch | Landed in active soak checkout? | Notes |
|---|---|---|---|---|---|
| `H1` VIEWER partial live arming path | `pass2b_adversarial_h1_h2.md`, `pass2g_admin_arming_wizards.md` | `ACCEPTED_FIX_NOT_LANDED` | `codex/dashboard-operator-guards` @ `847d8edf0` | No | Page gates and save-path role enforcement were independently accepted. |
| `H2` VIEWER writes API keys / settings mutation | `pass2b_adversarial_h1_h2.md` | `ACCEPTED_FIX_NOT_LANDED` | `codex/dashboard-operator-guards` @ `847d8edf0` | No | Service-layer operator enforcement added and accepted. |
| `H3` VIEWER paper reconciliation mutation | `pass2c_dashboard_pages.md` | `ACCEPTED_FIX_NOT_LANDED` | `codex/dashboard-operator-guards` @ `847d8edf0` | No | `44_Paper_Reconciliation.py` gate raised on accepted branch. |
| `H4` governance enforcement dead code | `pass2f_ops_admin_governance_dead_code.md` | `ACCEPTED_FIX_NOT_LANDED` | `codex/governance-enforcement-wiring` @ `8601aafae` | No | Paper evidence campaign service now consults governance wrappers on accepted branch. |
| `H5A` `resume_if_safe` disconnected from config | `pass2i_resume_safe_mode_watchdog.md` | `ACCEPTED_FIX_NOT_LANDED` | `codex/resume-gate-coherence` @ `62f50d643` | No | Resume flow restores persisted live-enable flag before guard re-check on accepted branch. |
| `H5B` missing/invalid system guard can fail open in `live_guard` | follow-up repo review after `pass2i` | `ACCEPTED_FIX_NOT_LANDED` | `codex/live-guard-failclosed` @ `4a1e10ec4` | No | `live_allowed()` now blocks explicitly on missing/invalid guard state on accepted branch. |
| `H6` soak evidence invisible to promotion gate | `pass2l_strategy_registry.md` | `ACCEPTED_FIX_NOT_LANDED` | `codex/h6-soak-evidence-fix` @ `fa50ff181` | No | Evidence/promotion mapping fixed on soak-target side branch; active soak checkout intentionally unchanged. |
| `M1` safe wrapper points to paper-era consumer | `execution_routing_risk_gates_audit_pass1.md` | `ACCEPTED_FIX_NOT_LANDED` | `codex/safe-idle-status-surface` @ `d33c53566` | No | Accepted branch also includes `83110b21b` live-consumer wrapper correction. |
| `M2` safe wrappers can look healthy while idle after crash | `execution_routing_risk_gates_audit_pass1.md` | `ACCEPTED_FIX_NOT_LANDED` | `codex/safe-idle-status-surface` @ `d33c53566` | No | Accepted branch surfaces `safe_idle` / `blocked` as unhealthy runtime truth. |
| Trades provenance gap | `dashboard_trades_provenance_audit_pass1.md` | `READY_FOR_REVIEW` | `codex/trades-provenance-truth` @ `fba06b3c3` | No | Synthetic/default rows and recent fills are labeled on the prepared branch, but independent review has not yet been recorded. |

## Findings that still look open from current visible evidence

These do **not** have an accepted remediation branch recorded in this audit lane.

| Finding | Current status | Source |
|---|---|---|
| Governance signoff doc is frozen at 2026-03-21 and stale for current branch/strategy | `OPEN_IN_ACTIVE_BRANCH` | `evidence_promotion_governance_audit_pass1.md` |
| Governance checklist describes a different branch/strategy lineage | `OPEN_IN_ACTIVE_BRANCH` | `evidence_promotion_governance_audit_pass1.md` |
| Automation `execution_enabled` badge is layered source, not canonical arming truth | `OPEN_IN_ACTIVE_BRANCH` | `dashboard_automation_settings_audit_pass1.md` |
| Settings provider status is saved config string, not live probe truth | `OPEN_IN_ACTIVE_BRANCH` | `dashboard_automation_settings_audit_pass1.md` |
| Silent fallback from unknown strategy name to `ema_cross` | `OPEN_IN_ACTIVE_BRANCH` | `pass2l_strategy_registry.md` |
| Paper soak operator policy questions remain unresolved | `OPEN_IN_ACTIVE_BRANCH` | `paper_soak_runtime_evidence_audit_pass1.md`, `PAPER_SOAK_GATE.md` |

## Operator guidance

- For historical evidence: read the original pass note.
- For current blocker status: read this overlay first.
- For branch safety: treat `ACCEPTED_FIX_NOT_LANDED` as “remediated in review
  branch, not yet merged into the active soak checkout.”
- Do not treat an accepted isolated branch as proof that the active soak
  checkout already contains the fix.

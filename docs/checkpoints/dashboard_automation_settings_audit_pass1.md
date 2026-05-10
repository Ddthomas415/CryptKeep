# Automation and Settings Runtime-Truth Framing Audit — Pass 1

**Date:** 2026-05-10
**Section:** 6. Dashboard and Operator UI
**Scope:** Automation and Settings pages — runtime posture framing
**Status:** COMPLETE

---

## Scope

- `dashboard/pages/50_Automation.py`
- `dashboard/pages/70_Settings.py`
- `dashboard/services/views/settings_view.py` — `get_automation_view()`,
  `update_automation_view()`, `get_settings_view()`

## Evidence reviewed

- Full read of `dashboard/pages/50_Automation.py`
- Full read of `dashboard/pages/70_Settings.py`
- `get_automation_view()` at `settings_view.py:97`
- `update_automation_view()` at `settings_view.py:162`
- `get_settings_view()` at `settings_view.py:22`

## Checklist status

- [x] Verified where `execution_enabled`, `executor_mode`, `live_enabled` are sourced from.
- [x] Verified whether `update_automation_view` calls the canonical arming boundary.
- [x] Verified what runtime truth Settings surfaces and what it does not.
- [x] Verified security section framing.
- [ ] Manual browser smoke not performed in this pass.

---

## SHOWN findings

### Finding 1 — `execution_enabled` reads from a layered source, not canonical arming truth (Medium)

`get_automation_view()` (`settings_view.py:108`):

```python
execution_enabled = bool(
    automation_ui.get("enabled", summary.get("execution_enabled", False))
)
```

Reads first from `dashboard_ui.automation.enabled` in user config, then falls
back to `summary.get("execution_enabled")` from `get_dashboard_summary()` which
is API-sourced and may be stale or mocked.

The canonical arming truth is `services.execution.live_arming.is_live_enabled()`.
The Automation page does not call this function.

Contrast: `executor_mode` and `live_enabled` ARE read from `runtime_execution`
which is `load_user_yaml()["execution"]` — the actual config file. Those are closer
to canonical than `execution_enabled`.

**Impact:** The Enabled/Disabled badge may not match actual arming state.

---

### Finding 2 — Save path writes through canonical arming boundary (Strength)

`update_automation_view()` calls:

```python
from services.execution.live_arming import set_live_enabled
cfg = set_live_enabled(cfg, runtime_live_enabled)
```

Saving via the Automation page correctly goes through the canonical arming
function. The gap is read-only: displayed state may be stale, but the write
is correct.

---

### Finding 3 — `dry_run_mode` override logic is implicit (Low)

If `dry_run_mode=True`, both `runtime_live_enabled=False` and `executor_mode="paper"`
regardless of `execution_enabled` and `default_mode`. This is the correct safety
behavior but is not labeled on the page. An operator enabling automation with
`default_mode=live_auto` and `dry_run_mode=True` will see `execution_enabled=True`
in the badge without understanding why live is still blocked.

---

### Finding 4 — Automation caption exposes config_path, executor_mode, live_enabled (Strength)

The page renders:

```python
st.caption(
    f"Runtime config path: {automation_view.get('config_path')}  "
    f"(executor_mode={automation_view.get('executor_mode')}, "
    f"live_enabled={automation_view.get('live_enabled')})"
)
```

This is the strongest runtime-truth framing of any dashboard page reviewed.
The operator sees exactly which config file is in use plus the current executor
mode and live-enabled state directly on the page.

---

### Finding 5 — Settings provider status is config-file truth, not live connectivity (Medium)

`_render_provider_card()` reads:

```python
status = str(provider.get("status") or "ready").replace("_", " ").title()
```

This is the last-saved status string from the user config, not a live probe.
A provider saved as `"status": "ready"` months ago still shows Ready even if
the API key has expired or the endpoint is down.

**Impact:** Provider status badges may mislead operators verifying connectivity
before enabling a provider.

---

### Finding 6 — Settings does not surface canonical soak or service state (Medium)

`get_settings_view()` reads exclusively from `load_user_yaml()`. It does not
consult `report_supervised_soak_status.py`, `bot_status.py`,
`check_system_health.py`, or runtime status files. The page shows configured
posture, not running posture. Known gap, expected for a settings page.

---

### Finding 7 — Security section has strong framing (Strength)

Explicit warnings when auth_scope is `remote_public_candidate` without outer
access control configured. The page shows `st.error()` when the combination is
unsafe. This matches the discipline of the launch blockers doc.

---

## Summary

| Surface | Source | Quality |
|---|---|---|
| Automation `execution_enabled` badge | dashboard_summary (API/mock) | Weak |
| Automation `executor_mode`, `live_enabled` | load_user_yaml() | Good |
| Automation config caption | config_path, executor_mode, live_enabled | **Strong** |
| Automation save path | set_live_enabled() canonical | **Strong** |
| Settings provider status | Last-saved config string | Weak |
| Settings soak/service state | Not surfaced | Gap (by design) |
| Settings security framing | Explicit unsafe-combo warnings | **Strong** |

---

## UNVERIFIED points

- Whether `_load_automation_operations_snapshot()` reads from canonical runtime
  status files or from the dashboard_summary API payload.
- Whether operators rely on the badge vs the caption to infer arming state.
- Whether stale provider status has caused operational decisions.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Automation and Settings
**Next target:** per `full_repo_audit_master_todo.md`:
Section 3 — Execution, Routing, and Risk Gates
or Section 9 — Auth, Roles, and Safety Boundaries

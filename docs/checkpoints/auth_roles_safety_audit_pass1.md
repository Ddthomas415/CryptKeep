# Auth, Roles, and Safety Boundaries Audit — Pass 1

**Date:** 2026-05-10
**Section:** 9. Auth, Roles, and Safety Boundaries
**Status:** COMPLETE

---

## Scope

- `dashboard/auth_gate.py`
- `dashboard/role_guard.py`
- `services/security/auth_capabilities.py`
- `dashboard/services/operator.py`
- `dashboard/pages/` — role assignments

---

## Checklist status

- [x] Verified auth runtime guard surfaces are current.
- [x] Verified role boundaries on operator pages and actions.
- [x] Verified bypass behavior is gated to dev mode only.
- [x] Verified RolePolicy enforcement paths.
- [x] Verified lockout uses server-side store.
- [ ] No unauthorized viewer-to-state-change path — **Finding 1 open.**
- [ ] Manual browser smoke not performed.

---

## SHOWN findings

### Finding 1 — Settings and Automation pages require VIEWER but expose save actions (High)

`dashboard/pages/70_Settings.py:20`:
```python
AUTH_STATE = require_authenticated_role("VIEWER")
```
`dashboard/pages/50_Automation.py:15`:
```python
AUTH_STATE = require_authenticated_role("VIEWER")
```

Both pages expose `render_save_action` that writes state:

- Settings: writes API keys for all providers, auth scope, session timeout,
  paper trading parameters via `update_settings_view`.
- Automation: writes `execution_enabled`, `executor_mode`, calls
  `set_live_enabled()` — the canonical arming function — via
  `update_automation_view`.

Any authenticated VIEWER can trigger the live arming function by saving
Automation settings with `execution_enabled=True` and `default_mode=live_auto`.

This conflicts with `RolePolicy.execute_required = "ADMIN"` and
`RolePolicy.approve_required = "OPERATOR"` in `role_guard.py`.

---

### Finding 2 — RolePolicy defined but not enforced on save paths (Medium)

`dashboard/role_guard.py`:
```python
@dataclass(frozen=True)
class RolePolicy:
    generate_required: Role = "OPERATOR"
    approve_required: Role = "OPERATOR"
    execute_required: Role = "ADMIN"
```

`dashboard/services/operator.py` correctly calls
`require_role(current_role, "OPERATOR")` on 12 call sites for Operations page
actions. But `update_automation_view` and `update_settings_view` have no
`require_role` check. The policy is stated but not enforced on those paths.

---

### Finding 3 — Auth bypass is correctly gated to dev mode (Strength)

```python
def _dashboard_auth_bypassed() -> bool:
    return _app_env() == "dev" and _truthy_env("BYPASS_DASHBOARD_AUTH")

def _bypass_requested_outside_dev() -> bool:
    return _app_env() != "dev" and _truthy_env("BYPASS_DASHBOARD_AUTH")
```

Bypass requires both `APP_ENV=dev` AND `BYPASS_DASHBOARD_AUTH=1`. Bypass
outside dev shows `st.error()` — it does not silently pass.

---

### Finding 4 — Lockout uses server-side SQLite, not session state (Strength)

Failed login counts and lockout timestamps are recorded in
`user_auth_store`. Session state is an explicit display cache only:

```python
# Clear server-side lockout; session state is display cache only
_server_clear_failed_logins(str(username or ""))
```

Lockout survives tab refresh and new sessions. Correct.

---

### Finding 5 — Operations page correctly requires OPERATOR (Strength)

`60_Operations.py:72` — `require_authenticated_role("OPERATOR")`

`dashboard/services/operator.py` — 12 call sites of
`require_role(current_role, "OPERATOR")` covering arm/disarm, kill switch,
halt, order approval.

Live execution control plane is correctly gated. The gap is only on the
Settings and Automation save paths.

---

### Finding 6 — supervisor_process.py requires ADMIN for process control (Strength)

`services/process/supervisor_process.py:93`:
```python
require_role(current_role, "ADMIN")
```

Process-level supervisor control requires the highest role. Correct.

---

## Role summary

| Page | Role | Has save? | Save writes to |
|---|---|---|---|
| 00_Home | VIEWER | No | — |
| 00_Operator | OPERATOR | Yes | Operator actions |
| 40_Trades | VIEWER | No | — |
| **50_Automation** | **VIEWER** | **Yes** | **live arming, executor_mode** |
| 60_Operations | OPERATOR | Yes | arm/disarm, kill switch |
| 65_Copilot_Reports | OPERATOR | No | — |
| **70_Settings** | **VIEWER** | **Yes** | **API keys, auth scope, paper config** |

---

## UNVERIFIED points

- Whether `render_save_action` enforces any role check internally.
- Whether current operators are all OPERATOR or above (no VIEWER-only accounts).
- Whether `update_automation_view` is reachable outside the dashboard.

---

## Highest-leverage next action

Raise `50_Automation.py` and `70_Settings.py` to
`require_authenticated_role("OPERATOR")`, or add `require_role` inside
`update_automation_view` and `update_settings_view`. Either aligns the
implementation with the stated `RolePolicy`.

Per current audit scope: record, do not remediate.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Section 9
**Next target:** Section 10 — Release, Validation, and Operator Docs
or Section 4 — Storage and State Integrity

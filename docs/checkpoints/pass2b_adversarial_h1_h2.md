# Pass 2B — Adversarial Verification of H1 and H2

**Date:** 2026-05-10  
**Pass:** 2B — adversarial verification of High findings  
**Status:** COMPLETE — both findings CONFIRMED exploitable

---

## H1 — VIEWER can arm live via Automation save

### Adversarial trace

**Step 1:** Any authenticated user passes VIEWER gate.
```python
# 50_Automation.py:15
AUTH_STATE = require_authenticated_role("VIEWER")
```

**Step 2:** User clicks Save.
```python
render_save_action(save_fn=update_automation_view, payload=payload, ...)
```

**Step 3:** `render_save_action` calls `save_fn` unconditionally.
```python
# dashboard/components/forms.py
def render_save_action(*, save_fn, payload, ...):
    if st.button(...):
        st.session_state[key] = save_fn(payload)   # NO role check
```

**Step 4:** `update_automation_view` has zero role checks.
```python
# settings_view.py:156
def update_automation_view(payload):
    # NO require_role() call
    cfg = set_live_enabled(cfg, runtime_live_enabled)  # canonical arming
```

**Verdict: CONFIRMED.** VIEWER → canonical arming. Zero role checks in chain.

---

## H2 — VIEWER can write API keys via Settings save

### Adversarial trace

Same pattern. `70_Settings.py` requires VIEWER. `render_save_action` has
no role check. `update_settings_view` has no `require_role()` call.
Writes: provider API keys, auth_scope, session_timeout, paper trading config.

**Verdict: CONFIRMED.** VIEWER → API key writes. Zero role checks in chain.

---

## Fix specification

### Option A — Raise page-level role (recommended, one line per page)

```python
# 50_Automation.py:15
AUTH_STATE = require_authenticated_role("OPERATOR")  # was VIEWER

# 70_Settings.py:20
AUTH_STATE = require_authenticated_role("OPERATOR")  # was VIEWER
```

Aligns with `RolePolicy.execute_required = "OPERATOR"` and matches
`60_Operations.py` which already requires OPERATOR. VIEWERs cannot access
these pages.

### Option B — require_role inside save functions (defense-in-depth)

Pass `current_role` through payload. VIEWERs can still read but not save.
More granular but requires threading role context through two layers.

**Recommendation: Option A.** Simplest, most reliable, no new patterns.

---

## Impact on current soak

Current environment has no VIEWER-only accounts. H1 and H2 are not
exploitable today. Must be fixed before any multi-user deployment.

---

## Handoff

**Active role:** AUDITOR  
**Acceptance state:** COMPLETE for Pass 2B  
**H1 and H2:** CONFIRMED exploitable, fix specification documented  
**Next:** Pass 2C — unread dashboard pages, or open fix PR for H1/H2

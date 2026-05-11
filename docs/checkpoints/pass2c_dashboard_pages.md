# Pass 2C — Unread Dashboard Pages

**Date:** 2026-05-10  
**Pass:** 2C — dashboard pages not read in pass 1  
**Status:** COMPLETE

## Status update — 2026-05-11

- Historical finding `H3` remains valid as evidence of the bug at audit time.
- Independently accepted remediation now exists on:
  - `codex/dashboard-operator-guards` @ `847d8edf0`
- That remediation has **not** been landed into the active soak checkout.
- Current blocker status is tracked in:
  - [audit_findings_status_2026_05_11.md](./audit_findings_status_2026_05_11.md)

---

## Pages read

1. `44_Paper_Reconciliation.py`
2. `20_Portfolio.py`
3. `35_Research.py`
4. `99_Legacy_UI.py`

---

## SHOWN findings

### Finding 1 — H3: `44_Paper_Reconciliation.py` runs a state-changing action as VIEWER (Medium)

```python
AUTH_STATE = require_authenticated_role("VIEWER")
```

```python
if run_now:
    result = reconcile_execution_plan_intents(
        default_fill_price=float(default_fill_price),
        venue=str(venue),
    )
```

`reconcile_execution_plan_intents` writes paper positions (`insert_position`)
and updates intent status (`upsert_intent` / `update_intent`). Any VIEWER
can run paper reconciliation at any venue with any fill price. No role check.

This is a **third instance** of the VIEWER-can-mutate pattern (H1: arming,
H2: API keys, H3: paper state). Impact is lower — paper state only, not live
arming — but a VIEWER can corrupt paper position state and affect soak evidence.

**Fix:** raise to `require_authenticated_role("OPERATOR")`.

---

### Finding 2 — `35_Research.py` correctly enforces OPERATOR on start/stop (Strength)

The page is VIEWER-accessible for reading. Start/stop collector actions pass
`current_role=CURRENT_ROLE` to `operator.py` functions which enforce
`require_role(current_role, "OPERATOR")`. A VIEWER who clicks Start gets a
`PermissionError` before any action is taken.

**This is the correct pattern** — read access for VIEWERs, write gated at
OPERATOR via `require_role` inside the action function. This is what
`50_Automation.py` and `70_Settings.py` should follow.

---

### Finding 3 — `20_Portfolio.py` is read-only, clean (Strength)

VIEWER access, `get_portfolio_view()` is read-only. No save actions. Appropriate.

---

### Finding 4 — `99_Legacy_UI.py` is correctly retired and requires OPERATOR (Strength)

`require_authenticated_role("OPERATOR")`. Retired page with warning and redirect only.
No state-changing actions. Correct.

---

## Not yet read (13 pages)

```
05_Help.py                    36_Symbol_Scanner.py
37_Coinbase_Movers.py         38_Rotation_And_Correlation.py
39_Cross_Exchange_Alerts.py   40_Market_Intelligence.py
41_Order_Book_Intelligence.py 42_Portfolio_Allocation.py
43_Execution_Plan.py          45_Selector_Backtest.py
46_Historical_Selector_Backtest.py
47_Preset_Comparison.py       48_Runtime_Outcome_Summary.py
```

---

## Summary

| Page | Auth | State-changing? | Finding |
|---|---|---|---|
| `44_Paper_Reconciliation.py` | VIEWER | Yes — reconcile intents | **H3: raise to OPERATOR** |
| `35_Research.py` | VIEWER (read) | Yes — role-gated correctly | **Strength** |
| `20_Portfolio.py` | VIEWER | No | Clean |
| `99_Legacy_UI.py` | OPERATOR | No — retired | **Strength** |

---

## Handoff

**Active role:** AUDITOR  
**Acceptance state:** COMPLETE for Pass 2C (priority pages)  
**New finding:** H3 — VIEWER can corrupt paper state via reconciliation  
**Next:** Pass 2D — zero-coverage services, or fix PRs for H1/H2/H3

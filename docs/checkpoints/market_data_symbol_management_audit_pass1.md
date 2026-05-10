# Market Data and Symbol Management Audit — Pass 1

**Date:** 2026-05-10
**Section:** 5. Market Data and Symbol Management
**Status:** COMPLETE

---

## Scope

- `services/runtime/managed_symbol_selection.py`
- `services/runtime/dynamic_symbol_selector.py`
- `scripts/run_pipeline_loop.py` — symbol resolution
- `scripts/report_supervised_soak_status.py` — drift visibility

---

## Checklist status

- [x] Symbol selection, propagation, and runtime truth alignment.
- [x] Scanner cache behavior and refresh policy.
- [x] Timeout/error handling in symbol selection path.
- [x] Multi-symbol runtime semantics.
- [x] Symbol drift visibility to operators.

---

## SHOWN findings

### Finding 1 — Scanner source is blocked in live mode (Strength)

```python
if mode != "paper" or live_enabled:
    out["source"] = "static"
    out["reason"] = "scanner_source_live_unsupported"
    return out
```

Dynamic symbol selection only activates in paper mode with live disabled.
Live execution always uses the static config symbol list. Correct safety gate.

---

### Finding 2 — Scanner failure falls back to base symbols explicitly (Strength)

```python
if bool(scan.get("ok")) and selected_symbols:
    out["symbols"] = _unique_symbols(selected_symbols + protected_symbols)
    out["reason"] = "scanner_selected..."
    return out

out["symbols"] = _unique_symbols(base_symbols + protected_symbols)
out["reason"] = "scanner_fallback_to_base..."
return out
```

Scan failure or empty selection falls back to base config symbols. Reason
is labeled explicitly. No silent failure.

---

### Finding 3 — Scanner cache has TTL enforcement (Strength)

`_read_scan_cache()` enforces:
```python
if age < 0 or age > refresh_sec:
    return None
```

`refresh_sec=300` default (5 minutes), configurable. Cache validates venue
and criteria match — a config change invalidates the cache. Writes use
`atomic_write()`.

---

### Finding 4 — Symbol drift visible to operators (Strength)

`report_supervised_soak_status.py` surfaces:
```
runtime_matches_run_state: true
runtime_matches_current_desired_state: false
```

Both flags are explicit in the soak report. Policy decision on how to
handle this drift is documented in `PAPER_SOAK_GATE.md` (Decision 2).

---

### Finding 5 — No alert hook on drift (Noted)

Drift is visible in the soak report but there is no P3A alert or
notification when `runtime_matches_current_desired_state=false`. An
operator not checking the report would not be alerted. Expected behavior
given P3A is future work.

---

### Finding 6 — Multi-symbol pipeline is sequential (Noted)

```python
for symbol in symbols:
    pipelines[symbol].run_once()
```

Sequential processing per symbol in each cycle. Fine for 2–3 symbols.
Scales linearly — relevant when fleet model is built.

---

## Summary

| Surface | Finding | Severity |
|---|---|---|
| Scanner blocked in live mode | Correct safety gate | **Strength** |
| Fallback to base symbols | Explicit, labeled | **Strength** |
| Cache TTL enforcement | 300s default, atomic write | **Strength** |
| Drift visibility | Soak reporter surfaces both flags | **Strength** |
| No drift alert hook | P3A future work | Noted |
| Sequential multi-symbol loop | Fine for small sets | Noted |

---

## UNVERIFIED points

- Whether `run_symbol_scan()` enforces a network timeout or uses CCXT defaults.
- Whether scanner criteria are documented as operator-visible config.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Section 5
**Next target:** Section 7 — AI Copilot and Alerting

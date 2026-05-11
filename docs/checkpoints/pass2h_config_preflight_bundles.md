# Pass 2H — Config Editor, Preflight, and Profiles

**Date:** 2026-05-10
**Pass:** 2H
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — `save_user_yaml` is non-atomic but backup-protected (Noted)

Write sequence:
1. `BACKUP_PATH.write_bytes(CONFIG_PATH.read_bytes())` -- backup first
2. `CONFIG_PATH.open('w')` -- overwrite

Interruption between 1 and 2: backup exists, config corrupted. Interrupted
mid-step 2: config partially written, backup available. `load_user_yaml` on
corrupt YAML silently returns `{}`. Operator must restore `.bak` manually.

Not using `atomic_write` -- same inconsistency as PID files etc.

---

### Finding 2 — `load_user_yaml` silently returns `{}` on any error (Noted)

```python
except Exception as e:
    print(f'Error loading config: ...')   # stdout, not log file
    return {}
```

Corrupt config = empty dict = hardcoded defaults everywhere. Mostly fail-safe
(is_live_enabled({}) returns False, exchange adapter fails closed). But the
error prints to stdout rather than to the operator log file.

---

### Finding 3 — `validate_user_yaml` is comprehensive (Strength)

Validates all sections: preflight, paper_execution, signals, execution, risk,
paper_trading, managed_symbols, dashboard_ui. Error codes: machine-readable
`section.key:reason` format. Returns (ok, errors, warnings) tuple. Called by
`pre_release_sanity.py`.

---

### Finding 4 — Preflight calls `ensure_kill_default()` first (Strength)

```python
async def run_preflight(...):
    ensure_kill_default()   # kill switch armed before any connectivity
```

Kill switch guaranteed to exist and be ARMED before probes run. Crash during
preflight leaves kill switch in known safe state.

---

### Finding 5 — Preflight exceptions produce structured results (Strength)

`_safe_private_connectivity` and `_safe_probes` both catch all exceptions and
return `{'ok': False, 'reason': type(e).__name__, ...}`. Preflight failures are
reported, not raised. Preflight is advisory, not a hard gate.

---

### Finding 6 — `PAPER_SAFE_DEFAULTS` bundle is conservative (Strength)

```
mode: paper
max_order_quote: 100.0      ($100 per order)
max_portfolio_exposure: 800.0  ($800 max)
ws_enabled: False
```

Compare to `risk_gate.py` permissive defaults ($10,000/$50,000).
PAPER_SAFE_DEFAULTS is what should be applied before any paper soak.

---

### Finding 7 — `_deep_merge` uses deepcopy throughout (Strength)

No shared references between bundles or between bundle and caller. Mutations
on merged output don't affect original bundle definitions.

---

## Summary

| Finding | Severity |
|---|---|
| `save_user_yaml` non-atomic; backup-protected | Noted |
| `load_user_yaml` returns {} silently; stdout not log | Noted |
| `validate_user_yaml` comprehensive | **Strength** |
| Preflight `ensure_kill_default()` first | **Strength** |
| Preflight exceptions structured results | **Strength** |
| PAPER_SAFE_DEFAULTS conservative limits | **Strength** |
| `_deep_merge` deepcopy throughout | **Strength** |

---

## Updated audit map

| File | Depth |
|---|---|
| `services/admin/config_editor.py` | REVIEWED |
| `services/admin/preflight.py` | REVIEWED |
| `services/profiles/bundles.py` | REVIEWED |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2H
**Next:** `services/admin/` remaining or `services/strategies/` full reads

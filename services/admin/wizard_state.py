from __future__ import annotations

import json
import time
from typing import Any
from services.os.app_paths import data_dir

PATH = data_dir() / "wizard_reconcile.json"

DEFAULT = {
    "version": 1,
    "updated_ts": 0.0,
    "step": 1,  # 1..6
    "last_reconcile": None,
    "last_export_path": None,
    "last_cancel_unknown": None,
    "last_reconcile_after_cancel": None,
    "last_resolve": None,
    "last_resume": None,
}

def load() -> dict[str, Any]:
    try:
        if not PATH.exists():
            return dict(DEFAULT)
        d = json.loads(PATH.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            return dict(DEFAULT)
        out = dict(DEFAULT)
        out.update(d)
        return out
    except Exception:
        return dict(DEFAULT)

def save(st: dict[str, Any]) -> dict[str, Any]:
    st = dict(st or {})
    st["updated_ts"] = float(time.time())
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"ok": True, "path": str(PATH), "updated_ts": st["updated_ts"]}

def reset() -> dict[str, Any]:
    st = dict(DEFAULT)
    save(st)
    return st

def advance(st: dict[str, Any], step: int) -> dict[str, Any]:
    st["step"] = int(step)
    save(st)
    return st


# --- compatibility wrapper (preflight/UI expects WizardState) ---
def _call_any(names, *args, **kwargs):
    for n in names:
        fn = globals().get(n)
        if callable(fn):
            return fn(*args, **kwargs)
    raise AttributeError(f"none of {names} found in wizard_state")

class WizardState:
    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def live_unlocked() -> bool:
        # Safe default: False if no underlying impl exists
        try:
            return bool(_call_any(["live_unlocked", "is_live_unlocked", "get_live_unlocked"]))
        except Exception:
            return False

# --- CBP compatibility shim (preflight/UI expect WizardState.summary + args-safe init) ---
try:
    WizardState
except NameError:
    class WizardState:
        pass

if not hasattr(WizardState, "__init__"):
    def __init__(self, *args, **kwargs):
        pass
    WizardState.__init__ = __init__

# Always safe default: False unless real impl exists
if not hasattr(WizardState, "live_unlocked"):
    def _live_unlocked() -> bool:
        fn = globals().get("live_unlocked") or globals().get("is_live_unlocked") or globals().get("get_live_unlocked")
        try:
            return bool(fn()) if callable(fn) else False
        except Exception:
            return False
    WizardState.live_unlocked = staticmethod(_live_unlocked)

# Preflight expects .summary on an instance; make it available everywhere
if not hasattr(WizardState, "summary"):
    def _summary() -> dict:
        return {
            "live_unlocked": bool(getattr(WizardState, "live_unlocked")()),
            "note": "compat shim",
        }
    WizardState.summary = staticmethod(_summary)

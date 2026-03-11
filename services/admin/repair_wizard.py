from __future__ import annotations

from typing import Any, Dict

from services.admin.repair_reset import reset_runtime_state
from services.preflight.preflight import run_preflight


CONFIRM_TEXT = "RESET STATE"


def preflight_self_check(*, cfg_path: str = "config/trading.yaml") -> Dict[str, Any]:
    pf = run_preflight(cfg_path=cfg_path)
    checks = list(getattr(pf, "checks", []) or [])
    return {
        "ok": bool(getattr(pf, "ok", False)),
        "dry_run": bool(getattr(pf, "dry_run", False)),
        "checks": checks,
    }


def preview_reset(*, include_locks: bool = False) -> Dict[str, Any]:
    out = reset_runtime_state(include_locks=bool(include_locks), dry_run=True)
    out["non_destructive"] = True
    return out


def execute_reset(*, confirm_text: str, include_locks: bool = False) -> Dict[str, Any]:
    typed = str(confirm_text or "").strip()
    if typed != CONFIRM_TEXT:
        return {"ok": False, "reason": "confirmation_mismatch", "expected": CONFIRM_TEXT}
    out = reset_runtime_state(include_locks=bool(include_locks), dry_run=False)
    out["non_destructive"] = False
    return out

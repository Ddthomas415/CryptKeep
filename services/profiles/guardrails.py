# HU1: Live guardrails for bundle apply (Phase 230)
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

def _md(cfg: dict) -> dict:
    md = cfg.get("marketdata") if isinstance(cfg.get("marketdata"), dict) else {}
    md.setdefault("ws_enabled", False)
    md.setdefault("ws_use_for_trading", False)
    md.setdefault("ws_block_on_stale", True)
    return md

def _wh(cfg: dict) -> dict:
    wh = cfg.get("ws_health") if isinstance(cfg.get("ws_health"), dict) else {}
    wh.setdefault("enabled", False)
    wh.setdefault("auto_switch_enabled", False)
    return wh


def apply_live_guardrails(cfg: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(dict(cfg or {}))
    runtime = out.get("runtime") if isinstance(out.get("runtime"), dict) else {}
    mode = str(runtime.get("mode") or "").lower().strip()
    md = _md(out)
    wh = _wh(out)
    actions: list[str] = []

    if mode == "live":
        # Live mode should fail closed on stale WS conditions.
        if not bool(md.get("ws_enabled", False)):
            md["ws_enabled"] = True
            actions.append("marketdata.ws_enabled=true")
        if not bool(md.get("ws_block_on_stale", True)):
            md["ws_block_on_stale"] = True
            actions.append("marketdata.ws_block_on_stale=true")
        if bool(md.get("ws_use_for_trading", False)) and not bool(wh.get("enabled", False)):
            wh["enabled"] = True
            actions.append("ws_health.enabled=true")
        if bool(md.get("ws_use_for_trading", False)) and not bool(wh.get("auto_switch_enabled", False)):
            wh["auto_switch_enabled"] = True
            actions.append("ws_health.auto_switch_enabled=true")

    out["marketdata"] = md
    out["ws_health"] = wh
    out["_guardrail_actions"] = actions
    return out


def validate_live_guardrails(cfg: Dict[str, Any]) -> Dict[str, Any]:
    runtime = cfg.get("runtime") if isinstance(cfg.get("runtime"), dict) else {}
    mode = str(runtime.get("mode") or "").lower().strip()
    md = _md(cfg)
    wh = _wh(cfg)
    issues: list[str] = []

    if mode == "live":
        if not bool(md.get("ws_enabled", False)):
            issues.append("marketdata.ws_enabled must be true in live mode")
        if not bool(md.get("ws_block_on_stale", False)):
            issues.append("marketdata.ws_block_on_stale must be true in live mode")
        if bool(md.get("ws_use_for_trading", False)) and not bool(wh.get("enabled", False)):
            issues.append("ws_health.enabled must be true when ws_use_for_trading=true")

    return {"ok": len(issues) == 0, "issues": issues}

from __future__ import annotations

import os
from typing import Any, Dict


def overlay_enabled(cfg: Dict[str, Any] | None = None) -> bool:
    env = str(os.environ.get("CBP_SIGNAL_OVERLAY_ENABLED") or "").strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    if env in {"0", "false", "no", "off"}:
        return False
    c = dict(cfg or {})
    section = c.get("signal_overlay") if isinstance(c.get("signal_overlay"), dict) else {}
    return bool(section.get("enabled", False))


def evaluate_overlay_guard(
    *,
    base_action: str,
    overlay_action: str,
    overlay_score: float,
    max_abs_score: float = 1.0,
    allow_flip: bool = True,
) -> Dict[str, Any]:
    b = str(base_action).lower().strip()
    o = str(overlay_action).lower().strip()
    s = float(overlay_score)
    if abs(s) > float(max_abs_score):
        return {"ok": False, "allow": False, "reason": "score_out_of_bounds"}
    if not allow_flip and b in {"buy", "sell"} and o in {"buy", "sell"} and b != o:
        return {"ok": False, "allow": False, "reason": "flip_not_allowed"}
    return {"ok": True, "allow": True, "reason": "ok"}

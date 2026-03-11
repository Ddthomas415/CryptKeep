from __future__ import annotations

from typing import Any, Dict, Iterable


def _signal_vote(action: str) -> float:
    a = str(action).lower().strip()
    if a == "buy":
        return 1.0
    if a == "sell":
        return -1.0
    return 0.0


def aggregate_overlay_score(
    signals: Iterable[Dict[str, Any]],
    *,
    min_confidence: float = 0.0,
) -> Dict[str, Any]:
    used = 0
    score = 0.0
    weight_sum = 0.0
    for s in signals or []:
        c = float(s.get("confidence") or 0.0)
        if c < float(min_confidence):
            continue
        v = _signal_vote(str(s.get("action") or ""))
        if v == 0.0:
            continue
        w = max(0.0, c)
        score += v * w
        weight_sum += w
        used += 1
    norm = (score / weight_sum) if weight_sum > 0 else 0.0
    if norm > 0:
        action = "buy"
    elif norm < 0:
        action = "sell"
    else:
        action = "hold"
    return {"ok": True, "action": action, "score": float(norm), "used": used, "weight_sum": float(weight_sum)}


def apply_signal_overlay(
    base_decision: Dict[str, Any],
    signals: Iterable[Dict[str, Any]],
    *,
    min_confidence: float = 0.3,
    min_abs_score_to_override: float = 0.35,
) -> Dict[str, Any]:
    base = dict(base_decision or {})
    agg = aggregate_overlay_score(signals, min_confidence=min_confidence)
    overlay_action = str(agg.get("action") or "hold")
    overlay_score = float(agg.get("score") or 0.0)
    base_action = str(base.get("action") or "hold").lower().strip()

    override = overlay_action in {"buy", "sell"} and abs(overlay_score) >= float(min_abs_score_to_override)
    final_action = overlay_action if override else base_action
    return {
        "ok": True,
        "base_action": base_action,
        "overlay_action": overlay_action,
        "overlay_score": float(overlay_score),
        "override": bool(override),
        "action": final_action,
        "used": int(agg.get("used") or 0),
    }

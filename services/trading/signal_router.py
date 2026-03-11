from __future__ import annotations

from typing import Any, Dict

from services.signals.routing import route_signal_to_paper_intent


def route_signal(signal: Dict[str, Any], *, mode: str = "paper") -> Dict[str, Any]:
    m = str(mode or "paper").lower().strip()
    if m != "paper":
        return {"ok": False, "reason": "unsupported_mode", "mode": m}
    return route_signal_to_paper_intent(dict(signal or {}))


def route_batch(signals: list[Dict[str, Any]], *, mode: str = "paper") -> Dict[str, Any]:
    out: list[Dict[str, Any]] = []
    accepted = 0
    rejected = 0
    for sig in signals or []:
        r = route_signal(sig, mode=mode)
        out.append(r)
        if r.get("ok"):
            accepted += 1
        else:
            rejected += 1
    return {"ok": True, "mode": str(mode), "count": len(out), "accepted": accepted, "rejected": rejected, "results": out}

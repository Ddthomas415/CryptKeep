from __future__ import annotations

from typing import Any, Dict, Iterable


def summarize_overlay_impact(
    baseline: Iterable[Dict[str, Any]],
    overlay: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    base = list(baseline or [])
    over = list(overlay or [])
    base_pnl = sum(float(r.get("pnl", 0.0) or 0.0) for r in base)
    over_pnl = sum(float(r.get("pnl", 0.0) or 0.0) for r in over)
    base_trades = len(base)
    over_trades = len(over)
    delta = over_pnl - base_pnl
    return {
        "ok": True,
        "baseline_pnl": float(base_pnl),
        "overlay_pnl": float(over_pnl),
        "delta_pnl": float(delta),
        "baseline_trades": base_trades,
        "overlay_trades": over_trades,
        "trade_delta": int(over_trades - base_trades),
    }

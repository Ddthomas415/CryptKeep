from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def build_risk_limits(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = dict(cfg or {})
    rcfg = dict(cfg.get("risk") or {})

    return {
        "max_concurrent_positions": _safe_int(rcfg.get("max_concurrent_positions", 5), 5),
        "max_symbol_exposure_pct": _safe_float(rcfg.get("max_symbol_exposure_pct", 20.0), 20.0),
        "max_total_exposure_pct": _safe_float(rcfg.get("max_total_exposure_pct", 80.0), 80.0),
        "max_strategy_exposure_pct": _safe_float(rcfg.get("max_strategy_exposure_pct", 50.0), 50.0),
        "max_open_intents_per_symbol": _safe_int(rcfg.get("max_open_intents_per_symbol", 1), 1),
    }


def summarize_exposure(
    *,
    positions: list[dict[str, Any]] | None,
    strategy_name: str | None = None,
) -> dict[str, Any]:
    rows = list(positions or [])

    open_positions = [p for p in rows if abs(_safe_float(p.get("qty"), 0.0)) > 0]
    concurrent = len(open_positions)

    total_exposure_pct = 0.0
    strategy_exposure_pct = 0.0
    per_symbol_pct: dict[str, float] = {}

    for p in open_positions:
        symbol = str(p.get("symbol") or "").strip()
        exposure_pct = _safe_float(
            p.get("exposure_pct"),
            _safe_float(p.get("notional_pct"), 0.0),
        )
        total_exposure_pct += exposure_pct
        if symbol:
            per_symbol_pct[symbol] = per_symbol_pct.get(symbol, 0.0) + exposure_pct
        if strategy_name and str(p.get("strategy") or "").strip() == str(strategy_name):
            strategy_exposure_pct += exposure_pct

    return {
        "concurrent_positions": concurrent,
        "total_exposure_pct": round(total_exposure_pct, 4),
        "strategy_exposure_pct": round(strategy_exposure_pct, 4),
        "per_symbol_pct": {k: round(v, 4) for k, v in per_symbol_pct.items()},
    }


def evaluate_entry(
    *,
    symbol: str,
    strategy_name: str,
    limits: dict[str, Any],
    exposure: dict[str, Any],
    open_intents_for_symbol: int = 0,
) -> dict[str, Any]:
    concurrent = _safe_int(exposure.get("concurrent_positions", 0), 0)
    total_exposure_pct = _safe_float(exposure.get("total_exposure_pct", 0.0), 0.0)
    strategy_exposure_pct = _safe_float(exposure.get("strategy_exposure_pct", 0.0), 0.0)
    per_symbol_pct = dict(exposure.get("per_symbol_pct") or {})
    symbol_exposure_pct = _safe_float(per_symbol_pct.get(symbol), 0.0)

    if concurrent >= _safe_int(limits.get("max_concurrent_positions", 5), 5):
        return {"ok": False, "reason": "risk:max_concurrent_positions"}

    if symbol_exposure_pct >= _safe_float(limits.get("max_symbol_exposure_pct", 20.0), 20.0):
        return {"ok": False, "reason": "risk:max_symbol_exposure_pct"}

    if total_exposure_pct >= _safe_float(limits.get("max_total_exposure_pct", 80.0), 80.0):
        return {"ok": False, "reason": "risk:max_total_exposure_pct"}

    if strategy_exposure_pct >= _safe_float(limits.get("max_strategy_exposure_pct", 50.0), 50.0):
        return {"ok": False, "reason": "risk:max_strategy_exposure_pct"}

    if open_intents_for_symbol >= _safe_int(limits.get("max_open_intents_per_symbol", 1), 1):
        return {"ok": False, "reason": "risk:max_open_intents_per_symbol"}

    return {"ok": True, "reason": "risk:pass"}

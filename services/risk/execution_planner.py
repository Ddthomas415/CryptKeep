from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _norm_symbol(v: Any) -> str:
    return str(v or "").strip().upper()


def summarize_current_allocations(
    *,
    positions: list[dict[str, Any]] | None = None,
) -> dict[str, float]:
    rows = list(positions or [])
    out: dict[str, float] = {}
    for row in rows:
        sym = _norm_symbol(row.get("symbol"))
        if not sym:
            continue
        alloc = _safe_float(
            row.get("exposure_pct"),
            _safe_float(row.get("notional_pct"), 0.0),
        )
        out[sym] = out.get(sym, 0.0) + alloc
    return {k: round(v, 4) for k, v in out.items()}


def build_execution_plan(
    *,
    target_rows: list[dict[str, Any]],
    current_allocations: dict[str, float] | None = None,
    min_rebalance_delta_pct: float = 1.0,
    price_map: dict[str, float] | None = None,
    portfolio_value: float = 10000.0,
) -> dict[str, Any]:
    current_allocations = dict(current_allocations or {})
    price_map = {str(k).strip().upper(): dict(v) for k, v in dict(price_map or {}).items()}
    portfolio_value = _safe_float(portfolio_value, 10000.0)
    targets = []
    target_symbols = set()

    for row in list(target_rows or []):
        sym = _norm_symbol(row.get("symbol"))
        if not sym:
            continue
        target_symbols.add(sym)
        target_alloc = _safe_float(row.get("target_alloc_pct"), 0.0)
        current_alloc = _safe_float(current_allocations.get(sym), 0.0)
        delta = target_alloc - current_alloc

        action = "hold"
        if delta >= min_rebalance_delta_pct:
            action = "buy"
        elif delta <= -min_rebalance_delta_pct:
            action = "sell"

        price_info = dict(price_map.get(sym) or {})
        ref_price = _safe_float(price_info.get("price"), 0.0)
        ref_venue = str(price_info.get("venue") or "")
        ref_source = str(price_info.get("price_source") or "")
        ref_ts = str(price_info.get("price_ts") or "")
        est_notional_delta = (abs(delta) / 100.0) * portfolio_value
        est_qty_delta = (est_notional_delta / ref_price) if ref_price > 0 else 0.0

        targets.append({
            **row,
            "symbol": sym,
            "current_alloc_pct": round(current_alloc, 4),
            "delta_alloc_pct": round(delta, 4),
            "action": action,
            "priority": round(abs(delta), 4),
            "reference_price": round(ref_price, 8) if ref_price > 0 else 0.0,
            "reference_price_venue": ref_venue,
            "reference_price_source": ref_source,
            "reference_price_ts": ref_ts,
            "est_notional_delta": round(est_notional_delta, 4),
            "est_qty_delta": round(est_qty_delta, 8),
        })

    # anything currently allocated but not in target set becomes a sell-down candidate
    for sym, current_alloc in current_allocations.items():
        if sym not in target_symbols and _safe_float(current_alloc, 0.0) > 0:
            price_info = dict(price_map.get(sym) or {})
            ref_price = _safe_float(price_info.get("price"), 0.0)
            ref_venue = str(price_info.get("venue") or "")
            ref_source = str(price_info.get("price_source") or "")
            ref_ts = str(price_info.get("price_ts") or "")
            est_notional_delta = (_safe_float(current_alloc, 0.0) / 100.0) * portfolio_value
            est_qty_delta = (est_notional_delta / ref_price) if ref_price > 0 else 0.0

            targets.append({
                "symbol": sym,
                "target_alloc_pct": 0.0,
                "current_alloc_pct": round(_safe_float(current_alloc, 0.0), 4),
                "delta_alloc_pct": round(-_safe_float(current_alloc, 0.0), 4),
                "action": "sell",
                "priority": round(abs(_safe_float(current_alloc, 0.0)), 4),
                "reason": "not_in_target_set",
                "reference_price": round(ref_price, 8) if ref_price > 0 else 0.0,
                "reference_price_venue": ref_venue,
                "reference_price_source": ref_source,
                "reference_price_ts": ref_ts,
                "est_notional_delta": round(est_notional_delta, 4),
                "est_qty_delta": round(est_qty_delta, 8),
            })

    targets.sort(key=lambda r: _safe_float(r.get("priority"), 0.0), reverse=True)

    return {
        "ok": True,
        "rows": targets,
        "buys": [r for r in targets if r.get("action") == "buy"],
        "sells": [r for r in targets if r.get("action") == "sell"],
        "holds": [r for r in targets if r.get("action") == "hold"],
    }

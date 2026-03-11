from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return float(default)
        return float(v)
    except Exception:
        return float(default)


def compute_unrealized(positions: Iterable[Dict[str, Any]], prices: Dict[str, float]) -> Tuple[float, list[Dict[str, Any]]]:
    total = 0.0
    details: list[dict[str, Any]] = []
    pmap = {str(k): _safe_float(v) for k, v in (prices or {}).items()}
    for row in positions or []:
        sym = str(row.get("symbol") or "")
        qty = _safe_float(row.get("qty"))
        avg = _safe_float(row.get("avg_price"))
        px = pmap.get(sym)
        if px is None:
            details.append({"symbol": sym, "qty": qty, "avg_price": avg, "mark_price": None, "unrealized_pnl": 0.0, "priced": False})
            continue
        pnl = (float(px) - avg) * qty
        total += pnl
        details.append({"symbol": sym, "qty": qty, "avg_price": avg, "mark_price": float(px), "unrealized_pnl": float(pnl), "priced": True})
    return float(total), details


def compute_mtm_equity(
    *,
    cash_quote: float,
    positions: Iterable[Dict[str, Any]],
    prices: Dict[str, float],
    realized_pnl: float = 0.0,
) -> Dict[str, Any]:
    cash = _safe_float(cash_quote)
    realized = _safe_float(realized_pnl)
    unrealized, details = compute_unrealized(positions, prices)
    market_value = 0.0
    for d in details:
        if d["priced"] and d["mark_price"] is not None:
            market_value += float(d["mark_price"]) * float(d["qty"])
    equity = cash + market_value
    return {
        "ok": True,
        "cash_quote": float(cash),
        "realized_pnl": float(realized),
        "unrealized_pnl": float(unrealized),
        "market_value": float(market_value),
        "equity_quote": float(equity),
        "positions": details,
    }

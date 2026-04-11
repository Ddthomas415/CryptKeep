from __future__ import annotations

import time
from typing import Any

try:
    import ccxt
except Exception:
    ccxt = None

from storage.intent_queue_sqlite import IntentQueueSQLite
from storage.paper_trading_sqlite import PaperTradingSQLite


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _norm_symbol(v: Any) -> str:
    return str(v or "").strip().upper()




def _build_price_map(*, symbols: list[str], venue: str = "coinbase") -> dict[str, float]:
    out: dict[str, float] = {}
    if ccxt is None:
        return out

    ex_cls = getattr(ccxt, venue, None)
    if ex_cls is None:
        return out

    ex = ex_cls({"enableRateLimit": True})
    try:
        for symbol in symbols:
            sym = _norm_symbol(symbol)
            if not sym:
                continue
            try:
                ticker = ex.fetch_ticker(sym)
                px = _safe_float(ticker.get("last"), 0.0)
                if px <= 0:
                    px = _safe_float(ticker.get("bid"), 0.0) or _safe_float(ticker.get("ask"), 0.0)
                if px > 0:
                    out[sym] = px
            except Exception:
                continue
    finally:
        try:
            ex.close()
        except Exception:
            pass

    return out


def _list_open_intents(qdb: Any) -> list[dict[str, Any]]:
    rows = []
    try:
        if hasattr(qdb, "list_intents"):
            rows = list(qdb.list_intents() or [])
        elif hasattr(qdb, "get_all_intents"):
            rows = list(qdb.get_all_intents() or [])
        elif hasattr(qdb, "intents"):
            rows = list(qdb.intents() or [])
    except Exception:
        rows = []

    out = []
    for row in rows:
        status = str(row.get("status") or "").strip().lower()
        if status in {"filled", "cancelled", "rejected", "closed"}:
            continue
        out.append(dict(row))
    return out


def _list_positions(pdb: Any) -> list[dict[str, Any]]:
    rows = []
    try:
        if hasattr(pdb, "list_positions"):
            rows = list(pdb.list_positions() or [])
        elif hasattr(pdb, "get_all_positions"):
            rows = list(pdb.get_all_positions() or [])
        elif hasattr(pdb, "positions"):
            rows = list(pdb.positions() or [])
    except Exception:
        rows = []
    return rows


def _find_position(positions: list[dict[str, Any]], symbol: str) -> dict[str, Any]:
    sym = _norm_symbol(symbol)
    for row in positions:
        if _norm_symbol(row.get("symbol")) == sym:
            return dict(row)
    return {"symbol": sym, "qty": 0.0, "avg_price": 0.0, "exposure_pct": 0.0}


def _upsert_position_best_effort(pdb: Any, row: dict[str, Any]) -> None:
    if hasattr(pdb, "upsert_position"):
        pdb.upsert_position(row)
        return
    if hasattr(pdb, "save_position"):
        pdb.save_position(row)
        return
    if hasattr(pdb, "insert_position"):
        pdb.insert_position(row)
        return
    raise RuntimeError("paper_db_no_position_writer")


def _close_or_fill_intent_best_effort(qdb: Any, row: dict[str, Any], *, status: str, fill_price: float) -> None:
    updated = dict(row)
    updated["status"] = status
    meta = dict(updated.get("meta") or {})
    meta["fill_price"] = round(fill_price, 8)
    meta["filled_ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    updated["meta"] = meta

    if hasattr(qdb, "upsert_intent"):
        qdb.upsert_intent(updated)
        return
    if hasattr(qdb, "update_intent"):
        qdb.update_intent(updated)
        return
    raise RuntimeError("intent_queue_no_update_writer")


def reconcile_execution_plan_intents(
    *,
    fill_price_map: dict[str, float] | None = None,
    default_fill_price: float = 100.0,
    venue: str = "coinbase",
) -> dict[str, Any]:
    qdb = IntentQueueSQLite()
    pdb = PaperTradingSQLite()

    open_intents = _list_open_intents(qdb)
    positions = _list_positions(pdb)
    fill_price_map = dict(fill_price_map or {})

    all_symbols = [_norm_symbol(r.get("symbol")) for r in open_intents if _norm_symbol(r.get("symbol"))]
    live_price_map = _build_price_map(symbols=all_symbols, venue=venue)

    filled: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for row in open_intents:
        source = str(row.get("source") or (row.get("meta") or {}).get("source") or "").strip()
        strategy = str(row.get("strategy") or "").strip()
        if source != "execution_plan" and strategy != "allocation_rebalance":
            skipped.append({**row, "skip_reason": "not_execution_plan_intent"})
            continue

        symbol = _norm_symbol(row.get("symbol"))
        action = str(row.get("action") or "").strip().lower()
        if action not in {"buy", "sell"} or not symbol:
            skipped.append({**row, "skip_reason": "invalid_intent"})
            continue

        fill_price = _safe_float(fill_price_map.get(symbol), 0.0)
        if fill_price <= 0:
            fill_price = _safe_float(live_price_map.get(symbol), 0.0)
        if fill_price <= 0:
            fill_price = default_fill_price
        if fill_price <= 0:
            skipped.append({**row, "skip_reason": "invalid_fill_price"})
            continue

        meta = dict(row.get("meta") or {})
        target_alloc = _safe_float(row.get("target_alloc_pct"), _safe_float(meta.get("target_alloc_pct"), 0.0))
        current_alloc = _safe_float(row.get("current_alloc_pct"), _safe_float(meta.get("current_alloc_pct"), 0.0))
        delta_alloc = _safe_float(row.get("delta_alloc_pct"), _safe_float(meta.get("delta_alloc_pct"), 0.0))

        pos = _find_position(positions, symbol)
        qty = _safe_float(pos.get("qty"), 0.0)
        avg_price = _safe_float(pos.get("avg_price"), 0.0)
        exposure_pct = _safe_float(pos.get("exposure_pct"), _safe_float(pos.get("notional_pct"), 0.0))

        try:
            if action == "buy":
                new_qty = qty + max(delta_alloc, 0.0)
                new_exposure = exposure_pct + max(delta_alloc, 0.0)
                new_avg = fill_price if qty <= 0 else ((avg_price * qty) + (fill_price * max(delta_alloc, 0.0))) / max(new_qty, 1e-9)
            else:
                sell_amt = max(abs(delta_alloc), 0.0)
                new_qty = max(0.0, qty - sell_amt)
                new_exposure = max(0.0, exposure_pct - sell_amt)
                new_avg = avg_price if new_qty > 0 else 0.0

            new_pos = {
                **pos,
                "symbol": symbol,
                "qty": round(new_qty, 8),
                "avg_price": round(new_avg, 8),
                "exposure_pct": round(new_exposure, 4),
                "notional_pct": round(new_exposure, 4),
                "strategy": strategy,
                "last_fill_price": round(fill_price, 8),
                "updated_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            _upsert_position_best_effort(pdb, new_pos)
            _close_or_fill_intent_best_effort(qdb, row, status="filled", fill_price=fill_price)

            filled.append({
                "symbol": symbol,
                "action": action,
                "fill_price": round(fill_price, 8),
                "target_alloc_pct": round(target_alloc, 4),
                "current_alloc_pct": round(current_alloc, 4),
                "delta_alloc_pct": round(delta_alloc, 4),
                "new_exposure_pct": round(new_exposure, 4),
            })
        except Exception as e:
            errors.append({**row, "error": f"{type(e).__name__}:{e}"})

    return {
        "ok": len(errors) == 0,
        "filled": filled,
        "skipped": skipped,
        "errors": errors,
    }

from __future__ import annotations

import time
from typing import Any

try:
    import ccxt
except Exception:
    ccxt = None

from storage.intent_queue_sqlite import IntentQueueSQLite
from storage.paper_trading_sqlite import PaperTradingSQLite
from services.execution.position_math import apply_allocation_fill
from services.execution.outcome_logger import log_strategy_outcome


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
        try:
            pdb.upsert_position(row)
        except TypeError:
            pdb.upsert_position(
                str(row.get("symbol") or ""),
                float(row.get("qty") or 0.0),
                float(row.get("avg_price") or 0.0),
                float(row.get("realized_pnl") or 0.0),
            )
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
        action = str(row.get("action") or row.get("side") or "").strip().lower()
        if action not in {"buy", "sell"} or not symbol:
            skipped.append({**row, "skip_reason": "invalid_intent"})
            continue

        meta = dict(row.get("meta") or {})

        planned_reference_price = _safe_float(meta.get("reference_price"), 0.0)
        planned_reference_price_venue = str(meta.get("reference_price_venue") or "")
        planned_reference_price_source = str(meta.get("reference_price_source") or "")
        planned_reference_price_ts = str(meta.get("reference_price_ts") or "")

        fill_price = _safe_float(fill_price_map.get(symbol), 0.0)
        fill_price_source = "explicit_fill_price_map"
        if fill_price <= 0:
            fill_price = _safe_float(live_price_map.get(symbol), 0.0)
            fill_price_source = "live_market_price"
        if fill_price <= 0:
            fill_price = default_fill_price
            fill_price_source = "default_fill_price"
        if fill_price <= 0:
            skipped.append({**row, "skip_reason": "invalid_fill_price"})
            continue

        fill_vs_plan_pct = 0.0
        if planned_reference_price > 0 and fill_price > 0:
            fill_vs_plan_pct = ((fill_price - planned_reference_price) / planned_reference_price) * 100.0

        target_alloc = _safe_float(row.get("target_alloc_pct"), _safe_float(meta.get("target_alloc_pct"), 0.0))
        current_alloc = _safe_float(row.get("current_alloc_pct"), _safe_float(meta.get("current_alloc_pct"), 0.0))
        delta_alloc = _safe_float(row.get("delta_alloc_pct"), _safe_float(meta.get("delta_alloc_pct"), 0.0))
        est_qty_delta = abs(_safe_float(row.get("est_qty_delta"), _safe_float(meta.get("est_qty_delta"), 0.0)))
        est_notional_delta = abs(_safe_float(row.get("est_notional_delta"), _safe_float(meta.get("est_notional_delta"), 0.0)))

        if est_qty_delta <= 0:
            est_qty_delta = abs(_safe_float(row.get("qty"), 0.0))
        if est_notional_delta <= 0 and est_qty_delta > 0 and fill_price > 0:
            est_notional_delta = est_qty_delta * fill_price

        pos = _find_position(positions, symbol)
        qty = _safe_float(pos.get("qty"), 0.0)
        avg_price = _safe_float(pos.get("avg_price"), 0.0)
        exposure_pct = _safe_float(pos.get("exposure_pct"), _safe_float(pos.get("notional_pct"), 0.0))

        try:
            applied = None
            applied_source = "allocation_fallback"

            if est_qty_delta > 0 and fill_price > 0:
                if action == "buy":
                    new_qty = qty + est_qty_delta
                    new_exposure = exposure_pct + est_notional_delta
                    new_avg = fill_price if qty <= 0 or avg_price <= 0 else ((avg_price * qty) + (fill_price * est_qty_delta)) / max(new_qty, 1e-12)
                    event = "open" if qty <= 0 else "add"
                    signed_qty_delta = est_qty_delta
                else:
                    sell_qty = min(qty, est_qty_delta) if qty > 0 else 0.0
                    new_qty = max(0.0, qty - sell_qty)
                    new_exposure = max(0.0, exposure_pct - est_notional_delta)
                    new_avg = avg_price if new_qty > 1e-12 else 0.0
                    event = "close" if new_qty <= 1e-12 else "reduce"
                    signed_qty_delta = -est_qty_delta

                applied = {
                    "ok": True,
                    "reason": "applied_estimated_qty",
                    "new_qty": round(new_qty, 8),
                    "new_avg_price": round(new_avg, 8),
                    "new_exposure_pct": round(new_exposure, 4),
                    "qty_delta": round(signed_qty_delta, 8),
                    "position_event": event,
                }
                applied_source = "estimated_qty"

            elif est_notional_delta > 0 and fill_price > 0:
                synthetic_delta_alloc = est_notional_delta
                applied = apply_allocation_fill(
                    action=action,
                    fill_price=fill_price,
                    delta_alloc_pct=synthetic_delta_alloc,
                    current_qty=qty,
                    current_avg_price=avg_price,
                    current_exposure_pct=exposure_pct,
                )
                applied_source = "estimated_notional"

            else:
                applied = apply_allocation_fill(
                    action=action,
                    fill_price=fill_price,
                    delta_alloc_pct=delta_alloc,
                    current_qty=qty,
                    current_avg_price=avg_price,
                    current_exposure_pct=exposure_pct,
                )
                applied_source = "allocation_fallback"

            if not bool(applied.get("ok")):
                raise RuntimeError(str(applied.get("reason") or "apply_fill_failed"))

            new_pos = {
                **pos,
                "symbol": symbol,
                "qty": float(applied["new_qty"]),
                "avg_price": float(applied["new_avg_price"]),
                "exposure_pct": float(applied["new_exposure_pct"]),
                "notional_pct": float(applied["new_exposure_pct"]),
                "strategy": strategy,
                "last_fill_price": round(fill_price, 8),
                "updated_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            _upsert_position_best_effort(pdb, new_pos)
            _close_or_fill_intent_best_effort(qdb, row, status="filled", fill_price=fill_price)

            filled_row = {
                "symbol": symbol,
                "action": action,
                "planned_reference_price": round(planned_reference_price, 8) if planned_reference_price > 0 else 0.0,
                "planned_reference_price_venue": planned_reference_price_venue,
                "planned_reference_price_source": planned_reference_price_source,
                "planned_reference_price_ts": planned_reference_price_ts,
                "actual_fill_price": round(fill_price, 8),
                "fill_price_source": fill_price_source,
                "fill_vs_plan_pct": round(fill_vs_plan_pct, 4),
                "target_alloc_pct": round(target_alloc, 4),
                "current_alloc_pct": round(current_alloc, 4),
                "delta_alloc_pct": round(delta_alloc, 4),
                "est_notional_delta": round(est_notional_delta, 4),
                "est_qty_delta": round(est_qty_delta, 8),
                "applied_source": applied_source,
                "old_exposure_pct": round(exposure_pct, 4),
                "new_exposure_pct": float(applied["new_exposure_pct"]),
                "old_qty": round(qty, 8),
                "new_qty": float(applied["new_qty"]),
                "qty_delta": float(applied["qty_delta"]),
                "position_event": applied.get("position_event"),
            }

            outcome_meta = {
                "selected_strategy": meta.get("selected_strategy"),
                "selected_strategy_reason": meta.get("selected_strategy_reason"),
                "regime": meta.get("regime"),
                "volume_surge": meta.get("volume_surge"),
                "volume_ratio": meta.get("volume_ratio"),
                "signal_reason": meta.get("signal_reason"),
                "intent_strategy_id": row.get("strategy"),
                "venue": row.get("venue"),
                **filled_row,
            }

            log_strategy_outcome(outcome_meta)
            filled.append(filled_row)

        except Exception as e:
            errors.append({**row, "error": f"{type(e).__name__}:{e}"})

    return {
        "ok": len(errors) == 0,
        "filled": filled,
        "skipped": skipped,
        "errors": errors,
    }

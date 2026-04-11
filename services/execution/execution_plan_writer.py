from __future__ import annotations

import time
from typing import Any

from storage.intent_queue_sqlite import IntentQueueSQLite


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _norm_symbol(v: Any) -> str:
    return str(v or "").strip().upper()


def plan_rows_to_intents(
    *,
    plan_rows: list[dict[str, Any]],
    strategy_name: str = "allocation_rebalance",
    venue: str = "coinbase",
    min_delta_pct: float = 1.0,
) -> list[dict[str, Any]]:
    intents: list[dict[str, Any]] = []

    for row in list(plan_rows or []):
        action = str(row.get("action") or "").strip().lower()
        if action not in {"buy", "sell"}:
            continue

        symbol = _norm_symbol(row.get("symbol"))
        if not symbol:
            continue

        delta = abs(_safe_float(row.get("delta_alloc_pct"), 0.0))
        if delta < min_delta_pct:
            continue

        intents.append({
            "venue": venue,
            "symbol": symbol,
            "action": action,
            "strategy": strategy_name,
            "target_alloc_pct": round(_safe_float(row.get("target_alloc_pct"), 0.0), 4),
            "current_alloc_pct": round(_safe_float(row.get("current_alloc_pct"), 0.0), 4),
            "delta_alloc_pct": round(_safe_float(row.get("delta_alloc_pct"), 0.0), 4),
            "priority": round(_safe_float(row.get("priority"), delta), 4),
            "reference_price": round(_safe_float(row.get("reference_price"), 0.0), 8),
            "reference_price_venue": str(row.get("reference_price_venue") or ""),
            "reference_price_source": str(row.get("reference_price_source") or ""),
            "reference_price_ts": str(row.get("reference_price_ts") or ""),
            "est_notional_delta": round(_safe_float(row.get("est_notional_delta"), 0.0), 4),
            "est_qty_delta": round(_safe_float(row.get("est_qty_delta"), 0.0), 8),
            "source": "execution_plan",
            "status": "queued",
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

    intents.sort(key=lambda r: _safe_float(r.get("priority"), 0.0), reverse=True)
    return intents


def queue_execution_intents(
    *,
    plan_rows: list[dict[str, Any]],
    strategy_name: str = "allocation_rebalance",
    venue: str = "coinbase",
    min_delta_pct: float = 1.0,
) -> dict[str, Any]:
    qdb = IntentQueueSQLite()
    intents = plan_rows_to_intents(
        plan_rows=plan_rows,
        strategy_name=strategy_name,
        venue=venue,
        min_delta_pct=min_delta_pct,
    )

    queued: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    existing_rows = []
    try:
        if hasattr(qdb, "list_intents"):
            existing_rows = list(qdb.list_intents() or [])
        elif hasattr(qdb, "get_all_intents"):
            existing_rows = list(qdb.get_all_intents() or [])
        elif hasattr(qdb, "intents"):
            existing_rows = list(qdb.intents() or [])
    except Exception:
        existing_rows = []

    existing_open = {
        (
            str(r.get("venue") or "").strip().lower(),
            _norm_symbol(r.get("symbol")),
            str(r.get("action") or "").strip().lower(),
        )
        for r in existing_rows
        if str(r.get("status") or "").strip().lower() not in {"filled", "cancelled", "rejected", "closed"}
    }

    for row in intents:
        key = (
            str(row.get("venue") or "").strip().lower(),
            _norm_symbol(row.get("symbol")),
            str(row.get("action") or "").strip().lower(),
        )
        if key in existing_open:
            skipped.append({**row, "skip_reason": "duplicate_open_intent"})
            continue

        try:
            payload = {
                "venue": row["venue"],
                "symbol": row["symbol"],
                "action": row["action"],
                "strategy": row["strategy"],
                "status": row["status"],
                "meta": {
                    "target_alloc_pct": row["target_alloc_pct"],
                    "current_alloc_pct": row["current_alloc_pct"],
                    "delta_alloc_pct": row["delta_alloc_pct"],
                    "priority": row["priority"],
                    "reference_price": row["reference_price"],
                    "reference_price_venue": row["reference_price_venue"],
                    "reference_price_source": row["reference_price_source"],
                    "reference_price_ts": row["reference_price_ts"],
                    "est_notional_delta": row["est_notional_delta"],
                    "est_qty_delta": row["est_qty_delta"],
                    "source": row["source"],
                    "ts": row["ts"],
                },
            }

            if hasattr(qdb, "upsert_intent"):
                qdb.upsert_intent(payload)
            elif hasattr(qdb, "insert_intent"):
                qdb.insert_intent(payload)
            else:
                raise RuntimeError("intent_queue_no_writer")

            queued.append(row)
            existing_open.add(key)
        except Exception as e:
            errors.append({**row, "error": f"{type(e).__name__}:{e}"})

    return {
        "ok": len(errors) == 0,
        "queued": queued,
        "skipped": skipped,
        "errors": errors,
    }

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AggregationConfig:
    mode: str = "median"
    stale_seconds: int = 10
    primary_exchange_by_symbol: dict[str, str] | None = None


def _row_price(row: dict[str, Any]) -> float | None:
    bid = row.get("bid")
    ask = row.get("ask")
    if bid is not None and ask is not None:
        try:
            return (float(bid) + float(ask)) / 2.0
        except Exception:
            return None
    last = row.get("last")
    try:
        return None if last is None else float(last)
    except Exception:
        return None


def aggregate_prices(rows: list[dict[str, Any]], cfg: AggregationConfig) -> tuple[dict[str, float], dict[str, Any]]:
    now_ms = time.time() * 1000.0
    stale_ms = max(0.0, float(cfg.stale_seconds or 0) * 1000.0)
    grouped: dict[str, list[dict[str, Any]]] = {}
    detail: dict[str, Any] = {"sources": {}}

    for row in rows or []:
        symbol = str(row.get("symbol") or "").strip()
        if not symbol:
            continue
        ts_ms = row.get("ts_ms")
        try:
            ts_val = float(ts_ms) if ts_ms is not None else None
        except Exception:
            ts_val = None
        if ts_val is not None and stale_ms > 0 and (now_ms - ts_val) > stale_ms:
            continue
        px = _row_price(row)
        if px is None:
            continue
        grouped.setdefault(symbol, []).append({**row, "_agg_price": px})

    prices: dict[str, float] = {}
    for symbol, items in grouped.items():
        preferred_venue = ((cfg.primary_exchange_by_symbol or {}).get(symbol) or "").strip().lower()
        chosen = None
        if preferred_venue:
            for item in items:
                if str(item.get("venue") or "").strip().lower() == preferred_venue:
                    chosen = item
                    break
        if chosen is None:
            values = [float(item["_agg_price"]) for item in items]
            mode = str(cfg.mode or "median").strip().lower()
            if mode == "mean":
                px = sum(values) / float(len(values))
            else:
                px = float(statistics.median(values))
            prices[symbol] = px
            detail["sources"][symbol] = {
                "mode": mode,
                "count": len(values),
                "venues": sorted({str(item.get("venue") or "") for item in items}),
            }
            continue
        prices[symbol] = float(chosen["_agg_price"])
        detail["sources"][symbol] = {
            "mode": "primary",
            "count": len(items),
            "venue": str(chosen.get("venue") or ""),
        }
    return prices, detail

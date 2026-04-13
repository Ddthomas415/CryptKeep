from __future__ import annotations

from typing import Any

from services.signals.market_ranker import rank_market
from services.signals.trade_type_classifier import classify_trade_type
from services.signals.candidate_strategy_mapper import map_candidate_to_strategy


def build_candidate_list(
    *,
    symbols_data: list[dict[str, Any]],
    min_composite_score: float = 40.0,
) -> list[dict[str, Any]]:
    ranked = rank_market(symbols_data=symbols_data)
    out: list[dict[str, Any]] = []

    for row in ranked:
        trade_type = classify_trade_type(scores=row.get("scores") or {})
        if trade_type.get("trade_type") == "pass":
            continue
        if float(row.get("composite_score") or 0.0) < float(min_composite_score):
            continue

        mapped = map_candidate_to_strategy({
            **row,
            "trade_type": trade_type.get("trade_type"),
            "trade_type_reason": trade_type.get("reason"),
        })

        out.append({
            "symbol": row.get("symbol"),
            "composite_score": row.get("composite_score"),
            "trade_type": trade_type.get("trade_type"),
            "trade_type_reason": trade_type.get("reason"),
            "preferred_strategy": mapped.get("preferred_strategy"),
            "mapping_reason": mapped.get("reason"),
            "scores": row.get("scores") or {},
            "symbol_return_pct": row.get("symbol_return_pct"),
        })

    return out

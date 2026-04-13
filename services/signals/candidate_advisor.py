from __future__ import annotations

from typing import Any

from services.signals.candidate_store import load_latest_candidates


def get_top_candidate(*, min_score: float = 40.0) -> dict[str, Any] | None:
    rows = load_latest_candidates()
    if not rows:
        return None

    usable = []
    for row in rows:
        score = float(row.get("composite_score") or 0.0)
        trade_type = str(row.get("trade_type") or "pass")
        preferred_strategy = row.get("preferred_strategy")

        if score < min_score:
            continue
        if trade_type == "pass":
            continue
        if not preferred_strategy:
            continue

        usable.append(row)

    if not usable:
        return None

    usable.sort(key=lambda r: float(r.get("composite_score") or 0.0), reverse=True)
    top = usable[0]

    return {
        "symbol": top.get("symbol"),
        "composite_score": top.get("composite_score"),
        "trade_type": top.get("trade_type"),
        "preferred_strategy": top.get("preferred_strategy"),
        "mapping_reason": top.get("mapping_reason"),
        "trade_type_reason": top.get("trade_type_reason"),
        "scores": top.get("scores") or {},
    }

from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _norm_symbol(v: Any) -> str:
    return str(v or "").strip().upper()


def summarize_paper_state(
    *,
    positions: list[dict[str, Any]] | None = None,
    intents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    positions = list(positions or [])
    intents = list(intents or [])

    open_positions = [p for p in positions if abs(_safe_float(p.get("qty"), 0.0)) > 0]
    open_intents = [i for i in intents if str(i.get("status") or "").lower() not in {"filled", "cancelled", "rejected", "closed"}]

    symbols_with_positions = sorted({_norm_symbol(p.get("symbol")) for p in open_positions if _norm_symbol(p.get("symbol"))})
    symbols_with_intents = sorted({_norm_symbol(i.get("symbol")) for i in open_intents if _norm_symbol(i.get("symbol"))})

    strategies_with_positions = sorted({str(p.get("strategy") or "").strip() for p in open_positions if str(p.get("strategy") or "").strip()})
    strategies_with_intents = sorted({str(i.get("strategy") or "").strip() for i in open_intents if str(i.get("strategy") or "").strip()})

    per_symbol_positions: dict[str, int] = {}
    per_symbol_open_intents: dict[str, int] = {}

    for p in open_positions:
        sym = _norm_symbol(p.get("symbol"))
        if sym:
            per_symbol_positions[sym] = per_symbol_positions.get(sym, 0) + 1

    for i in open_intents:
        sym = _norm_symbol(i.get("symbol"))
        if sym:
            per_symbol_open_intents[sym] = per_symbol_open_intents.get(sym, 0) + 1

    return {
        "open_positions": len(open_positions),
        "open_intents": len(open_intents),
        "symbols_with_positions": symbols_with_positions,
        "symbols_with_intents": symbols_with_intents,
        "strategies_with_positions": strategies_with_positions,
        "strategies_with_intents": strategies_with_intents,
        "per_symbol_positions": per_symbol_positions,
        "per_symbol_open_intents": per_symbol_open_intents,
    }


def validate_multi_symbol_state(
    *,
    positions: list[dict[str, Any]] | None = None,
    intents: list[dict[str, Any]] | None = None,
    max_open_intents_per_symbol: int = 1,
) -> dict[str, Any]:
    summary = summarize_paper_state(positions=positions, intents=intents)

    issues: list[str] = []

    for sym, count in dict(summary.get("per_symbol_positions") or {}).items():
        if count > 1:
            issues.append(f"duplicate_open_positions:{sym}:{count}")

    for sym, count in dict(summary.get("per_symbol_open_intents") or {}).items():
        if count > int(max_open_intents_per_symbol):
            issues.append(f"too_many_open_intents:{sym}:{count}>{max_open_intents_per_symbol}")

    pos_syms = set(summary.get("symbols_with_positions") or [])
    intent_syms = set(summary.get("symbols_with_intents") or [])
    if len(pos_syms | intent_syms) > 1:
        multi_symbol_active = True
    else:
        multi_symbol_active = False

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "multi_symbol_active": multi_symbol_active,
        "summary": summary,
    }


def collect_runtime_rows(
    *,
    paper_db: Any,
    intent_db: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    positions: list[dict[str, Any]] = []
    intents: list[dict[str, Any]] = []

    try:
        if hasattr(paper_db, "list_positions"):
            positions = list(paper_db.list_positions() or [])
        elif hasattr(paper_db, "get_all_positions"):
            positions = list(paper_db.get_all_positions() or [])
        elif hasattr(paper_db, "positions"):
            positions = list(paper_db.positions() or [])
    except Exception:
        positions = []

    try:
        if hasattr(intent_db, "list_intents"):
            intents = list(intent_db.list_intents() or [])
        elif hasattr(intent_db, "get_all_intents"):
            intents = list(intent_db.get_all_intents() or [])
        elif hasattr(intent_db, "intents"):
            intents = list(intent_db.intents() or [])
    except Exception:
        intents = []

    return positions, intents

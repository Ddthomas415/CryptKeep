from __future__ import annotations

from typing import Any

from dashboard.services.symbol_scanner import run_symbol_scan
from services.market_data.correlation_inputs import load_series_by_symbol
from services.market_data.correlation_matrix import build_correlation_matrix, diversify_ranked_symbols


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def build_rotation_candidates(
    *,
    venue: str = "coinbase",
    top_n: int = 10,
    min_hot_score: float = 20.0,
    min_change_pct: float = 2.0,
    min_volume_24h: float = 100000.0,
    diversify: bool = True,
    max_abs_corr: float = 0.85,
) -> dict[str, Any]:
    scan = run_symbol_scan(venue=venue, symbols=[])
    if not scan.get("ok"):
        return {
            "ok": False,
            "reason": "scan_failed",
            "rows": [],
            "selected": [],
        }

    rows = list(scan.get("hot") or [])
    filtered: list[dict[str, Any]] = []
    for row in rows:
        hot_score = _safe_float(row.get("hot_score"), 0.0)
        change_pct = _safe_float(row.get("change_pct"), 0.0)
        volume_24h = _safe_float(row.get("volume_24h"), 0.0)
        if hot_score < min_hot_score:
            continue
        if change_pct < min_change_pct:
            continue
        if volume_24h < min_volume_24h:
            continue
        filtered.append(dict(row))

    filtered.sort(
        key=lambda r: (
            _safe_float(r.get("hot_score"), 0.0),
            _safe_float(r.get("change_pct"), 0.0),
            _safe_float(r.get("volume_24h"), 0.0),
        ),
        reverse=True,
    )

    ranked_symbols = [str(r.get("symbol") or "").strip() for r in filtered if str(r.get("symbol") or "").strip()]
    corr = {"ok": True, "matrix": {}, "most_positive": [], "most_negative": []}

    if diversify and ranked_symbols:
        series_by_symbol = load_series_by_symbol(
            venue=venue,
            symbols=ranked_symbols[:top_n],
            timeframe="1h",
            limit=120,
        )
        corr = build_correlation_matrix(series_by_symbol=series_by_symbol)
        selected = diversify_ranked_symbols(
            ranked_symbols=ranked_symbols,
            matrix=(corr.get("matrix") or {}),
            max_abs_corr=max_abs_corr,
            top_n=top_n,
        )
    else:
        selected = ranked_symbols[:top_n]

    selected_set = set(selected)
    selected_rows = [r for r in filtered if str(r.get("symbol") or "").strip() in selected_set]

    return {
        "ok": True,
        "source": scan.get("source"),
        "market_regime": scan.get("market_regime"),
        "rows": filtered[:top_n],
        "selected_rows": selected_rows,
        "selected": selected,
        "correlation": corr,
        "diversified": bool(diversify),
        "scanned": scan.get("scanned", 0),
        "ts": scan.get("ts"),
    }

from __future__ import annotations

from typing import Any

from dashboard.services.symbol_scanner import run_symbol_scan


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

    selected = [str(r.get("symbol") or "") for r in filtered[:top_n] if str(r.get("symbol") or "").strip()]

    return {
        "ok": True,
        "source": scan.get("source"),
        "market_regime": scan.get("market_regime"),
        "rows": filtered[:top_n],
        "selected": selected,
        "scanned": scan.get("scanned", 0),
        "ts": scan.get("ts"),
    }

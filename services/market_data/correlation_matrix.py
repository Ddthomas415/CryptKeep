from __future__ import annotations

import math
from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except Exception:
        return default


def _returns_from_ohlcv(ohlcv: list[list[Any]]) -> list[float]:
    closes = [_safe_float(r[4]) for r in (ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 5]
    if len(closes) < 2:
        return []
    out: list[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        cur = closes[i]
        if prev > 0 and cur > 0:
            out.append((cur - prev) / prev)
    return out


def _pearson(x: list[float], y: list[float]) -> float:
    n = min(len(x), len(y))
    if n < 3:
        return 0.0
    x = x[-n:]
    y = y[-n:]
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den_x = math.sqrt(sum((a - mx) ** 2 for a in x))
    den_y = math.sqrt(sum((b - my) ** 2 for b in y))
    den = den_x * den_y
    if den <= 1e-12:
        return 0.0
    return max(-1.0, min(1.0, num / den))


def build_correlation_matrix(
    *,
    series_by_symbol: dict[str, list[list[Any]]],
) -> dict[str, Any]:
    symbols = [str(s).strip() for s in series_by_symbol.keys() if str(s).strip()]
    returns = {sym: _returns_from_ohlcv(series_by_symbol.get(sym) or []) for sym in symbols}

    matrix: dict[str, dict[str, float]] = {}
    pairs: list[dict[str, Any]] = []

    for a in symbols:
        matrix[a] = {}
        for b in symbols:
            corr = 1.0 if a == b else _pearson(returns.get(a, []), returns.get(b, []))
            matrix[a][b] = round(corr, 4)
            if a < b:
                pairs.append({"a": a, "b": b, "corr": round(corr, 4)})

    most_positive = sorted(pairs, key=lambda r: r["corr"], reverse=True)[:10]
    most_negative = sorted(pairs, key=lambda r: r["corr"])[:10]

    return {
        "ok": True,
        "symbols": symbols,
        "matrix": matrix,
        "most_positive": most_positive,
        "most_negative": most_negative,
    }


def diversify_ranked_symbols(
    *,
    ranked_symbols: list[str],
    matrix: dict[str, dict[str, float]],
    max_abs_corr: float = 0.85,
    top_n: int = 10,
) -> list[str]:
    selected: list[str] = []
    for sym in ranked_symbols:
        sym = str(sym).strip()
        if not sym:
            continue
        if not selected:
            selected.append(sym)
            if len(selected) >= top_n:
                break
            continue
        too_correlated = False
        for chosen in selected:
            corr = abs(float((matrix.get(sym) or {}).get(chosen, 0.0)))
            if corr >= max_abs_corr:
                too_correlated = True
                break
        if not too_correlated:
            selected.append(sym)
        if len(selected) >= top_n:
            break
    return selected

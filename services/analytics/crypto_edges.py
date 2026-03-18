from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _s(value: Any) -> str:
    return str(value or "").strip()


def summarize_funding_carry(
    rows: Iterable[Dict[str, Any]],
    *,
    interval_hours: float = 8.0,
) -> Dict[str, Any]:
    items = [dict(row or {}) for row in list(rows or [])]
    interval = max(float(interval_hours), 1e-9)
    cleaned: List[Dict[str, Any]] = []
    rates: List[float] = []

    for row in items:
        rate = _fnum(row.get("funding_rate"), 0.0)
        rates.append(rate)
        cleaned.append(
            {
                "symbol": _s(row.get("symbol")),
                "venue": _s(row.get("venue")),
                "funding_rate": float(rate),
                "side_bias": "long_pays" if rate > 0 else ("short_pays" if rate < 0 else "flat"),
            }
        )

    if not cleaned:
        return {
            "ok": True,
            "rows": [],
            "count": 0,
            "avg_funding_rate": 0.0,
            "last_funding_rate": 0.0,
            "annualized_carry_pct": 0.0,
            "positive_ratio": 0.0,
            "negative_ratio": 0.0,
            "dominant_bias": "flat",
        }

    avg_rate = sum(rates) / len(rates)
    last_rate = rates[-1]
    annualized = avg_rate * (24.0 / interval) * 365.0 * 100.0
    positive_ratio = sum(1 for rate in rates if rate > 0) / len(rates)
    negative_ratio = sum(1 for rate in rates if rate < 0) / len(rates)
    dominant_bias = "long_pays" if positive_ratio > negative_ratio else ("short_pays" if negative_ratio > positive_ratio else "flat")

    return {
        "ok": True,
        "rows": cleaned,
        "count": int(len(cleaned)),
        "avg_funding_rate": float(avg_rate),
        "last_funding_rate": float(last_rate),
        "annualized_carry_pct": float(annualized),
        "positive_ratio": float(positive_ratio),
        "negative_ratio": float(negative_ratio),
        "dominant_bias": dominant_bias,
    }


def summarize_basis_spread(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    items = [dict(row or {}) for row in list(rows or [])]
    cleaned: List[Dict[str, Any]] = []
    basis_bps_values: List[float] = []

    for row in items:
        spot_px = _fnum(row.get("spot_px"), 0.0)
        perp_px = _fnum(row.get("perp_px"), 0.0)
        if spot_px <= 0.0 or perp_px <= 0.0:
            continue
        basis_bps = ((perp_px - spot_px) / spot_px) * 10000.0
        days_to_expiry = row.get("days_to_expiry")
        annualized_basis_pct = None
        if days_to_expiry is not None and _fnum(days_to_expiry, 0.0) > 0.0:
            annualized_basis_pct = ((perp_px - spot_px) / spot_px) * (365.0 / _fnum(days_to_expiry)) * 100.0
        cleaned.append(
            {
                "symbol": _s(row.get("symbol")),
                "venue": _s(row.get("venue")),
                "spot_px": float(spot_px),
                "perp_px": float(perp_px),
                "basis_bps": float(basis_bps),
                "annualized_basis_pct": float(annualized_basis_pct) if annualized_basis_pct is not None else None,
                "basis_state": "premium" if basis_bps > 0 else ("discount" if basis_bps < 0 else "flat"),
            }
        )
        basis_bps_values.append(basis_bps)

    if not cleaned:
        return {
            "ok": True,
            "rows": [],
            "count": 0,
            "avg_basis_bps": 0.0,
            "widest_basis_bps": 0.0,
            "premium_ratio": 0.0,
            "discount_ratio": 0.0,
        }

    avg_basis_bps = sum(basis_bps_values) / len(basis_bps_values)
    widest_basis_bps = max(basis_bps_values, key=lambda value: abs(value))
    premium_ratio = sum(1 for value in basis_bps_values if value > 0) / len(basis_bps_values)
    discount_ratio = sum(1 for value in basis_bps_values if value < 0) / len(basis_bps_values)

    return {
        "ok": True,
        "rows": cleaned,
        "count": int(len(cleaned)),
        "avg_basis_bps": float(avg_basis_bps),
        "widest_basis_bps": float(widest_basis_bps),
        "premium_ratio": float(premium_ratio),
        "discount_ratio": float(discount_ratio),
    }


def summarize_cross_venue_dislocations(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    items = [dict(row or {}) for row in list(rows or [])]
    by_symbol: Dict[str, List[Dict[str, Any]]] = {}
    for row in items:
        symbol = _s(row.get("symbol"))
        if not symbol:
            continue
        by_symbol.setdefault(symbol, []).append(row)

    dislocations: List[Dict[str, Any]] = []
    for symbol, quotes in by_symbol.items():
        best_bid_row = None
        best_ask_row = None
        best_bid = None
        best_ask = None

        for row in quotes:
            bid = row.get("bid")
            ask = row.get("ask")
            if bid is not None:
                bid_v = _fnum(bid, 0.0)
                if bid_v > 0.0 and (best_bid is None or bid_v > best_bid):
                    best_bid = bid_v
                    best_bid_row = row
            if ask is not None:
                ask_v = _fnum(ask, 0.0)
                if ask_v > 0.0 and (best_ask is None or ask_v < best_ask):
                    best_ask = ask_v
                    best_ask_row = row

        if best_bid is None or best_ask is None or best_ask <= 0.0:
            continue

        gross_cross_bps = ((best_bid - best_ask) / best_ask) * 10000.0
        entry = {
            "symbol": symbol,
            "best_bid_venue": _s((best_bid_row or {}).get("venue")),
            "best_ask_venue": _s((best_ask_row or {}).get("venue")),
            "best_bid": float(best_bid),
            "best_ask": float(best_ask),
            "gross_cross_bps": float(gross_cross_bps),
            "dislocated": bool(gross_cross_bps > 0.0),
        }
        dislocations.append(entry)

    dislocations.sort(key=lambda row: row["gross_cross_bps"], reverse=True)
    positive = [row for row in dislocations if row["gross_cross_bps"] > 0.0]

    return {
        "ok": True,
        "rows": dislocations,
        "count": int(len(dislocations)),
        "positive_count": int(len(positive)),
        "top_dislocation": positive[0] if positive else None,
    }


def build_crypto_edge_report(
    *,
    funding_rows: Iterable[Dict[str, Any]] | None = None,
    basis_rows: Iterable[Dict[str, Any]] | None = None,
    quote_rows: Iterable[Dict[str, Any]] | None = None,
    funding_interval_hours: float = 8.0,
) -> Dict[str, Any]:
    funding = summarize_funding_carry(funding_rows or [], interval_hours=float(funding_interval_hours))
    basis = summarize_basis_spread(basis_rows or [])
    dislocations = summarize_cross_venue_dislocations(quote_rows or [])
    return {
        "ok": True,
        "funding": funding,
        "basis": basis,
        "dislocations": dislocations,
        "research_only": True,
        "execution_enabled": False,
    }

from __future__ import annotations

from collections import defaultdict
from typing import Any

from services.market_data.symbol_router import map_symbol, normalize_venue
from services.security.exchange_factory import make_exchange


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _truthy_quote(value: Any) -> float | None:
    try:
        parsed = float(value)
    except Exception:
        return None
    return parsed if parsed > 0.0 else None


def _close_exchange(ex: Any) -> None:
    try:
        if ex is not None and hasattr(ex, "close"):
            ex.close()
    except Exception:
        pass


def _open_public_exchange(venue: str) -> Any:
    ex = make_exchange(str(venue), {"apiKey": None, "secret": None}, enable_rate_limit=True)
    if hasattr(ex, "load_markets"):
        ex.load_markets()
    return ex


def _mid_from_ticker(ticker: dict[str, Any]) -> float | None:
    bid = _truthy_quote((ticker or {}).get("bid"))
    ask = _truthy_quote((ticker or {}).get("ask"))
    last = _truthy_quote((ticker or {}).get("last")) or _truthy_quote((ticker or {}).get("close"))
    if bid is not None and ask is not None:
        return (bid + ask) / 2.0
    return last


def _extract_funding_rate(payload: dict[str, Any]) -> float | None:
    candidates = [
        payload.get("fundingRate"),
        payload.get("funding_rate"),
        payload.get("nextFundingRate"),
        payload.get("next_funding_rate"),
        ((payload.get("info") or {}) if isinstance(payload.get("info"), dict) else {}).get("fundingRate"),
        ((payload.get("info") or {}) if isinstance(payload.get("info"), dict) else {}).get("funding_rate"),
    ]
    for candidate in candidates:
        try:
            return float(candidate)
        except Exception:
            continue
    return None


def _collect_funding_rows(plan_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    by_venue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in plan_rows:
        by_venue[normalize_venue(str(item.get("venue") or ""))].append(dict(item or {}))

    for venue, items in by_venue.items():
        ex = None
        try:
            ex = _open_public_exchange(venue)
        except Exception as exc:
            for item in items:
                checks.append(
                    {
                        "kind": "funding",
                        "venue": venue,
                        "symbol": str(item.get("symbol") or ""),
                        "ok": False,
                        "reason": f"exchange_open_failed:{type(exc).__name__}",
                    }
                )
            continue

        try:
            fetcher = getattr(ex, "fetch_funding_rate", None)
            if not callable(fetcher):
                for item in items:
                    checks.append(
                        {
                            "kind": "funding",
                            "venue": venue,
                            "symbol": str(item.get("symbol") or ""),
                            "ok": False,
                            "reason": "funding_unsupported",
                        }
                    )
                continue

            for item in items:
                symbol = str(item.get("symbol") or "").strip()
                native = map_symbol(venue, symbol)
                try:
                    payload = dict(fetcher(native) or {})
                    rate = _extract_funding_rate(payload)
                    if rate is None:
                        checks.append(
                            {
                                "kind": "funding",
                                "venue": venue,
                                "symbol": symbol,
                                "ok": False,
                                "reason": "funding_rate_missing",
                            }
                        )
                        continue
                    rows.append(
                        {
                            "symbol": symbol,
                            "venue": venue,
                            "funding_rate": float(rate),
                            "interval_hours": float(item.get("interval_hours") or 8.0),
                        }
                    )
                    checks.append({"kind": "funding", "venue": venue, "symbol": symbol, "ok": True})
                except Exception as exc:
                    checks.append(
                        {
                            "kind": "funding",
                            "venue": venue,
                            "symbol": symbol,
                            "ok": False,
                            "reason": f"funding_fetch_failed:{type(exc).__name__}",
                        }
                    )
        finally:
            _close_exchange(ex)

    return rows, checks


def _collect_basis_rows(plan_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    by_venue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in plan_rows:
        by_venue[normalize_venue(str(item.get("venue") or ""))].append(dict(item or {}))

    for venue, items in by_venue.items():
        ex = None
        try:
            ex = _open_public_exchange(venue)
        except Exception as exc:
            for item in items:
                checks.append(
                    {
                        "kind": "basis",
                        "venue": venue,
                        "spot_symbol": str(item.get("spot_symbol") or ""),
                        "perp_symbol": str(item.get("perp_symbol") or ""),
                        "ok": False,
                        "reason": f"exchange_open_failed:{type(exc).__name__}",
                    }
                )
            continue

        try:
            for item in items:
                spot_symbol = str(item.get("spot_symbol") or "").strip()
                perp_symbol = str(item.get("perp_symbol") or "").strip()
                try:
                    spot_ticker = dict(ex.fetch_ticker(map_symbol(venue, spot_symbol)) or {})
                    perp_ticker = dict(ex.fetch_ticker(map_symbol(venue, perp_symbol)) or {})
                    spot_px = _mid_from_ticker(spot_ticker)
                    perp_px = _mid_from_ticker(perp_ticker)
                    if spot_px is None or perp_px is None:
                        checks.append(
                            {
                                "kind": "basis",
                                "venue": venue,
                                "spot_symbol": spot_symbol,
                                "perp_symbol": perp_symbol,
                                "ok": False,
                                "reason": "price_missing",
                            }
                        )
                        continue
                    rows.append(
                        {
                            "symbol": perp_symbol,
                            "venue": venue,
                            "spot_px": float(spot_px),
                            "perp_px": float(perp_px),
                            "days_to_expiry": item.get("days_to_expiry"),
                        }
                    )
                    checks.append(
                        {
                            "kind": "basis",
                            "venue": venue,
                            "spot_symbol": spot_symbol,
                            "perp_symbol": perp_symbol,
                            "ok": True,
                        }
                    )
                except Exception as exc:
                    checks.append(
                        {
                            "kind": "basis",
                            "venue": venue,
                            "spot_symbol": spot_symbol,
                            "perp_symbol": perp_symbol,
                            "ok": False,
                            "reason": f"basis_fetch_failed:{type(exc).__name__}",
                        }
                    )
        finally:
            _close_exchange(ex)

    return rows, checks


def _best_bid_ask_from_orderbook(orderbook: dict[str, Any]) -> tuple[float | None, float | None]:
    bids = list((orderbook or {}).get("bids") or [])
    asks = list((orderbook or {}).get("asks") or [])
    best_bid = _truthy_quote(bids[0][0]) if bids else None
    best_ask = _truthy_quote(asks[0][0]) if asks else None
    return best_bid, best_ask


def _collect_quote_rows(plan_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    by_venue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in plan_rows:
        by_venue[normalize_venue(str(item.get("venue") or ""))].append(dict(item or {}))

    for venue, items in by_venue.items():
        ex = None
        try:
            ex = _open_public_exchange(venue)
        except Exception as exc:
            for item in items:
                checks.append(
                    {
                        "kind": "quotes",
                        "venue": venue,
                        "symbol": str(item.get("symbol") or ""),
                        "ok": False,
                        "reason": f"exchange_open_failed:{type(exc).__name__}",
                    }
                )
            continue

        try:
            for item in items:
                symbol = str(item.get("symbol") or "").strip()
                native = map_symbol(venue, symbol)
                try:
                    bid = ask = None
                    fetch_order_book = getattr(ex, "fetch_order_book", None)
                    if callable(fetch_order_book):
                        orderbook = dict(fetch_order_book(native, limit=int(item.get("orderbook_limit") or 5)) or {})
                        bid, ask = _best_bid_ask_from_orderbook(orderbook)
                    if bid is None or ask is None:
                        ticker = dict(ex.fetch_ticker(native) or {})
                        bid = bid or _truthy_quote(ticker.get("bid"))
                        ask = ask or _truthy_quote(ticker.get("ask"))
                    if bid is None or ask is None:
                        checks.append(
                            {
                                "kind": "quotes",
                                "venue": venue,
                                "symbol": symbol,
                                "ok": False,
                                "reason": "quote_missing",
                            }
                        )
                        continue
                    rows.append({"symbol": symbol, "venue": venue, "bid": float(bid), "ask": float(ask)})
                    checks.append({"kind": "quotes", "venue": venue, "symbol": symbol, "ok": True})
                except Exception as exc:
                    checks.append(
                        {
                            "kind": "quotes",
                            "venue": venue,
                            "symbol": symbol,
                            "ok": False,
                            "reason": f"quote_fetch_failed:{type(exc).__name__}",
                        }
                    )
        finally:
            _close_exchange(ex)

    return rows, checks


def collect_live_crypto_edge_snapshot(plan: dict[str, Any]) -> dict[str, Any]:
    funding_plan = [dict(item or {}) for item in list((plan or {}).get("funding") or [])]
    basis_plan = [dict(item or {}) for item in list((plan or {}).get("basis") or [])]
    quotes_plan = [dict(item or {}) for item in list((plan or {}).get("quotes") or [])]

    funding_rows, funding_checks = _collect_funding_rows(funding_plan)
    basis_rows, basis_checks = _collect_basis_rows(basis_plan)
    quote_rows, quote_checks = _collect_quote_rows(quotes_plan)

    return {
        "ok": True,
        "research_only": True,
        "execution_enabled": False,
        "funding_rows": funding_rows,
        "basis_rows": basis_rows,
        "quote_rows": quote_rows,
        "checks": funding_checks + basis_checks + quote_checks,
    }

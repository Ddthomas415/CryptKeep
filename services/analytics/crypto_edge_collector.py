from __future__ import annotations

from collections import defaultdict
from typing import Any

from services.market_data.symbol_router import map_symbol, normalize_venue
from services.security.binance_guard import require_binance_allowed


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
    except Exception as _err:
        pass  # suppressed: crypto_edge_collector.py


def _open_public_exchange(venue: str) -> Any:
    venue_id = normalize_venue(str(venue))
    if venue_id.startswith("binance"):
        require_binance_allowed(venue_id)

    import ccxt  # type: ignore

    klass = getattr(ccxt, venue_id)
    cfg: dict[str, Any] = {
        "enableRateLimit": True,
        "apiKey": None,
        "secret": None,
    }
    if venue_id.startswith("binance"):
        cfg["options"] = {"adjustForTimeDifference": True}
    ex = klass(cfg)
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
        except Exception as _err:
            continue
    return None


def _extract_open_interest(payload: dict[str, Any]) -> float | None:
    candidates = [
        payload.get("openInterest"),
        payload.get("open_interest"),
        payload.get("openInterestAmount"),
        ((payload.get("info") or {}) if isinstance(payload.get("info"), dict) else {}).get("openInterest"),
        ((payload.get("info") or {}) if isinstance(payload.get("info"), dict) else {}).get("open_interest"),
    ]
    for candidate in candidates:
        try:
            return float(candidate)
        except Exception as _err:
            continue
    return None


def _sum_notional(levels: list[Any], depth: int) -> float:
    total = 0.0
    for level in list(levels or [])[:depth]:
        if not isinstance(level, (list, tuple)) or len(level) < 2:
            continue
        px = _truthy_quote(level[0])
        qty = _truthy_quote(level[1])
        if px is not None and qty is not None:
            total += px * qty
    return total


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


def _collect_open_interest_rows(plan_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
                        "kind": "open_interest",
                        "venue": venue,
                        "symbol": str(item.get("symbol") or ""),
                        "ok": False,
                        "reason": f"exchange_open_failed:{type(exc).__name__}",
                    }
                )
            continue

        try:
            fetcher = getattr(ex, "fetch_open_interest", None)
            if not callable(fetcher):
                for item in items:
                    checks.append(
                        {
                            "kind": "open_interest",
                            "venue": venue,
                            "symbol": str(item.get("symbol") or ""),
                            "ok": False,
                            "reason": "open_interest_unsupported",
                        }
                    )
                continue

            for item in items:
                symbol = str(item.get("symbol") or "").strip()
                native = map_symbol(venue, symbol)
                try:
                    payload = dict(fetcher(native) or {})
                    open_interest = _extract_open_interest(payload)
                    if open_interest is None:
                        checks.append(
                            {
                                "kind": "open_interest",
                                "venue": venue,
                                "symbol": symbol,
                                "ok": False,
                                "reason": "open_interest_missing",
                            }
                        )
                        continue
                    price_change_pct = None
                    try:
                        ticker = dict(ex.fetch_ticker(native) or {})
                        if ticker.get("percentage") is not None:
                            price_change_pct = float(ticker.get("percentage"))
                    except Exception as _err:
                        price_change_pct = None
                    rows.append(
                        {
                            "symbol": symbol,
                            "venue": venue,
                            "open_interest": float(open_interest),
                            "price_change_pct": price_change_pct,
                        }
                    )
                    checks.append({"kind": "open_interest", "venue": venue, "symbol": symbol, "ok": True})
                except Exception as exc:
                    checks.append(
                        {
                            "kind": "open_interest",
                            "venue": venue,
                            "symbol": symbol,
                            "ok": False,
                            "reason": f"open_interest_fetch_failed:{type(exc).__name__}",
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


def _collect_order_book_rows(plan_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
                        "kind": "order_books",
                        "venue": venue,
                        "symbol": str(item.get("symbol") or ""),
                        "ok": False,
                        "reason": f"exchange_open_failed:{type(exc).__name__}",
                    }
                )
            continue

        try:
            fetcher = getattr(ex, "fetch_order_book", None)
            if not callable(fetcher):
                for item in items:
                    checks.append(
                        {
                            "kind": "order_books",
                            "venue": venue,
                            "symbol": str(item.get("symbol") or ""),
                            "ok": False,
                            "reason": "order_book_unsupported",
                        }
                    )
                continue

            for item in items:
                symbol = str(item.get("symbol") or "").strip()
                native = map_symbol(venue, symbol)
                depth = max(int(item.get("depth") or item.get("orderbook_limit") or 10), 1)
                try:
                    orderbook = dict(fetcher(native, limit=max(depth, 10)) or {})
                    bids = list(orderbook.get("bids") or [])
                    asks = list(orderbook.get("asks") or [])
                    best_bid, best_ask = _best_bid_ask_from_orderbook(orderbook)
                    if best_bid is None or best_ask is None:
                        checks.append(
                            {
                                "kind": "order_books",
                                "venue": venue,
                                "symbol": symbol,
                                "ok": False,
                                "reason": "best_bid_ask_missing",
                            }
                        )
                        continue
                    if best_ask < best_bid:
                        checks.append(
                            {
                                "kind": "order_books",
                                "venue": venue,
                                "symbol": symbol,
                                "ok": False,
                                "reason": "crossed_order_book",
                            }
                        )
                        continue
                    bid_notional = _sum_notional(bids, depth)
                    ask_notional = _sum_notional(asks, depth)
                    total_notional = bid_notional + ask_notional
                    if total_notional <= 0.0:
                        checks.append(
                            {
                                "kind": "order_books",
                                "venue": venue,
                                "symbol": symbol,
                                "ok": False,
                                "reason": "depth_notional_missing",
                            }
                        )
                        continue
                    spread_bps = ((best_ask - best_bid) / best_bid) * 10000.0
                    rows.append(
                        {
                            "symbol": symbol,
                            "venue": venue,
                            "depth": int(depth),
                            "best_bid": float(best_bid),
                            "best_ask": float(best_ask),
                            "spread_bps": float(spread_bps),
                            "bid_notional": float(bid_notional),
                            "ask_notional": float(ask_notional),
                            "imbalance": float((bid_notional - ask_notional) / total_notional),
                        }
                    )
                    checks.append({"kind": "order_books", "venue": venue, "symbol": symbol, "ok": True})
                except Exception as exc:
                    checks.append(
                        {
                            "kind": "order_books",
                            "venue": venue,
                            "symbol": symbol,
                            "ok": False,
                            "reason": f"order_book_fetch_failed:{type(exc).__name__}",
                        }
                    )
        finally:
            _close_exchange(ex)

    return rows, checks


def collect_live_crypto_edge_snapshot(plan: dict[str, Any]) -> dict[str, Any]:
    funding_plan = [dict(item or {}) for item in list((plan or {}).get("funding") or [])]
    basis_plan = [dict(item or {}) for item in list((plan or {}).get("basis") or [])]
    quotes_plan = [dict(item or {}) for item in list((plan or {}).get("quotes") or [])]
    open_interest_plan = [dict(item or {}) for item in list((plan or {}).get("open_interest") or [])]
    order_book_plan = [dict(item or {}) for item in list((plan or {}).get("order_books") or [])]

    funding_rows, funding_checks = _collect_funding_rows(funding_plan)
    open_interest_rows, open_interest_checks = _collect_open_interest_rows(open_interest_plan)
    basis_rows, basis_checks = _collect_basis_rows(basis_plan)
    quote_rows, quote_checks = _collect_quote_rows(quotes_plan)
    order_book_rows, order_book_checks = _collect_order_book_rows(order_book_plan)

    return {
        "ok": True,
        "research_only": True,
        "execution_enabled": False,
        "funding_rows": funding_rows,
        "open_interest_rows": open_interest_rows,
        "basis_rows": basis_rows,
        "quote_rows": quote_rows,
        "order_book_rows": order_book_rows,
        "checks": funding_checks + open_interest_checks + basis_checks + quote_checks + order_book_checks,
    }

"""Operator-accepted CMC quote qualification (2026-10-09); diagnostic, never scoring authorization.

Policy: docs/research/cmc_trending_log/quote_qualification_proposal_20261009.md (POLICY_ACCEPTED).
  provenance: accepted collector hash, exact product, valid ticker response hash, identity eligible
  freshness: ticker and book request round trip <= 5 s; |book receipt - book server time| <= 10 s
  liquidity flag (report only): last trade older than 60 min at ticker receipt
  size: displayed best ask (entry) / best bid (exit) covers the 100 USD entry quantity (100 / ticker entry ask, fees
        excluded; the exit keeps the entry quantity)
Alignment (60 s coin/BTC pairing) is separate and is not evidence of freshness or size.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from scripts.research.cmc_book_evidence import inspect_book, positive

POLICY = {"max_round_trip_seconds": 5.0, "max_book_age_seconds": 10.0,
          "illiquid_last_trade_seconds": 3600.0, "entry_notional_usd": Decimal("100"),
          "source": "quote_qualification_proposal_20261009.md POLICY_ACCEPTED"}
ACCEPTED_COLLECTORS = {
    "108d9da4159d3b2003da289c39c569cbd822901fa95f5d62ac48899488470f3c",  # v3 before level-1 edit
    "e97f93fa109cc5f2f32d27a6cec875492b27b9722eba0579382463965d91344a",  # v3 with optional level-1
}


def _time(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    text = value.replace("Z", "+00:00")
    head, sep, tail = text.partition(".")
    if sep:  # trim sub-microsecond digits (Coinbase sends nanoseconds)
        n = len(tail) - len(tail.lstrip("0123456789"))  # leading fractional digits only
        tail = tail[:min(n, 6)].ljust(6, "0") + tail[n:]  # Python 3.10 needs exactly 6 digits
        text = head + "." + tail
    parsed = datetime.fromisoformat(text)
    if parsed.utcoffset() is None:
        raise ValueError("naive timestamp")
    return parsed.astimezone(timezone.utc)


def _hash_ok(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def qualify_capture(snapshot, product, ticker, side, quantity=None, identity_eligible=None):
    """Qualify one coin capture. side is 'buy' (entry) or 'sell' (exit).

    Returns status QUALIFIED or EXCLUDED with every failing reason, plus report-only flags and the
    entry quantity used (computed from the registered ticker ask for buys).
    """
    if side not in ("buy", "sell"):
        raise ValueError("side must be buy or sell")
    reasons, flags, evidence = [], [], {"product_id": product, "side": side}
    if snapshot.get("collector_sha256") not in ACCEPTED_COLLECTORS:
        reasons.append("EXCLUDED_PROVENANCE_COLLECTOR")
    if identity_eligible is not True:
        reasons.append("EXCLUDED_PROVENANCE_IDENTITY")
    try:
        if ticker.get("error") or not _hash_ok(ticker.get("response_sha256")):
            raise ValueError("ticker error or missing response hash")
        t_start, t_recv = _time(ticker["request_started_utc"]), _time(ticker["received_utc"])
        trip = (t_recv - t_start).total_seconds()
        evidence["ticker_round_trip_seconds"] = trip
        if trip < 0 or trip > POLICY["max_round_trip_seconds"]:
            reasons.append("STALE_CAPTURE")
        try:
            last_trade_age = (t_recv - _time(ticker["payload"]["time"])).total_seconds()
            evidence["last_trade_age_seconds"] = last_trade_age
            if last_trade_age > POLICY["illiquid_last_trade_seconds"]:
                flags.append("ILLIQUID_FLAG")
        except (KeyError, TypeError, ValueError):
            flags.append("LAST_TRADE_TIME_UNKNOWN")
    except (KeyError, TypeError, ValueError, AttributeError):
        reasons.append("EXCLUDED_PROVENANCE_TICKER")
    books = snapshot.get("coinbase_level1_books")
    record = books.get(product) if isinstance(books, dict) else None
    if record is None:
        reasons.append("SIZE_UNVERIFIED_NO_BOOK")
        return {"status": "EXCLUDED", "reasons": reasons, "flags": flags, "quantity": None,
                "evidence": evidence, "scoring_authorized": False}
    book = inspect_book(record, product)
    if book["status"] == "UNQUALIFIED_AUCTION_STATE":
        reasons.append("UNQUALIFIED_AUCTION_STATE")
    elif book["status"] != "STRUCTURALLY_VALID":
        reasons.append("INVALID_BOOK")
    else:
        response = record["response"]
        b_start, b_recv = _time(response["request_started_utc"]), _time(response["received_utc"])
        b_trip = (b_recv - b_start).total_seconds()
        evidence["book_round_trip_seconds"] = b_trip
        if b_trip > POLICY["max_round_trip_seconds"]:
            reasons.append("STALE_CAPTURE_BOOK")
        try:
            age = (b_recv - _time(response["payload"]["time"])).total_seconds()
            evidence["book_age_seconds"] = age  # negative values = local clock behind exchange
            if abs(age) > POLICY["max_book_age_seconds"]:
                reasons.append("STALE_BOOK")
        except (KeyError, TypeError, ValueError):
            reasons.append("BOOK_TIME_UNVERIFIED")
        if quantity is None and side == "buy":
            try:
                # Capacity must cover the position valued by the unchanged registered outcome.
                quantity = POLICY["entry_notional_usd"] / positive(ticker["payload"]["ask"])
            except (KeyError, TypeError, ValueError, InvalidOperation):
                reasons.append("INVALID_ENTRY_ASK")
        if quantity is None:
            reasons.append("SIZE_UNVERIFIED_NO_QUANTITY")
        else:
            try:
                quantity = positive(quantity)
            except (TypeError, ValueError, InvalidOperation):
                reasons.append("INVALID_QUANTITY")
                quantity = None
            else:
                shown = Decimal(book["ask_base_size"] if side == "buy" else book["bid_base_size"])
                evidence.update(required_base_quantity=str(quantity), displayed_base_size=str(shown))
                if quantity > shown:
                    reasons.append("INSUFFICIENT_DISPLAYED_SIZE")
    return {"status": "EXCLUDED" if reasons else "QUALIFIED", "reasons": reasons, "flags": flags,
            "quantity": None if quantity is None else str(quantity), "evidence": evidence,
            "execution": "NOT_FILL_PROOF", "scoring_authorized": False}


def all_ranges_above_zero(statistics):
    """Operator gate rule (statistical_gate_decision_20261009.md) as a descriptive condition only."""
    if statistics.get("status") != "DIAGNOSTIC":
        return "NOT_EVALUABLE"
    sensitivities = statistics.get("serial_dependence_sensitivities_not_replacement_gate")
    if not isinstance(sensitivities, dict) or set(sensitivities) != {"7", "14", "28"}:
        return False
    intervals = [statistics.get("registered_entry_day_bootstrap"),
                 *(sensitivities[key] for key in ("7", "14", "28"))]
    for item in intervals:
        if not isinstance(item, dict) or item.get("status") != "DESCRIPTIVE":
            return False
        try:
            lower, upper = positive(item["p05"]), positive(item["p95"])
        except (KeyError, TypeError, ValueError, InvalidOperation):
            return False
        if upper < lower:
            return False
    return True

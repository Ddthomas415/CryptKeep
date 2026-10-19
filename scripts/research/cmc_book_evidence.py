"""Structural L1 capture qualification; no automatic scoring or fill claim."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import quote


def positive(value):
    if isinstance(value, bool):
        raise ValueError("boolean price or size")
    result = Decimal(str(value))
    if not result.is_finite() or result <= 0:
        raise ValueError("nonpositive or nonfinite price or size")
    return result


def aware(value):
    time = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if time.utcoffset() is None:
        raise ValueError("naive capture timestamp")
    return time.astimezone(timezone.utc)


def best_level(side):
    if not isinstance(side, list) or not side:
        raise ValueError("book side must be a nonempty array")
    row = side[0]
    if not isinstance(row, list) or len(row) < 2:
        raise ValueError("book level must be a price/size array")
    return tuple(map(positive, row[:2]))


def inspect_book(record, expected_product, required_base_quantity=None):
    try:
        expected_url = "https://api.exchange.coinbase.com/products/"+quote(expected_product, safe="")+"/book?level=1"
        if record["product_id"] != expected_product or record["request_url"] != expected_url:
            raise ValueError("product/request provenance mismatch")
        response = record["response"]
        if response.get("error"):
            raise ValueError("book capture error")
        digest = response["response_sha256"]
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("missing valid response hash")
        started, received = [aware(response[key]) for key in ("request_started_utc", "received_utc")]
        if received < started:
            raise ValueError("receipt precedes request")
        payload = response["payload"]
        if payload.get("auction_mode") is not False:
            return {"status": "UNQUALIFIED_AUCTION_STATE", "scoring_authorized": False}
        bid, bid_size = best_level(payload["bids"])
        ask, ask_size = best_level(payload["asks"])
        if bid > ask:
            raise ValueError("crossed book")
        quantity = positive(required_base_quantity) if required_base_quantity is not None else None
    except (KeyError, IndexError, TypeError, ValueError, AttributeError, InvalidOperation) as exc:
        return {"status": "INVALID", "reason": str(exc), "scoring_authorized": False}
    return {"status": "STRUCTURALLY_VALID", "product_id": expected_product,
            "bid": str(bid), "ask": str(ask), "bid_base_size": str(bid_size),
            "ask_base_size": str(ask_size), "capture_seconds": (received-started).total_seconds(),
            "displayed_size_covers_buy": None if quantity is None else quantity <= ask_size,
            "displayed_size_covers_sell": None if quantity is None else quantity <= bid_size,
            "response_hash_status": "RECORDED_NOT_RECOMPUTED",
            "freshness": "UNVERIFIED", "execution": "NOT_FILL_PROOF",
            "scoring_authorized": False}


def notional_sensitivity(record, expected_product, quote_notional="100"):
    """Displayed entry capacity only; quote notional excludes separate fees."""
    evidence = inspect_book(record, expected_product)
    if evidence["status"] != "STRUCTURALLY_VALID":
        return evidence
    notional = positive(quote_notional)
    quantity = notional/Decimal(evidence["ask"])
    evidence = inspect_book(record, expected_product, quantity)
    evidence.update(quote_notional_excluding_fees=str(notional),
                    hypothetical_base_quantity=str(quantity),
                    scope="entry_snapshot_only_not_round_trip_or_fill")
    return evidence


def timing_evidence(record, as_of):
    """Report transport timing, never infer exchange quote age from receipt."""
    base = {"exchange_quote_age_seconds": None, "freshness": "UNVERIFIED",
            "scoring_authorized": False, "execution": "NOT_FILL_PROOF"}
    try:
        if as_of.utcoffset() is None:
            raise ValueError("aware report time required")
        response = record["response"]
        started, received = [aware(response[key]) for key in
                             ("request_started_utc", "received_utc")]
        now = as_of.astimezone(timezone.utc)
        if received < started:
            raise ValueError("receipt precedes request")
        if received > now:
            raise ValueError("receipt after report time")
        if response.get("error"):
            raise ValueError("capture error")
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        return {**base, "timing_status": "INVALID", "reason": str(exc)}
    return {**base, "timing_status": "TRANSPORT_TIMING_ONLY",
            "request_duration_seconds": (received-started).total_seconds(),
            "receipt_age_at_report_seconds": (now-received).total_seconds(),
            "primary_qualification": "NOT_ESTABLISHED"}

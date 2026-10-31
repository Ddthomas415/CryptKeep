"""Pure receipt-preserving Coinbase candle adapter; no HTTP, files or scoring."""
from collections import Counter
import hashlib
import json
import math
from urllib.parse import parse_qs, quote, urlsplit

from services.backtest import descriptive_metadata as metadata
from services.backtest import shared_cash_research as ledger


HOUR = 3_600_000


def _hourly_receipt(capture):
    try:
        url = urlsplit(capture.get("url", ""))
        return (capture.get("method") == "GET" and url.scheme == "https"
                and url.hostname == "api.exchange.coinbase.com" and url.port in (None, 443)
                and url.username is None and url.password is None and not url.fragment
                and url.path == "/products/" + quote(capture["product_id"], safe="-") + "/candles"
                and parse_qs(url.query, keep_blank_values=True).get("granularity") == ["3600"])
    except (TypeError, ValueError):
        return False


def _bad_constant(value):
    raise ValueError("nonfinite_json_constant")


def _row(raw):
    if (not isinstance(raw, list) or len(raw) != 6 or type(raw[0]) is not int
            or raw[0] < 0 or raw[0] % 3600):
        raise ValueError("invalid_candle_timestamp_or_shape")
    try:
        valid = all(type(v) in (int, float) and math.isfinite(v) for v in raw[1:])
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("invalid_candle_numeric")
    _, low, high, opening, close, volume = raw
    if min(low, high, opening, close) <= 0 or low > min(opening, close) or high < max(opening, close) or low > high or volume < 0:
        raise ValueError("invalid_candle_range")
    return [raw[0]*1000, opening, high, low, close, volume]


def map_candle_captures(captures, *, identities, start_ms, end_ms, as_of_ms):
    """Use only supplied completed observations received by as_of_ms.

    captures: [{product_id, method, url, received_at_ms, http_status, response_bytes}].
    identities use the accepted metadata mapping contract. A supplied identity
    reference/hash is not independently authenticated. Conflicting completed
    versions make that hour unknown; no revision is selected to rescue it.
    """
    start, end, cutoff = (ledger.timestamp(t) for t in (start_ms, end_ms, as_of_ms))
    if (start % HOUR or end % HOUR or end <= start or end > cutoff
            or not isinstance(captures, (list, tuple)) or not isinstance(identities, dict)
            or not identities or any(not isinstance(s, str) or not s for s in identities)):
        raise ValueError("explicit_completed_window_and_identities_required")
    products = {symbol: record["product_id"] for symbol, record in identities.items() if metadata._identity(record)}
    if len(set(products.values())) != len(products):
        raise ValueError("duplicate_product_assignment")
    by_product = {product: symbol for symbol, product in products.items()}
    versions = {s: {} for s in identities}
    errors = {s: [] if s in products else ["unresolved_identity_evidence"] for s in identities}
    evidence, ignored = [], Counter()
    for capture in captures:
        if not isinstance(capture, dict):
            raise ValueError("capture_receipt_required")
        received = ledger.timestamp(capture.get("received_at_ms"))
        if received > cutoff:
            ignored["future_capture"] += 1
            continue
        if (capture.get("product_id") not in by_product
                or not isinstance(capture.get("response_bytes"), bytes)):
            raise ValueError("declared_product_and_raw_response_required")
        if not _hourly_receipt(capture):
            raise ValueError("hourly_public_get_receipt_required")
        symbol, body = by_product[capture["product_id"]], capture["response_bytes"]
        digest = hashlib.sha256(body).hexdigest()
        item = {"symbol": symbol, "product_id": capture["product_id"], "received_at_ms": received,
                "method": capture["method"], "url": capture["url"],
                "http_status": capture.get("http_status"), "source_sha256": digest, "status": "INCOMPLETE"}
        evidence.append(item)
        try:
            if type(capture.get("http_status")) is not int or capture["http_status"] != 200:
                raise ValueError("http_not_200")
            rows = json.loads(body, parse_constant=_bad_constant)
            if not isinstance(rows, list) or len(rows) > 300:
                raise ValueError("invalid_candle_response_shape")
            decoded = [_row(raw) for raw in rows]
            if len({r[0] for r in decoded}) != len(decoded):
                raise ValueError("duplicate_candle_timestamp")
        except (ValueError, UnicodeError) as error:
            reason = str(error) if str(error) in (
                "http_not_200", "invalid_candle_response_shape", "duplicate_candle_timestamp",
                "invalid_candle_timestamp_or_shape", "invalid_candle_numeric",
                "invalid_candle_range", "nonfinite_json_constant") else "unreadable_candle_response"
            item["reason"] = reason
            errors[symbol].append(reason)
            continue
        item["status"] = "COMPLETE"
        item["returned_rows"] = len(decoded)
        for row in decoded:
            timestamp = row[0]
            if not start <= timestamp < end:
                ignored["outside_declared_window"] += 1
                continue
            if timestamp + HOUR > received:
                ignored["still_forming_at_receipt"] += 1
                continue
            key = tuple(row)
            previous = versions[symbol].setdefault(timestamp, {}).get(key)
            candidate = {"row": row, "known_at_ms": received, "source_sha256": digest}
            # Earliest supplied receipt of this exact completed version, never bar-close time.
            if previous is None or (received, digest) < (previous["known_at_ms"], previous["source_sha256"]):
                versions[symbol][timestamp][key] = candidate
    observations, coverage = {}, []
    expected = set(range(start, end, HOUR))
    for symbol in sorted(identities):
        records, conflicts = [], []
        for timestamp, choices in sorted(versions[symbol].items()):
            if len(choices) != 1:
                conflicts.append({"ts_ms": timestamp, "versions": [choices[k] for k in sorted(choices)]})
            else:
                records.append(next(iter(choices.values())))
        observations[symbol] = records
        missing = sorted(expected - {r["row"][0] for r in records})
        coverage.append({"symbol": symbol, "status": "INCOMPLETE" if missing else "COMPLETE",
                         "observed_complete_hours": len(records), "missing_or_conflicting_hours": missing,
                         "conflicts": conflicts, "capture_errors": sorted(set(errors[symbol]))})
    return {"status": "COMPLETE" if all(r["status"] == "COMPLETE" for r in coverage) else "INCOMPLETE",
            "qualification": "SUPPLIED_RECEIPTS_NOT_AUTHENTICITY_OR_EXECUTION_PROOF",
            "source_authenticity_verified": False, "start_ms": start, "end_ms": end,
            "as_of_ms": cutoff, "observations": observations, "coverage": coverage,
            "capture_evidence": evidence, "ignored_counts": dict(ignored), "scoring_authorized": False}

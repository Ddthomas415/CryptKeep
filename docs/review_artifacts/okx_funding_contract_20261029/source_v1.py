"""Offline endpoint-specific evidence contract; no financial qualification.

Inputs are caller-owned saved public responses, not authenticated venue proof.
Time gaps describe observations, not a guarantee that no settlement is missing.
"""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from urllib.parse import parse_qsl, urlsplit


def _clock(value):
    if type(value) is not str:
        raise ValueError("receipt_timezone_required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("receipt_timezone_required") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("receipt_timezone_required")
    return parsed


def _milliseconds(value):
    if type(value) is not str or not value.isascii() or not value.isdigit():
        return None
    number = int(value)
    return number if 0 < number <= 253402300799999 else None


def _decimal(value):
    if type(value) is not str or not value.strip():
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_nonfinite(value):
    raise ValueError("nonfinite_json")


def _response(body, receipt, endpoint, inst_id):
    if type(body) is not bytes or len(body) > 1048576 or type(receipt) is not dict:
        raise ValueError("bounded_bytes_and_receipt_required")
    if type(receipt.get("url")) is not str:
        raise ValueError("endpoint_identity_mismatch")
    url = urlsplit(receipt["url"])
    query = parse_qsl(url.query, keep_blank_values=True)
    expected = [("instId", inst_id)]
    if endpoint == "funding-rate-history":
        expected.append(("limit", "5"))
    if (url.scheme != "https" or url.netloc != "www.okx.com" or url.fragment
            or url.path != "/api/v5/public/" + endpoint or sorted(query) != sorted(expected)):
        raise ValueError("endpoint_identity_mismatch")
    if (type(receipt.get("curl_exit_code")) is not int or receipt["curl_exit_code"] != 0
            or receipt.get("http_status") != "200"
            or type(receipt.get("body_bytes")) is not int or receipt["body_bytes"] != len(body)
            or receipt.get("body_sha256") != hashlib.sha256(body).hexdigest()):
        raise ValueError("receipt_integrity_failed")
    start, end = _clock(receipt.get("request_started_at")), _clock(receipt.get("received_at"))
    if start > end:
        raise ValueError("receipt_clock_reversed")
    payload = json.loads(body, object_pairs_hook=_object, parse_constant=_reject_nonfinite)
    if (type(payload) is not dict or payload.get("code") != "0"
            or type(payload.get("data")) is not list or not payload["data"]
            or len(payload["data"]) > 5):
        raise ValueError("api_response_invalid")
    if any(type(row) is not dict or row.get("instId") != inst_id
           or row.get("instType") != "SWAP" for row in payload["data"]):
        raise ValueError("response_identity_mismatch")
    return payload, end


def _field(row, name, kind, time_name):
    rate, timestamp = _decimal(row.get(name)), _milliseconds(row.get(time_name))
    return {
        "source_field": name, "raw_value": deepcopy(row.get(name)),
        "decimal_rate": str(rate) if rate is not None else None,
        "kind": kind, "time_source_field": time_name,
        "reported_time_ms": timestamp,
        "value_and_time_valid": rate is not None and timestamp is not None,
        "native_semantics_verified": False,
    }


def describe_okx_funding_pair(*, current_body, current_receipt, history_body,
                              history_receipt, requested_inst_id):
    """Separate fields and observed gaps without granting any eligibility."""
    if (type(requested_inst_id) is not str or not requested_inst_id.isascii()
            or not requested_inst_id.endswith("-SWAP") or not requested_inst_id):
        raise ValueError("explicit_swap_identity_required")
    current_payload, current_end = _response(current_body, current_receipt, "funding-rate", requested_inst_id)
    history_payload, history_end = _response(history_body, history_receipt, "funding-rate-history", requested_inst_id)
    if len(current_payload["data"]) != 1:
        raise ValueError("current_row_count_invalid")
    current, history = current_payload["data"][0], history_payload["data"]
    times = [_milliseconds(row.get("fundingTime")) for row in history]
    if None in times or len(set(times)) != len(times):
        raise ValueError("historical_times_invalid_or_duplicate")
    if any(timestamp > int(history_end.timestamp() * 1000) for timestamp in times):
        raise ValueError("historical_settlement_in_future")
    ordered = sorted(zip(times, history), key=lambda pair: pair[0])
    events = []
    previous = None
    for timestamp, row in ordered:
        events.append({
            "funding_time_ms": timestamp,
            "realized": _field(row, "realizedRate", "venue_reported_settled", "fundingTime"),
            "published": _field(row, "fundingRate", "historical_published", "fundingTime"),
            "preceding_observed_gap_hours": str(Decimal(timestamp - previous) / 3600000) if previous else None,
            "effective_interval_verified": False,
            "formula_type_reported": deepcopy(row.get("formulaType")),
            "method_reported": deepcopy(row.get("method")),
        })
        previous = timestamp
    prev_time = _milliseconds(current.get("prevFundingTime"))
    funding_time = _milliseconds(current.get("fundingTime"))
    next_time = _milliseconds(current.get("nextFundingTime"))
    settlement = _field(current, "settFundingRate", "venue_reported_settled", "prevFundingTime")
    settlement["sett_state_reported"] = deepcopy(current.get("settState"))
    settlement["reported_settled"] = current.get("settState") == "settled"
    matches = [row for timestamp, row in ordered if timestamp == prev_time]
    historical = _decimal(matches[0].get("realizedRate")) if matches else None
    settled = _decimal(current.get("settFundingRate"))
    return {
        "schema": 1, "contract": "okx_endpoint_evidence_v1", "inst_id": requested_inst_id,
        "raw_current": deepcopy(current_payload), "raw_history": deepcopy(history_payload),
        "receipts": {"current": deepcopy(current_receipt), "history": deepcopy(history_receipt)},
        "current": _field(current, "fundingRate", "current_unsettled_or_estimate", "fundingTime"),
        "next": _field(current, "nextFundingRate", "next_estimate", "nextFundingTime"),
        "reported_settlement": settlement, "history": events,
        "scheduled_gap_hours": str(Decimal(next_time - funding_time) / 3600000)
            if funding_time and next_time and next_time > funding_time else None,
        "cross_checks": {
            "previous_time_in_history": bool(matches),
            "reported_settled_rate_matches_history": settled == historical
                if settlement["reported_settled"] and settled is not None and historical is not None else None,
            "current_rate_differs_from_reported_settlement": _decimal(current.get("fundingRate")) != settled
                if _decimal(current.get("fundingRate")) is not None and settled is not None else None,
            "receipt_span_seconds": abs((current_end - history_end).total_seconds()),
        },
        "normalization_eligible": False, "strategy_eligible": False, "execution_authority": False,
        "rate_per_8h": None, "annualized_pct": None,
        "remaining_requirements": ["native_semantics", "effective_interval_not_just_observed_gap",
                                   "effective_formula", "cash_cost_basis", "crowding_comparability",
                                   "freshness_and_capture_origin"],
    }

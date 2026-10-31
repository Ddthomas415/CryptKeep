"""Pure ED-002 receipt merging and first-batch checks; no signals, files or HTTP."""
from copy import deepcopy
import hashlib
from urllib.parse import parse_qs, urlsplit

from services.backtest import descriptive_candles as candles
from services.backtest import descriptive_metadata as metadata
from services.backtest import shared_cash_research as ledger


HOUR = candles.HOUR


def _scope(symbols, identities):
    if (not isinstance(symbols, (list, tuple)) or len(symbols) != 25
            or any(not isinstance(s, str) or not s for s in symbols)
            or len(set(symbols)) != 25 or not {"BTC", "ETH"} <= set(symbols)
            or not isinstance(identities, dict) or set(identities) != set(symbols)):
        raise ValueError("explicit_25_symbol_scope_required")
    for symbol, identity in identities.items():
        if identity is not None and (not metadata._identity(identity)
                or identity["base_currency"] != symbol or identity["product_id"] != symbol+"-USD"):
            raise ValueError("explicit_native_usd_identity_required")


def _route(record):
    url = urlsplit(record["url"])
    if (record["method"] != "GET" or url.scheme != "https"
            or url.hostname != "api.exchange.coinbase.com" or url.port not in (None, 443)
            or url.username is not None or url.password is not None or url.fragment):
        raise ValueError("public_get_receipt_required")
    if url.path in ("/products", "/currencies") and not url.query:
        return url.path[1:], None
    query = parse_qs(url.query, keep_blank_values=True)
    parts = url.path.split("/")
    if (len(parts) == 4 and parts[1] == "products" and parts[3] == "candles"
            and set(query) == {"granularity", "start", "end"}
            and query["granularity"] == ["3600"]
            and all(len(v) == 1 and v[0] for v in query.values())):
        return "candles", parts[2]
    raise ValueError("public_hourly_route_required")


def merge_receipts(records, *, symbols, identities, start_ms, end_ms, as_of_ms):
    """Normalize caller-supplied raw bodies, not precomputed observation claims.

    Each record supplies method/url/request_started_ms/received_at_ms/http_status,
    response_bytes/sha256/truncated, as saved by the capture worker. Hashes bind
    bytes to supplied receipts; they do not authenticate the caller or exchange.
    The caller must bind symbols/identities to the adopted universe before freeze.
    """
    _scope(symbols, identities)
    start, end, cutoff = map(ledger.timestamp, (start_ms, end_ms, as_of_ms))
    if (start % HOUR or end % HOUR or not start < end <= cutoff
            or not isinstance(records, (list, tuple))):
        raise ValueError("completed_merge_interval_required")
    by_product = {v["product_id"]: s for s, v in identities.items() if v is not None}
    captures, products, evidence, seen = [], {}, [], set()
    future = 0
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("raw_receipt_required")
        if record.get("received_at_ms") is None:
            sent = ledger.timestamp(record.get("request_started_ms"))
            if sent > cutoff:
                future += 1
                continue
            _route(record)
            if (record.get("http_status") is not None or record.get("response_bytes") is not None
                    or not isinstance(record.get("error_class"), str) or not record["error_class"]):
                raise ValueError("unanswered_transport_diagnostic_required")
            evidence.append({"url": record["url"], "request_started_ms": sent,
                             "qualification": "UNANSWERED_NOT_OBSERVATION"})
            continue
        received = ledger.timestamp(record.get("received_at_ms"))
        if received > cutoff:
            future += 1
            continue
        raw = record.get("response_bytes")
        if (not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != record.get("sha256")
                or type(record.get("http_status")) is not int
                or type(record.get("truncated")) is not bool
                or ledger.timestamp(record.get("request_started_ms")) > received):
            raise ValueError("raw_body_receipt_mismatch")
        kind, product = _route(record)
        key = (record["url"], received, record["sha256"], record["http_status"], record["truncated"])
        if key in seen:
            continue
        seen.add(key)
        evidence.append({"url": record["url"], "received_at_ms": received,
            "source_sha256": record["sha256"], "http_status": record["http_status"],
            "truncated": record["truncated"]})
        if kind == "products":
            products.setdefault(received, []).append(record)
        elif kind == "candles":
            if product not in by_product:
                raise ValueError("undeclared_candle_product")
            captures.append({"product_id": product, "method": "GET", "url": record["url"],
                "received_at_ms": received, "response_bytes": raw,
                "http_status": 0 if record["truncated"] else record["http_status"]})
    panel = candles.map_candle_captures(captures, identities=identities,
        start_ms=start, end_ms=end, as_of_ms=cutoff)
    snapshots, failed = [], {}
    for received, group in sorted(products.items()):
        reason = ("ambiguous_products_receipt" if len(group) != 1 else
            "failed_products_receipt" if group[0]["http_status"] != 200 or group[0]["truncated"] else None)
        snapshots.append({"received_at_ms": received, "products_bytes": group[0]["response_bytes"]
                          if reason is None else b""})
        if reason:
            failed[received] = (reason, sorted({r["sha256"] for r in group}))
    mapped = metadata.map_public_metadata(snapshots, identities=identities) if snapshots else {
        "rules": {s: [] for s in sorted(symbols)}, "observations": []}
    # Failed HTTP bodies must not grant permission even if they look like a valid list.
    for rows in mapped["rules"].values():
        for row in rows:
            if row["known_at_ms"] in failed:
                reason, hashes = failed[row["known_at_ms"]]
                row.update(eligible=None, metadata_reason=reason, source_sha256=None,
                           original_source_sha256=hashes)
    for row in mapped["observations"]:
        if row["received_at_ms"] in failed:
            reason, hashes = failed[row["received_at_ms"]]
            row.update(status="INCOMPLETE", eligible=None, reason=reason,
                       source_sha256=None, original_source_sha256=hashes)
    return {"qualification": "MERGED_SUPPLIED_RECEIPTS_NOT_STUDY_OR_AUTHENTICITY_PROOF",
        "symbols": sorted(symbols), "identities": deepcopy(identities),
        "as_of_ms": cutoff, "start_ms": start, "end_ms": end,
        "observations": panel["observations"], "coverage": panel["coverage"],
        "physical_window_status": panel["status"], "rules": mapped["rules"],
        "metadata_observations": mapped["observations"], "receipt_evidence": evidence,
        "ignored_future_receipts": future, "scoring_authorized": False}


def first_batch_readiness(merged, *, signal_close_ms, checked_at_ms):
    """Check flat-account initial inputs only, not execution opens or activation.

    Use the merged prefix through min(actual check time, E). A report cannot
    retroactively import a later receipt into the fixed E deadline. All 25 rows
    remain visible. This does not assess future held positions or compute signals.
    """
    close, checked = map(ledger.timestamp, (signal_close_ms, checked_at_ms))
    execution = close+HOUR
    if close % HOUR or checked < close or merged["end_ms"] != close:
        raise ValueError("initial_signal_close_and_check_clock_required")
    if merged["as_of_ms"] != min(checked, execution):
        raise ValueError("merge_at_fixed_first_batch_cutoff_required")
    _scope(merged["symbols"], merged["identities"])
    by_symbol = {r["symbol"]: r for r in merged["coverage"]}
    results = []
    for symbol in merged["symbols"]:
        row = {"symbol": symbol, "status": "COMPLETE", "reasons": [],
               "required_signal_hours": 0, "signal_eligible": None, "execution_eligible": None}
        for field, clock in (("signal_eligible", close), ("execution_eligible", execution)):
            try:
                row[field] = ledger.rule_at(merged["rules"], symbol, clock, clock, "coinbase", "USD")["eligible"]
            except ledger.Incomplete:
                row["reasons"].append("unknown_"+field)
        if symbol in ("BTC", "ETH") and (row["signal_eligible"] is False or row["execution_eligible"] is False):
            row["reasons"].append("required_control_ineligible")
        if row["signal_eligible"] is True:
            count = 1464 if symbol in ("BTC", "ETH") else 300
            row["required_signal_hours"] = count
            records = {r["row"][0]: r for r in merged["observations"][symbol]}
            wanted = range(close-count*HOUR, close, HOUR)
            missing = [t for t in wanted if t not in records or records[t]["known_at_ms"] > execution]
            row["missing_or_late_hours"] = missing
            conflicts = [r["ts_ms"] for r in by_symbol[symbol]["conflicts"] if close-count*HOUR <= r["ts_ms"] < close]
            row["conflicting_hours"] = conflicts
            if missing:
                row["reasons"].append("missing_late_or_conflicting_signal_history")
        if row["reasons"]:
            row["status"] = "INCOMPLETE"
        results.append(row)
    return {"status": "COMPLETE" if all(r["status"] == "COMPLETE" for r in results) else "INCOMPLETE",
        "qualification": "FLAT_FIRST_BATCH_INPUTS_ONLY_NOT_ACTIVATION",
        "signal_close_ms": close, "execution_ms": execution, "checked_at_ms": checked,
        "deadline_passed": checked > execution, "rows": results,
        "execution_open_verified": False, "activation_authorized": False,
        "scoring_authorized": False, "statistical_qualification": "INCOMPLETE"}

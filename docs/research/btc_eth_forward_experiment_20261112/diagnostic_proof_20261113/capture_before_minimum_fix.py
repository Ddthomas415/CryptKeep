"""Offline by default. Public diagnostic, not orders, E1 qualification or fill evidence.

Live use requires a separately authorized parent enforcing a 75-second process
deadline. Socket timeouts and local deadline checks are cooperative, not that bound.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
import math
from pathlib import Path
import ssl
import statistics
import time
import urllib.error
import urllib.request

BASE = "https://api.exchange.coinbase.com"
PRODUCTS = ("BTC-USD", "ETH-USD")
PER_BODY, TOTAL_BODY, MAX_GETS = 1 << 20, 10 << 20, 10
FLAGS = ("trading_disabled", "cancel_only", "post_only", "limit_only", "auction_mode")
HEADERS = ("date", "content-type", "cb-before", "cb-after")
URLS = {BASE + "/products/" + p + suffix for p in PRODUCTS
        for suffix in ("", "/book?level=2", "/trades?limit=100")}


class Invalid(ValueError):
    pass


def positive(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise Invalid("invalid_number")
    try:
        value = float(value)
    except (ValueError, OverflowError):
        raise Invalid("invalid_number") from None
    if not math.isfinite(value) or value <= 0:
        raise Invalid("invalid_number")
    return value


def metadata(value, product):
    if not isinstance(value, dict) or any(value.get(k) != v for k, v in (
            ("id", product), ("base_currency", product[:-4]), ("quote_currency", "USD"))):
        raise Invalid("metadata_identity")
    status = value.get("status")
    known = status in ("online", "offline", "internal", "delisted") and all(
        type(value.get(k)) is bool for k in FLAGS)
    return {"status": status if status in ("online", "offline", "internal", "delisted") else "UNKNOWN",
            "eligibility": (status == "online" and not any(value.get(k) is True for k in FLAGS)) if known else None,
            "eligibility_basis": "declared_online_and_all_modes_known; not order acceptance",
            "product_rules": {k: value.get(k) for k in ("base_increment", "quote_increment", "min_market_funds")},
            "flags": {k: value.get(k) if type(value.get(k)) is bool else None for k in FLAGS}}


def book(value):
    if not isinstance(value, dict) or value.get("auction_mode") not in (None, False) or (
            "auction_mode" in value and type(value["auction_mode"]) is not bool):
        raise Invalid("auction_or_invalid_book")
    if value.get("auction"):
        raise Invalid("auction_or_invalid_book")
    result = {}
    for side in ("bids", "asks"):
        rows = value.get(side)
        if not isinstance(rows, list) or not rows:
            raise Invalid("missing_book_side")
        levels = []
        for row in rows:
            if not isinstance(row, list) or len(row) != 3 or type(row[2]) is not int or row[2] <= 0:
                raise Invalid("invalid_book_level")
            levels.append((positive(row[0]), positive(row[1])))
        if len({p for p, _ in levels}) != len(levels):
            raise Invalid("duplicate_book_price")
        result[side] = sorted(levels, reverse=side == "bids")
    bid, ask = result["bids"][0][0], result["asks"][0][0]
    if bid >= ask:
        raise Invalid("crossed_or_locked_book")
    mid = bid + (ask - bid) / 2
    depth = {side: sum(p * q for p, q in result[side] if abs(p / mid - 1) <= .001)
             for side in ("bids", "asks")}
    if not all(math.isfinite(v) for v in depth.values()):
        raise Invalid("nonfinite_depth")
    return {**result, "mid": mid, "spread_bps": (ask - bid) / mid * 10000,
            "half_spread_fraction": (ask - bid) / (2 * mid),
            "auction_mode": value.get("auction_mode"),
            "source_time": value.get("time") if isinstance(value.get("time"), str) else None,
            "sequence": value.get("sequence") if type(value.get("sequence")) is int else None,
            "visible_usd_within_10bps_of_mid": depth}


def walk(levels, qty):
    qty = positive(qty)
    remaining, gross = qty, 0.0
    for price, size in levels:
        take = min(remaining, size)
        gross += price * take
        remaining -= take
        if remaining <= 0:
            break
    if remaining > 0 or not math.isfinite(gross):
        raise Invalid("insufficient_visible_depth")
    return gross


def cost(gross, qty, reference_mid, side, fee):
    gross, qty, reference_mid = positive(gross), positive(qty), positive(reference_mid)
    if side not in ("buy", "sell") or isinstance(fee, bool) or not isinstance(fee, (float, int)) or not 0 <= fee < 1:
        raise Invalid("invalid_model_cost_inputs")
    reference = qty * reference_mid
    price_cost = (gross - reference) * (1 if side == "buy" else -1)
    fees = gross * fee
    if not all(math.isfinite(v) for v in (gross, reference, price_cost, fees)) or reference <= 0:
        raise Invalid("nonfinite_model_cost")
    return {"gross_notional_usd": gross, "price_cost_usd": price_cost, "fee_usd": fees,
            "total_cost_usd": price_cost + fees, "cost_bps": (price_cost + fees) / reference * 10000}


def analyse(meta, books, prints, interval):
    if meta["eligibility"] is not True:
        raise Invalid("ineligible_or_unknown_metadata")
    t0, arrival, final = books
    rules = meta["product_rules"]
    try:
        increment, tick, minimum = [Decimal(str(positive(rules[k]))) for k in
                                    ("base_increment", "quote_increment", "min_market_funds")]
        quantity = (Decimal(500) / Decimal(str(t0["mid"])) / increment).to_integral_value(rounding=ROUND_FLOOR) * increment
    except (ArithmeticError, KeyError):
        raise Invalid("unknown_product_rules") from None
    qty, models = positive(str(quantity)), {}
    if quantity * Decimal(str(t0["mid"])) < minimum:
        raise Invalid("below_product_minimum")
    for side, take_side, rest_side in (("buy", "asks", "bids"), ("sell", "bids", "asks")):
        limit = t0[rest_side][0][0]
        if Decimal(str(limit)) % tick:
            raise Invalid("off_tick_limit")
        resting = limit < arrival["asks"][0][0] if side == "buy" else limit > arrival["bids"][0][0]
        immediate = cost(walk(arrival[take_side], qty), qty, t0["mid"], side, .005)
        fallback = cost(walk(final[take_side], qty), qty, t0["mid"], side, .005)
        models[side] = {"qty_base": qty, "t0_limit": limit, "maker_non_crossing_at_arrival": resting,
                       "maker_eligibility": "CONDITIONAL_NOT_FILL_PROOF" if resting else "HYPOTHETICAL_POST_ONLY_REJECTION",
                       "arrival_taker": immediate, "no_maker_fill_final_taker": fallback,
                       "optimistic_full_maker": cost(limit * qty, qty, t0["mid"], side, .0025) if resting else None,
                       "observed_trade_through": "NOT_INFERRED_WITH_UNVERIFIED_SOURCE_CLOCK_ALIGNMENT"}
    if not isinstance(prints, list) or not 0 < len(prints) <= 100:
        raise Invalid("missing_or_invalid_trade_page")
    prices, ids, selected = [], set(), []
    for row in prints:
        if not isinstance(row, dict) or row.get("side") not in ("buy", "sell") or type(row.get("trade_id")) is not int:
            raise Invalid("invalid_trade")
        if row["trade_id"] in ids:
            raise Invalid("duplicate_trade")
        ids.add(row["trade_id"])
        p, _ = positive(row.get("price")), positive(row.get("size"))
        if not isinstance(row.get("time"), str):
            raise Invalid("invalid_trade_time")
        try:
            stamp = datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
        except ValueError:
            raise Invalid("invalid_trade_time") from None
        if stamp.utcoffset() != timezone.utc.utcoffset(stamp):
            raise Invalid("trade_time_not_utc")
        if interval[0] <= stamp.timestamp() <= interval[1]:
            prices.append(p)
            selected.append({"trade_id": row["trade_id"], "time": stamp.isoformat(),
                             "price": p, "size": positive(row["size"]), "maker_side": row["side"]})
    if not prices:
        raise Invalid("no_reported_trades_in_local_window")
    mean = statistics.mean(prices)
    return {"status": "COMPLETE", "metadata": meta, "books": books, "reference_usd": 500,
            "hypothetical_models": models, "maker_fee_bps": 25, "taker_fee_bps": 50,
            "fees_provisional_not_account_verified": True,
            "assumptions": ["maker fractions 0 and 1 are assumptions, not probabilities",
                            "maker best case ignores queue, cancellations and intervening book changes",
                            "visible depth is not guaranteed; basic increments/minimum only, not full order validation"],
            "mid_move_t0_arrival_bps": (arrival["mid"] / t0["mid"] - 1) * 10000,
            "mid_move_t0_final_bps": (final["mid"] / t0["mid"] - 1) * 10000,
            "trade_page_rows": len(prints), "window_prints": len(prices), "selected_reported_trades": selected,
            "trade_price_dispersion_bps": statistics.pstdev(prices) / mean * 10000,
            "trade_side_semantics": "Coinbase Exchange maker side, not aggressor side",
            "trade_page_coverage": "UNVERIFIED", "source_clock_alignment": "UNVERIFIED",
            "volatility_scope": "short local observation only; not annualized or a historical regime"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def public_getter():
    import certifi
    # Explicit context avoids SSLKEYLOGFILE/default-context environment hooks.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cafile=certifi.where())
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=context))

    def get(url, timeout, limit, sink):
        if url not in URLS or not 0 < timeout <= 5 or not 0 < limit <= PER_BODY:
            raise Invalid("unsafe_request")
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "CryptKeep-public-diagnostic/1",
                                                               "Accept": "application/json", "Accept-Encoding": "identity"})
        response, status, headers, failure = None, None, {}, None
        deadline = time.monotonic() + timeout
        try:
            try:
                response = opener.open(req, timeout=timeout)
            except urllib.error.HTTPError as error:
                response = error
            status = response.code
            headers = {k: response.headers.get(k) for k in HEADERS}
            while sink.count < limit:
                if time.monotonic() >= deadline:
                    raise TimeoutError()
                raw = response.read(min(65536, limit - sink.count))
                if not raw:
                    break
                sink.write(raw)
            if time.monotonic() >= deadline:
                failure = "request_deadline"
        except Exception:
            failure = "transport_failure"
        finally:
            if response is not None:
                response.close()
        return status, headers, failure
    return get


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write("\n")


class Body:
    def __init__(self, stream, limit):
        self.stream, self.limit, self.count = stream, limit, 0

    def write(self, raw):
        part = raw[:self.limit - self.count]
        if self.stream.write(part) != len(part):
            raise Invalid("short_body_write")
        self.count += len(part)
        if len(part) != len(raw):
            raise Invalid("body_limit")


def capture(output, *, get=None, clock=time):
    output = Path(output)
    output.mkdir(mode=0o700, exist_ok=False)
    result = {"status": "INCOMPLETE", "qualification": "OFF_WINDOW_PUBLIC_DIAGNOSTIC_NOT_E1_OR_FILL_PROOF",
              "orders_submitted": False, "e1_qualified": False, "products": {}, "requests": [],
              "evidence_labels": ["OBSERVED_PUBLIC_MARKET_DATA_WITH_VALIDATION_LIMITS", "CF-MODELLED"],
              "actual_account_fills": "UNVERIFIED", "trade_page_coverage": "UNVERIFIED"}
    used = 0

    def request(product, suffix, label):
        nonlocal used
        if len(result["requests"]) >= MAX_GETS or used >= TOTAL_BODY:
            raise Invalid("capture_budget")
        url, index = BASE + "/products/" + product + suffix, len(result["requests"]) + 1
        if url not in URLS:
            raise Invalid("unsafe_request")
        record = {"url": url, "product": product, "label": label, "method": "GET",
                  "request_utc": datetime.fromtimestamp(clock.time(), timezone.utc).isoformat()}
        write_json(output / f"{index:02d}_intent.json", record)
        result["requests"].append(record)
        started, failure, status, headers = clock.monotonic(), None, None, {}
        limit = min(PER_BODY, TOTAL_BODY - used)
        raw_path = output / f"{index:02d}_raw.bin"
        try:
            with raw_path.open("xb", buffering=0) as stream:
                sink = Body(stream, limit)
                status, headers, failure = get(url, 5, limit, sink)
        except (Exception, KeyboardInterrupt):
            failure = "request_failure"
        raw = raw_path.read_bytes()
        used += len(raw)
        received = clock.time()
        duration = clock.monotonic() - started
        if received < datetime.fromisoformat(record["request_utc"]).timestamp() or not math.isfinite(duration) or duration < 0:
            failure = "invalid_local_clock"
        elif duration > 5:
            failure = "request_deadline"
        record.update(receipt_utc=datetime.fromtimestamp(received, timezone.utc).isoformat(),
            duration_seconds=duration, http_status=status, failure=failure,
            headers={k: v[:256] for k, v in headers.items() if k in HEADERS and isinstance(v, str)},
            raw_file=raw_path.name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
            body_at_cap_or_truncated=len(raw) >= limit)
        write_json(output / f"{index:02d}_receipt.json", record)
        if failure or status != 200 or len(raw) >= limit:
            raise Invalid("request_incomplete")
        return json.loads(raw), received

    try:
        get = get or public_getter()
        for product in PRODUCTS:
            value, _ = request(product, "", "metadata")
            meta = metadata(value, product)
            result["products"][product] = {"status": "INCOMPLETE", "metadata": meta}
            if meta["eligibility"] is not True:
                raise Invalid("ineligible_or_unknown_metadata")
            value, start = request(product, "/book?level=2", "t0")
            books = [book(value)]
            result["products"][product]["observed_books"] = books
            for label in ("arrival", "final"):
                clock.sleep(2)
                value, end = request(product, "/book?level=2", label)
                books.append(book(value))
            prints, _ = request(product, "/trades?limit=100", "trades")
            result["products"][product] = analyse(meta, books, prints, (start, end))
        result["status"] = "COMPLETE"
    except (Exception, KeyboardInterrupt) as exc:
        result["reason"] = str(exc) if isinstance(exc, Invalid) else "capture_or_validation_incomplete"
    result.update(stored_payload_bytes=used, get_count=len(result["requests"]),
                  timing_basis="T0 local receipt; sleeps 2s then 2s; not exact source-clock or Monday-open alignment")
    write_json(output / "report.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.capture:
        print('{"status":"OFFLINE","orders_submitted":false}')
        return 0
    if args.output is None:
        parser.error("--capture requires --output pointing to a new folder")
    try:
        result = capture(args.output)
        print(json.dumps({k: result[k] for k in ("status", "get_count", "orders_submitted")}))
        return 0 if result["status"] == "COMPLETE" else 2
    except Exception:
        print('{"status":"INCOMPLETE","reason":"exclusive_output_or_report_failure"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

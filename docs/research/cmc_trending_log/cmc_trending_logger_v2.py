"""Append-only public-data capture; no orders, credentials or evaluation.

Preserves v1's files and hypothesis. Retains Coinbase observations for 35 days
after list appearance (30-day endpoint plus collection grace, not an exit rule).
Identity matches remain UNVERIFIED unless an explicit evidence-backed map agrees.
The evaluation must separately define valid timing, missingness and mature cohorts.
"""

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request
import uuid
import warnings

UTC = dt.timezone.utc
CMC = "https://api.coinmarketcap.com/data-api/v3/unified-trending/listing"
CB = "https://api.exchange.coinbase.com"
BN = "https://data-api.binance.vision/api/v3"


def utcnow():
    return dt.datetime.now(UTC)


def stamp(value):
    return value.isoformat(timespec="microseconds")


def request(url, body=None):
    started = utcnow()
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"User-Agent": "cryptkeep-research-v2", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
        payload = json.loads(raw)
        return {"payload": payload, "request_started_utc": stamp(started),
                "received_utc": stamp(utcnow()), "response_sha256": hashlib.sha256(raw).hexdigest()}
    except Exception as exc:
        return {"payload": None, "request_started_utc": stamp(started),
                "received_utc": stamp(utcnow()), "error": str(exc)}


def read_history(directory, now):
    history = []
    for path in sorted(directory.glob("*.json")):
        raw = path.read_bytes()
        item = json.loads(raw)
        when = dt.datetime.fromisoformat(item["snapshot_utc"].replace("Z", "+00:00"))
        if when.tzinfo is None or when > now:
            raise ValueError(f"invalid/future snapshot timestamp: {path.name}")
        if now - when <= dt.timedelta(days=35):
            history.append((item, {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}))
    return history


def watchlist(history, current):
    watched = {}
    for item in [h[0] for h in history] + [current]:
        for row in item.get("trending_hidden_boost", []):
            if row.get("type") != "listing" or "coinbase" not in row:
                continue
            symbol = str(row.get("symbol", "")).upper()
            product = row.get("coinbase_product", symbol + "-USD")
            if not symbol or not product.endswith("-USD"):
                raise ValueError("invalid retained Coinbase product")
            key = (str(row.get("cmc_id")), product)
            watched[key] = {"cmc_id": row.get("cmc_id"), "symbol": symbol,
                            "coinbase_product": product}
    return list(watched.values())


def quote(fetch, product):
    result = fetch(f"{CB}/products/{product}/ticker")
    payload = result.get("payload")
    result["quote_status"] = "MISSING"
    if isinstance(payload, dict):
        try:
            bid, ask = float(payload["bid"]), float(payload["ask"])
            if not (0 < bid <= ask < float("inf")):
                raise ValueError("invalid bid/ask")
            result["quote_status"] = "OBSERVED_NOT_FILL_PROOF"
        except (KeyError, TypeError, ValueError):
            result["validation_error"] = "missing, non-finite or crossed bid/ask"
    return result


def collect(directory, identities=None, fetch=request, now=None):
    now = now or utcnow()
    identities = identities or {}
    history = read_history(directory, now)
    hidden = fetch(CMC, {"interval": "24h", "pageNum": 1, "pageSize": 100, "boostType": "hideBoost"})
    shown = fetch(CMC, {"interval": "24h", "pageNum": 1, "pageSize": 100})
    products = fetch(CB + "/products")
    payload = products.get("payload")
    available = {p["id"] for p in payload if isinstance(p, dict) and p.get("quote_currency") == "USD"
                 and p.get("status") == "online" and "id" in p} if isinstance(payload, list) else set()
    data = hidden.get("payload")
    nested = data.get("data") if isinstance(data, dict) else None
    source_rows = nested.get("list") if isinstance(nested, dict) else None
    source_errors = []
    if not isinstance(source_rows, list):
        source_errors.append("invalid or missing hidden-list envelope")
        source_rows = []
    current = []
    for rank, item in enumerate(source_rows, 1):
        if not isinstance(item, dict) or not isinstance(item.get("tokenSymbol"), str):
            source_errors.append(f"invalid hidden-list row {rank}")
            continue
        row = {"trend_rank": rank, "type": item.get("type"), "cmc_id": item.get("cryptoId"),
               "symbol": item.get("tokenSymbol"), "source_record": item}
        product = str(item.get("tokenSymbol", "")).upper() + "-USD"
        if item.get("type") == "listing" and product in available:
            row.update(coinbase_product=product, coinbase={"capture_pending": True})
        current.append(row)
    result = {"artifact_type": "research_only_forward_log_v2", "schema_version": 2,
              "places_orders": False, "snapshot_utc": stamp(now),
              "collector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "identity_map_sha256": hashlib.sha256(json.dumps(identities, sort_keys=True).encode()).hexdigest(),
              "history_sources": [h[1] for h in history], "trending_hidden_boost": current,
              "source_responses": {"hidden": hidden, "shown": shown, "coinbase_products": products},
              "trending_status": "DEGRADED" if source_errors else ("OBSERVED" if current else "MISSING"),
              "source_errors": source_errors,
              "tracked_coinbase": [], "majors_coinbase": {}}
    cache = {}
    for row in watchlist(history, result):
        product = row["coinbase_product"]
        if product not in cache:
            cache[product] = quote(fetch, product)
        identity = identities.get(str(row["cmc_id"]), {})
        verified = identity.get("coinbase_product") == product and bool(identity.get("evidence"))
        row.update(identity_status="OPERATOR_MAPPED" if verified else "UNVERIFIED",
                   identity_evidence=identity.get("evidence") if verified else None,
                   quote=cache[product])
        result["tracked_coinbase"].append(row)
    for row in current:
        if "coinbase_product" in row:
            row["coinbase"] = cache[row["coinbase_product"]]
    for symbol in ("BTC", "ETH"):
        product = symbol + "-USD"
        if product not in cache:
            cache[product] = quote(fetch, product)
        result["majors_coinbase"][symbol] = cache[product]
    # Preserve Binance context without presenting symbol matches as verified identity.
    result["binance_book"] = fetch(BN + "/ticker/bookTicker")
    return result


def save(directory, result):
    raw = json.dumps(result, sort_keys=True, allow_nan=False).encode()
    name = "v2_" + utcnow().strftime("%Y-%m-%d_%H%M%S_%fZ_") + uuid.uuid4().hex + ".json"
    target = directory / name
    fd, temporary = tempfile.mkstemp(prefix=".pending_", dir=directory)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(temporary)
        except PermissionError:
            # Connected-folder sandboxes may allow publication but forbid cleanup.
            # Do not mask either successful publication or its original failure.
            warnings.warn(f"Temporary snapshot retained; cleanup denied: {temporary}", RuntimeWarning)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--identity-map", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    identities = json.loads(args.identity_map.read_text()) if args.identity_map else {}
    with (args.out / ".collector.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = collect(args.out, identities)
        target = save(args.out, result)
    print(json.dumps({"file": str(target), "trending_status": result["trending_status"],
                      "tracked_products": len(result["tracked_coinbase"])}))
    return 0 if result["trending_status"] == "OBSERVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

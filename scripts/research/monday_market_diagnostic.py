"""Exploratory public Monday diagnostic, not strategy validation or trade authority."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import time

import requests


DAY = 86400
BASE = "https://api.coinbase.com/api/v3/brokerage/market"


def day_summary(candles, cutoff, fee=0.005):
    rows = {int(c["start"]): c for c in candles}
    groups = {"monday": [], "other_days": []}
    for start, candle in sorted(rows.items()):
        end = start + DAY
        if end > cutoff or end not in rows or start % DAY:
            continue
        opening = float(candle["open"])
        closing = float(rows[end]["open"])
        if opening <= 0 or closing <= 0:
            continue
        group = "monday" if datetime.fromtimestamp(start, timezone.utc).weekday() == 0 else "other_days"
        gross = closing / opening - 1
        groups[group].append({"start_utc": datetime.fromtimestamp(start, timezone.utc).isoformat(),
                              "gross_pct": gross * 100,
                              "fee_adjusted_pct": (closing / opening * (1-fee)/(1+fee)-1)*100})
    output = {}
    for name, events in groups.items():
        values = [r["fee_adjusted_pct"] for r in events]
        output[name] = {"count": len(values), "events": events,
                        "mean_fee_adjusted_pct": statistics.mean(values) if values else None,
                        "median_fee_adjusted_pct": statistics.median(values) if values else None,
                        "positive_fraction": sum(v > 0 for v in values)/len(values) if values else None}
    return output


def run(output):
    now = int(time.time())
    cutoff = now // DAY * DAY
    with Path(output).open("x") as stream, requests.Session() as session:
        session.trust_env = False
        def fetch(path, params=None):
            response = session.get(BASE+path, params=params, timeout=20, allow_redirects=False)
            if response.status_code != 200:
                raise ValueError("public_request_failed")
            return response.json(), hashlib.sha256(response.content).hexdigest()
        products, product_hash = fetch("/products", {"limit": 500, "product_type": "SPOT"})
        eligible = [p for p in products.get("products", [])
                    if p.get("quote_currency_id") == "USD" and not p.get("trading_disabled")
                    and not p.get("is_disabled")]
        eligible.sort(key=lambda p: float(p.get("volume_24h", "0"))*float(p.get("price", "0")), reverse=True)
        universe = list(dict.fromkeys([p["product_id"] for p in eligible[:8]] + ["BTC-USD", "GTC-USD"]))
        result = {"observed_at_utc": datetime.fromtimestamp(now, timezone.utc).isoformat(),
                  "kind": "EXPLORATORY_MONDAY_DIAGNOSTIC", "products_response_sha256": product_hash,
                  "universe_basis": "top8_returned_current_USD_quote_volume_plus_BTC_GTC",
                  "returned_product_count": len(products.get("products", [])),
                  "limitations": ["current_listing_and_volume_selection_bias", "no_holdout",
                                 "OHLC_open_price_proxies_not_execution_quotes", "no_spread_or_slippage",
                                 "no_multiple_testing_or_statistical_edge_claim"],
                  "fee_per_side_assumption": 0.005, "orders_submitted": False,
                  "scoring_authorized": False, "markets": {}}
        for product in universe:
            data, digest = fetch("/products/"+product+"/candles",
                                 {"start": cutoff-182*DAY, "end": now,
                                  "granularity": "ONE_DAY", "limit": 350})
            candles = data.get("candles", [])
            today = next((c for c in candles if int(c["start"]) == cutoff), None)
            info = next((p for p in eligible if p["product_id"] == product), None)
            if info is None:
                info, _ = fetch("/products/"+product)
            market = {"raw_candles": data, "response_sha256": digest,
                      "history": day_summary(candles, cutoff), "reported_price": info.get("price"),
                      "today_partial_open_change_pct": (float(info["price"])/float(today["open"])-1)*100
                          if today and float(today["open"]) > 0 else None}
            if product == "GTC-USD":
                book, book_hash = fetch("/product_book", {"product_id": product, "limit": 10})
                if book.get("pricebook", {}).get("product_id") != product:
                    raise ValueError("book_identity_mismatch")
                market.update(book=book, book_response_sha256=book_hash)
            result["markets"][product] = market
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"observed_at_utc": result["observed_at_utc"], "markets": {
        p: {"reported_price": d["reported_price"],
            "today_partial_open_change_pct": d["today_partial_open_change_pct"],
            "history": {k: {f: v for f, v in s.items() if f != "events"}
                        for k, s in d["history"].items()},
            "gtc_book": d.get("book", {}).get("pricebook")}
        for p, d in result["markets"].items()}}, allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    run(parser.parse_args().output)

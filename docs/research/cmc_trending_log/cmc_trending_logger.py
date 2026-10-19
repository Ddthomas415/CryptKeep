"""Daily forward log of CoinMarketCap's trending list, with prices you could actually trade at. Research only.
Places no orders, reads no keys, touches no CryptKeep config, state or account. Public endpoints only.

Each run writes one JSON file into --out (named by UTC time) holding:
  - CMC unified trending, 24h, top 100 with paid Boosts hidden, and the first 100 with Boosts shown;
  - for every listed coin: CMC id, symbol, trend rank, CMC price, 24h volume, market cap, % changes;
  - Coinbase USD best bid / ask / last for SYMBOL-USD when Coinbase lists it (public ticker);
  - Binance best bid / ask for SYMBOLUSDT when Binance lists it (public data mirror);
  - BTC-USD and ETH-USD bid / ask on Coinbase every run (spread evidence for the BTC+ETH paper test).

PRE-REGISTERED EVALUATION (written 2026-10-09, before any data is collected; run it only after >= 90 days of logs):
  Event = a coin's FIRST appearance in the hidden-boost top 100 within any 30-day window, Coinbase-listed at that moment.
  Entry = Coinbase ask in that snapshot. Exit = Coinbase bid in the snapshot closest to 1, 7 and 30 days later.
  Cost = 1.2% fee per side on top of the bid/ask. Benchmark = BTC-USD over the same entry/exit times, same costs.
  Report per horizon: number of events, mean and median net return, share positive, mean excess over BTC with a
  bootstrap 90% range (resampling by entry day). The trending hypothesis counts as worth further work only if the
  7-day mean excess over BTC is above 0 with the whole 90% range above 0. Coins with no Coinbase quote are counted
  and reported but not traded. No parameter of this evaluation may be changed after data collection starts."""
import argparse, json, os, time, urllib.request, datetime as dt

UA = {"User-Agent": "Mozilla/5.0 cryptkeep-research", "Content-Type": "application/json"}
CMC = "https://api.coinmarketcap.com/data-api/v3/unified-trending/listing"
CB = "https://api.exchange.coinbase.com"
BN = "https://data-api.binance.vision/api/v3"

def get(url, data=None, tries=4):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            err = str(e)
            time.sleep(2 * (a + 1))
    return {"_error": err}

def trending(hide_boost):
    body = {"interval": "24h", "pageNum": 1, "pageSize": 100}
    if hide_boost: body["boostType"] = "hideBoost"
    j = get(CMC, body)
    return (j.get("data") or {}).get("list", []) if isinstance(j, dict) else [], j.get("status") if isinstance(j, dict) else None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    hidden, st1 = trending(True); shown, st2 = trending(False)
    prods = get(f"{CB}/products")
    cb = {p["base_currency"].upper() for p in prods if isinstance(p, dict) and p.get("quote_currency") == "USD" and p.get("status") == "online"} if isinstance(prods, list) else set()
    info = get(f"{BN}/exchangeInfo")
    bn = {s["baseAsset"].upper() for s in info.get("symbols", []) if s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING"} if isinstance(info, dict) else set()
    bnbook = get(f"{BN}/ticker/bookTicker")
    bnq = {r["symbol"]: r for r in bnbook} if isinstance(bnbook, list) else {}
    def cbq(sym):
        t = get(f"{CB}/products/{sym}-USD/ticker", tries=2)
        return {k: t.get(k) for k in ("bid", "ask", "price", "time")} if isinstance(t, dict) and "bid" in t else {"error": t.get("_error") or t.get("message")}
    rows = []
    for rank, x in enumerate(hidden, 1):
        sym = (x.get("tokenSymbol") or "").upper()
        r = {"trend_rank": rank, "type": x.get("type"), "cmc_id": x.get("cryptoId"), "symbol": x.get("tokenSymbol"), "name": x.get("tokenName"),
             "cmc_price": x.get("priceUsd"), "volume_24h": x.get("volume24h"), "market_cap": x.get("marketCap"),
             "chg_1h": x.get("pricePercentageChange1h"), "chg_24h": x.get("pricePercentageChange24h"), "chg_7d": x.get("pricePercentageChange7d"),
             "chg_30d": x.get("pricePercentageChange30d"), "cmc_rank": x.get("listingRank"), "age": x.get("age"),
             "token_address": x.get("tokenAddress"), "platform": x.get("platformName")}
        if x.get("type") == "listing" and sym in cb:
            r["coinbase"] = cbq(sym); time.sleep(0.15)
        if x.get("type") == "listing" and sym in bn and sym + "USDT" in bnq:
            q = bnq[sym + "USDT"]; r["binance"] = {"bid": q.get("bidPrice"), "ask": q.get("askPrice")}
        rows.append(r)
    out = {"artifact_type": "research_only_forward_log", "places_orders": False, "snapshot_utc": now.isoformat(timespec="seconds"),
           "cmc_status": [st1, st2], "trending_hidden_boost": rows,
           "trending_with_boost": [{"rank": i, "type": x.get("type"), "cmc_id": x.get("cryptoId"), "symbol": x.get("tokenSymbol")} for i, x in enumerate(shown, 1)],
           "majors_coinbase": {s: cbq(s) for s in ("BTC", "ETH")}}
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, now.strftime("%Y-%m-%d_%H%M") + "Z.json")
    json.dump(out, open(path, "w"))
    n_cb = sum(1 for r in rows if "coinbase" in r and "bid" in r["coinbase"])
    print(json.dumps({"file": path, "trending_rows": len(rows), "with_boost_rows": len(out["trending_with_boost"]),
                      "coinbase_quoted": n_cb, "binance_quoted": sum(1 for r in rows if "binance" in r),
                      "btc": out["majors_coinbase"]["BTC"], "eth": out["majors_coinbase"]["ETH"]}))
    if not rows: raise SystemExit("no trending rows returned")

if __name__ == "__main__":
    main()

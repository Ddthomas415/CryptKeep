"""Descriptive deep-dive of CoinMarketCap's top-100 trending list (24h, paid boosts hidden) as of 2026-10-09.
Not a backtest: CMC publishes no trending history. For each listed coin: CMC daily history (~400 days), returns over
1/7/30/90/365 days, distance from its 1-year high and low, market cap, volume/market cap, age, CMC tags, whether it
trades on Coinbase (USD) or Binance (USDT). DEX-only tokens are listed but have no CMC history."""
import json, os, sys, time, urllib.request, datetime as dt
S = sys.argv[1]
T = json.load(open(f"{S}/cmc/trending/unified_trending_24h_hideboost_2026-10-09.json"))["data"]["list"]
H = "https://api.coinmarketcap.com/data-api/v3.1/cryptocurrency/historical?id={}&convertId=2781&timeEnd=1791504000&interval=1d"
def get(u):
    for a in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 research"}), timeout=60) as r: return json.loads(r.read())
        except Exception: time.sleep(2 + 2 * a)
cb = {f.split("-")[0] for f in os.listdir(f"{S}/cb/h1")} if os.path.isdir(f"{S}/cb/h1") else set()
bn = {f[:-9] for f in os.listdir(f"{S}/bn/d1") if f.endswith("USDT.json")}
snap = {r[0]: r for r in json.load(open(f"{S}/cmc/weekly/2026-10-04.json"))}
rows = []
for k, x in enumerate(T, 1):
    rec = {"trend_rank": k, "type": x["type"], "symbol": x["tokenSymbol"], "name": x["tokenName"], "cmc_id": x.get("cryptoId"),
           "price": float(x["priceUsd"] or 0), "chg_1h": x.get("pricePercentageChange1h"), "chg_24h": x.get("pricePercentageChange24h"),
           "chg_7d": x.get("pricePercentageChange7d"), "chg_30d": x.get("pricePercentageChange30d"),
           "market_cap": float(x.get("marketCap") or 0) or float(x.get("selfReportedMarketCap") or 0), "volume_24h": float(x.get("volume24h") or 0),
           "cmc_rank": x.get("listingRank"), "age_days": x.get("age"), "on_coinbase": x["tokenSymbol"].upper() in cb, "on_binance": x["tokenSymbol"].upper() in bn}
    if rec["cmc_id"]:
        s = snap.get(rec["cmc_id"]); rec["tags"] = s[9] if s else []
        j = get(H.format(rec["cmc_id"]))
        q = (j or {}).get("data", {}).get("quotes", []) if j else []
        c = [z["quote"]["close"] for z in q if z["quote"].get("close")]
        rec["history_days"] = len(c)
        if len(c) >= 2:
            last = c[-1]
            for n in (7, 30, 90, 365):
                rec[f"ret_{n}d_hist"] = round((last / c[-1 - n] - 1) * 100, 1) if len(c) > n else None
            hi, lo = max(c[-365:]), min(c[-365:])
            rec["pct_below_1y_high"] = round((1 - last / hi) * 100, 1); rec["pct_above_1y_low"] = round((last / lo - 1) * 100, 1)
            dr = [c[i] / c[i - 1] - 1 for i in range(max(1, len(c) - 30), len(c))]
            rec["vol_30d_daily_pct"] = round((sum(d * d for d in dr) / len(dr)) ** 0.5 * 100, 2)
        time.sleep(0.3)
    rec["vol_to_mcap"] = round(rec["volume_24h"] / rec["market_cap"], 3) if rec["market_cap"] else None
    rows.append(rec)
json.dump(rows, open(f"{S}/cmc/trending_deepdive.json", "w"))
print(len(rows), sum(1 for r in rows if r["type"] == "listing"), sum(1 for r in rows if r.get("history_days")))

"""Download Coinbase Exchange public daily candles for all */USD products (cached per product; resumable). No keys."""
import json, os, sys, time, urllib.request, datetime as dt
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
H = {"User-Agent": "cryptkeep-research"}
def get(url):
    for a in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30))
        except Exception as e:
            if "404" in str(e) or "400" in str(e): return None
            time.sleep(1.5 * (a + 1))
    return None
prods = get("https://api.exchange.coinbase.com/products")
json.dump(prods, open(os.path.join(OUT, "_products.json"), "w"))
usd = sorted(p["id"] for p in prods if p["quote_currency"] == "USD")
start = int(dt.datetime(2017, 1, 1, tzinfo=dt.timezone.utc).timestamp())
end = (int(time.time()) // 86400) * 86400 - 86400
for pid in usd:
    f = os.path.join(OUT, pid + ".json")
    if os.path.exists(f): continue
    rows = {}; t = start; empty = 0
    while t <= end:
        e = min(t + 299 * 86400, end)
        r = get(f"https://api.exchange.coinbase.com/products/{pid}/candles?granularity=86400&start={dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat()}&end={dt.datetime.fromtimestamp(e, dt.timezone.utc).isoformat()}")
        if r:
            for row in r: rows[int(row[0])] = row
        t = e + 86400; time.sleep(0.2)
    json.dump(sorted(rows.values()), open(f + ".tmp", "w")); os.replace(f + ".tmp", f)
    print(pid, len(rows), flush=True)
print("ALL_DONE", flush=True)

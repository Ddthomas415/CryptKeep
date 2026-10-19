"""CoinMarketCap historical snapshots (public data-api, no key): top 1000 coins by market cap on every Sunday
2018-11-04..2026-10-04, including coins that later died. Fields kept: id, symbol, slug, cmcRank, price, volume24h,
marketCap, percentChange7d, dateAdded, tags."""
import json, os, sys, time, urllib.request, datetime as dt
from concurrent.futures import ThreadPoolExecutor
D = sys.argv[1]
U = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical?date={}&start=1&limit=1000&convertId=2781"
def get(u):
    for a in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 research"}), timeout=60) as r:
                j = json.loads(r.read())
            if j.get("data"): return j["data"]
        except Exception: pass
        time.sleep(2 + 2 * a)
    raise RuntimeError(u)
def one(day):
    p = f"{D}/{day}.json"
    if os.path.exists(p): return day, "cached"
    rows = []
    for x in get(U.format(day)):
        q = x["quotes"][0]
        rows.append([x["id"], x["symbol"], x["slug"], x["cmcRank"], q["price"], q["volume24h"], q["marketCap"], q.get("percentChange7d"), x.get("dateAdded", "")[:10], [t for t in x.get("tags", []) if not t.endswith("-portfolio")][:12]])
    json.dump(rows, open(p, "w")); return day, len(rows)
d0 = dt.date(2018, 11, 4); days = []
while d0 <= dt.date(2026, 10, 4): days.append(d0.isoformat()); d0 += dt.timedelta(days=7)
with ThreadPoolExecutor(4) as ex: res = list(ex.map(one, days))
print(len(res), sum(1 for _, n in res if n != "cached" and n < 900))

"""Binance spot daily candles (public data-api.binance.vision) for EVERY USDT pair Binance has ever listed, including delisted ones (status BREAK), to avoid survivorship bias.
Excludes stablecoins, fiat-like, wrapped and leveraged tokens. 2017-08-01 to 2026-10-09."""
import json, sys, time, urllib.request, datetime as dt
from concurrent.futures import ThreadPoolExecutor
D = sys.argv[1]; BASE = "https://data-api.binance.vision/api/v3"
def get(u):
    for a in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research"}), timeout=30) as r: return json.loads(r.read())
        except Exception: time.sleep(1 + a)
    raise RuntimeError(u)
info = get(f"{BASE}/exchangeInfo")
STABLE = {"USDC","FDUSD","TUSD","BUSD","DAI","USDP","PAX","EUR","GBP","AEUR","EURI","USDS","USD1","XUSD","BFUSD","RLUSD","PYUSD","USDE","PAXG","WBTC","WBETH","BETH","SUSD","UST","USTC","FRAX","XAUT","EURC","U","TRY","BRL","ARS","JPY","MXN","COP","ZAR","PLN","RON","UAH","CZK","USDSB","USDSOLD","BKRW","IDRT","BIDR","NGN","RUB","AUD"}
syms = [s["symbol"] for s in info["symbols"] if s["quoteAsset"] == "USDT"
        and s["symbol"].isascii() and s["symbol"].isalnum() and s["baseAsset"] not in STABLE and not (any(s["baseAsset"].endswith(x) for x in ("UP", "DOWN", "BULL", "BEAR")) and s["baseAsset"] not in ("JUP", "SUPER", "SYRUP"))]
START = int(dt.datetime(2017, 8, 1, tzinfo=dt.timezone.utc).timestamp() * 1000); END = int(dt.datetime(2026, 10, 9, tzinfo=dt.timezone.utc).timestamp() * 1000)
def one(sym):
    import os
    if os.path.exists(f"{D}/d1/{sym}.json"): return sym, len(json.load(open(f"{D}/d1/{sym}.json")))
    rows = []; t = START
    while t < END:
        k = get(f"{BASE}/klines?symbol={sym}&interval=1d&startTime={t}&endTime={END - 1}&limit=1000")
        if not k: break
        rows += [[r[0] // 1000, float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[7])] for r in k]  # ts, o, h, l, c, quote volume (USDT)
        t = k[-1][0] + 86400000
        if len(k) < 1000: break
    json.dump(rows, open(f"{D}/d1/{sym}.json", "w")); return sym, len(rows)
with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, syms))
json.dump({"symbols": len(syms), "rows": res}, open(f"{D}/fetch_summary.json", "w"))
print("done", len(syms), sum(1 for _, n in res if n >= 365 * 4))

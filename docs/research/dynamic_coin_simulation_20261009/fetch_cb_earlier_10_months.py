"""Fetch Coinbase Exchange public hourly candles for every product in universe.json.
End = 2026-10-09 00:00 UTC, 60 days back. Writes one JSON per product: [[ts_s, open, high, low, close, volume], ...] ascending."""
import json, sys, time, threading, urllib.request, urllib.error, datetime as dt
from concurrent.futures import ThreadPoolExecutor
D = sys.argv[1]
END = int(dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc).timestamp()); START = int(dt.datetime(2025, 10, 9, tzinfo=dt.timezone.utc).timestamp())
uni = json.load(open(f"{D}/universe.json"))
lock = threading.Lock(); last = [0.0]
def get(url):
    for attempt in range(8):
        with lock:
            wait = last[0] + 0.12 - time.time()
            if wait > 0: time.sleep(wait)
            last[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research"}), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(1 + attempt); continue
            if e.code == 404: return None
            time.sleep(1 + attempt)
        except Exception:
            time.sleep(1 + attempt)
    raise RuntimeError("failed " + url)
def one(pid):
    rows = {}
    t = START
    while t < END:
        e = min(END, t + 300 * 3600)
        s_iso = dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat().replace("+00:00", "Z")
        e_iso = dt.datetime.fromtimestamp(e, dt.timezone.utc).isoformat().replace("+00:00", "Z")
        data = get(f"https://api.exchange.coinbase.com/products/{pid}/candles?granularity=3600&start={s_iso}&end={e_iso}") or []
        for c in data:
            if START <= c[0] < END: rows[c[0]] = [c[0], c[3], c[2], c[1], c[4], c[5]]
        t = e
    out = [rows[k] for k in sorted(rows)]
    json.dump(out, open(f"{D}/h1/{pid}.json", "w"))
    return pid, len(out)
with ThreadPoolExecutor(6) as ex:
    res = list(ex.map(one, uni))
json.dump(res, open(f"{D}/fetch_summary.json", "w"))
print("done", len(res), sum(1 for _, n in res if n >= 1300))

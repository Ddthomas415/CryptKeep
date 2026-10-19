"""Download Coinbase Exchange public daily candles for all */USD products. No keys. Resumable.
Failure handling (review 2026-10-12):
 - Every HTTP error, including 400/404, and every exhausted retry is recorded as an UNRESOLVED failed window. It is never
   treated as "no trading". The only explicit "no data" evidence is a successful (HTTP 200) empty response.
 - A product is written as complete only if every window succeeded. Otherwise it is saved as <pid>.partial.json with its
   failed windows and retried on the next run.
 - A saved file is skipped on rerun only if _manifest.json marks it complete AND its sha256 still matches. Files without
   a manifest entry (e.g. from the first, unvalidated download) are downloaded again.
The first version is kept as fetch_v1_original.py."""
import hashlib, json, os, sys, time, urllib.error, urllib.request, datetime as dt
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
H = {"User-Agent": "cryptkeep-research"}
MAN = os.path.join(OUT, "_manifest.json")
man = json.load(open(MAN)) if os.path.exists(MAN) else {}
def save_man():
    json.dump(man, open(MAN + ".tmp", "w"), indent=0); os.replace(MAN + ".tmp", MAN)
def get(url):
    """Return (True, data) on HTTP 200, else (False, reason). Retries transient failures; nothing is mapped to 'no data'."""
    last = "unknown"
    for a in range(5):
        try:
            return True, json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (400, 404): break        # not transient; still a failure, not evidence of no trading
        except Exception as e:
            last = type(e).__name__
        time.sleep(1.5 * (a + 1))
    return False, last
ok, prods = get("https://api.exchange.coinbase.com/products")
if not ok: raise SystemExit(f"product list unavailable: {prods}")
json.dump(prods, open(os.path.join(OUT, "_products.json"), "w"))
usd = sorted(p["id"] for p in prods if p["quote_currency"] == "USD")
start = int(dt.datetime(2017, 1, 1, tzinfo=dt.timezone.utc).timestamp())
end = (int(time.time()) // 86400) * 86400 - 86400
sha = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
for pid in usd:
    f = os.path.join(OUT, pid + ".json")
    m = man.get(pid)
    if m and m.get("complete") and os.path.exists(f) and sha(f) == m.get("sha256"): continue
    rows = {}; t = start; failed = []
    while t <= end:
        e = min(t + 299 * 86400, end)
        ok, r = get(f"https://api.exchange.coinbase.com/products/{pid}/candles?granularity=86400&start={dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat()}&end={dt.datetime.fromtimestamp(e, dt.timezone.utc).isoformat()}")
        if ok:
            for row in r: rows[int(row[0])] = row
        else:
            failed.append([t, e, r])
        t = e + 86400; time.sleep(0.2)
    if failed:
        json.dump({"rows": sorted(rows.values()), "failed_windows": failed}, open(os.path.join(OUT, pid + ".partial.json"), "w"))
        man[pid] = {"complete": False, "failed_windows": failed, "rows": len(rows)}; save_man()
        print(pid, "INCOMPLETE", len(failed), "windows", flush=True); continue
    json.dump(sorted(rows.values()), open(f + ".tmp", "w")); os.replace(f + ".tmp", f)
    man[pid] = {"complete": True, "sha256": sha(f), "rows": len(rows), "range": [start, end]}; save_man()
    print(pid, len(rows), flush=True)
print("ALL_DONE", "incomplete:", sorted(p for p, m in man.items() if not m.get("complete")), flush=True)

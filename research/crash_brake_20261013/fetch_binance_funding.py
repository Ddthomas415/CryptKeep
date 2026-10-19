"""One-off READ-ONLY download of Binance USDT-M perpetual funding-rate history (public endpoint, no keys).
Runs on the Hetzner host via `ssh host 'python3 -' < this_file > local.jsonl`: it writes NOTHING on the server, only to stdout.
Every failure is emitted as an explicit error record (never silently skipped), and the script exits non-zero on any failure."""
import json, sys, time, urllib.request, urllib.error, datetime as dt, socket
BASE = "https://fapi.binance.com/fapi/v1/fundingRate"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
START = int(dt.datetime(2019, 9, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
now = int(time.time() * 1000)
out = sys.stdout; failed = False
out.write(json.dumps({"type": "meta", "host": socket.gethostname(), "fetched_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "endpoint": BASE}) + "\n")
for sym in SYMBOLS:
    t = START; n = 0
    while t < now:
        url = f"{BASE}?symbol={sym}&startTime={t}&limit=1000"
        rows = None
        for attempt in range(4):
            try:
                rows = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "cryptkeep-research"}), timeout=30)); break
            except Exception as e:
                err = f"{type(e).__name__} {getattr(e, 'code', '')}"
                time.sleep(2 * (attempt + 1))
        if rows is None:
            out.write(json.dumps({"type": "error", "symbol": sym, "startTime": t, "error": err}) + "\n"); failed = True; break
        if not rows: break
        for r in rows:
            out.write(json.dumps({"type": "funding", "symbol": sym, "fundingTime": int(r["fundingTime"]), "fundingRate": r["fundingRate"], "markPrice": r.get("markPrice")}) + "\n"); n += 1
        last = int(rows[-1]["fundingTime"])
        if last + 1 <= t: break
        t = last + 1
        time.sleep(0.3)
    out.write(json.dumps({"type": "summary", "symbol": sym, "rows": n}) + "\n")
out.flush()
sys.exit(1 if failed else 0)

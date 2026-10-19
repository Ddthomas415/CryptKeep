"""ENTR-CB-1 Step B: first and last daily candle for each Coinbase product in the frozen identity map.

Frozen preregistration (sha256 a7fb3662...), section 4, Step B: "find the first and last daily candle
by binary search over 300-candle windows (about 6 requests per product), at most 3 requests per
second. Raw responses saved and hashed; no other data downloaded."

Public Coinbase Exchange candle endpoint only, no credentials. Every response body is saved byte for
byte with its SHA256, HTTP status, URL and UTC send/receive times (requests.jsonl, one line per
request, append-only). Hard cap on total requests; at most 3 requests per second; resumable across
invocations (state.json, written atomically) with a per-invocation time budget so each invocation
fits a short shell call. results.json is written once, only when every product is done.

Windows: 300 daily buckets each, start T00:00:00Z to (start + 299 days) T00:00:00Z, the form Step A
showed returns 300 candles with both end days included (research/coinbase_listing_probe_20261019,
requests 04, 10, 11). Windows run back to back from 2018-12-15 to the first invocation's UTC date.

Search per product:
- last: step back from the newest window until a window has candles ("anchor"); its latest candle
  is the last candle. Exact even if trading had gaps.
- first: binary search over windows 0..anchor for the earliest window with candles; its earliest
  candle is the first candle. Exact if the product traded at least once in every window between
  listing and the anchor. KNOWN LIMIT: a trading gap covering a whole 300-day window after listing
  can make the search return a later first date; every window queried and its candle count is
  recorded so this can be checked.
- first == 2018-12-15 means "on or before 2018-12-15" (flag first_at_search_start).
Retries: network error, HTTP 429 or 5xx are retried up to twice (2 s, then 6 s); each attempt is a
logged, counted request. Any other non-200 status, or a body that is not a JSON list, marks the
product as failed; the listing builder turns a failed product into "unknown".
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

BASE = "https://api.exchange.coinbase.com"
START = date(2018, 12, 15)
WINDOW_DAYS = 300
MIN_INTERVAL = 0.34  # seconds between request starts: under 3 per second
RETRY_WAITS = (2.0, 6.0)
SCHEMA_STATE = "entr-cb1-stepB-fetch-state-v1"
SCHEMA_RESULTS = "entr-cb1-stepB-candle-dates-v1"


def now():
    return datetime.now(timezone.utc).isoformat()


def windows(end_day):
    out, start = [], START
    while start <= end_day:
        out.append((start, min(start + timedelta(days=WINDOW_DAYS - 1), end_day)))
        start += timedelta(days=WINDOW_DAYS)
    return out


def candle_url(product, win):
    return (f"{BASE}/products/{product}/candles?granularity=86400"
            f"&start={win[0].isoformat()}T00:00:00Z&end={win[1].isoformat()}T00:00:00Z")


def http_get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "cryptkeep-research-stepB/1",
                                                   "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return None, f"NETWORK_ERROR: {error}".encode()


class RequestCapReached(RuntimeError):
    pass


class ProductFailed(RuntimeError):
    pass


def write_json_atomic(path, doc):
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w") as stream:
        json.dump(doc, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


class Fetcher:
    def __init__(self, out, state, max_requests, get=http_get, sleep=time.sleep, clock=time.monotonic):
        self.out, self.state, self.max_requests = out, state, max_requests
        self.get, self.sleep, self.clock = get, sleep, clock
        self.last_start = None

    def _one(self, product, win):
        if self.state["requests"] >= self.max_requests:
            raise RequestCapReached(f"request cap {self.max_requests} reached")
        if self.last_start is not None:
            wait = MIN_INTERVAL - (self.clock() - self.last_start)
            if wait > 0:
                self.sleep(wait)
        self.last_start = self.clock()
        self.state["requests"] += 1
        n = self.state["requests"]
        url = candle_url(product, win)
        sent = now()
        status, body = self.get(url)
        name = f"{n:05d}_{product}_{win[0].isoformat()}.json"
        with open(self.out / "raw" / name, "xb") as stream:
            stream.write(body)
        record = {"n": n, "product": product, "window": [win[0].isoformat(), win[1].isoformat()],
                  "url": url, "http_status": status, "sent_utc": sent, "received_utc": now(),
                  "file": "raw/" + name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
        with open(self.out / "requests.jsonl", "a") as log:
            log.write(json.dumps(record, sort_keys=True) + "\n")
        return status, body

    def window_days(self, product, win, trail):
        """Sorted candle days in one window; retries transient failures; raises ProductFailed."""
        for attempt in range(len(RETRY_WAITS) + 1):
            status, body = self._one(product, win)
            if status is None or status == 429 or (status is not None and status >= 500):
                if attempt < len(RETRY_WAITS):
                    self.sleep(RETRY_WAITS[attempt])
                    continue
                raise ProductFailed(f"http_{status}_after_retries")
            if status != 200:
                raise ProductFailed(f"http_{status}")
            try:
                rows = json.loads(body)
                if not isinstance(rows, list) or not all(isinstance(r, list) and r for r in rows):
                    raise ValueError("not a list of candle rows")
                days = sorted(datetime.fromtimestamp(int(r[0]), timezone.utc).date() for r in rows)
            except (ValueError, TypeError, OverflowError, OSError):
                raise ProductFailed("bad_body")
            if any(d < win[0] or d > win[1] for d in days):
                raise ProductFailed("candle_outside_window")
            trail.append([win[0].isoformat(), len(days)])
            return days
        raise AssertionError("unreachable")

    def product(self, product, wins):
        """{first, last, first_at_search_start, windows_queried, error} for one product."""
        trail = []
        try:
            anchor, last_days = None, []
            for k in range(len(wins) - 1, -1, -1):
                days = self.window_days(product, wins[k], trail)
                if days:
                    anchor, last_days = k, days
                    break
            if anchor is None:
                return {"first": None, "last": None, "first_at_search_start": False,
                        "windows_queried": trail, "error": None}
            lo, hi, first_days = 0, anchor, last_days
            while lo < hi:
                mid = (lo + hi) // 2
                days = self.window_days(product, wins[mid], trail)
                if days:
                    hi, first_days = mid, days
                else:
                    lo = mid + 1
        except ProductFailed as failure:
            return {"first": None, "last": None, "first_at_search_start": False,
                    "windows_queried": trail, "error": str(failure)}
        return {"first": first_days[0].isoformat(), "last": last_days[-1].isoformat(),
                "first_at_search_start": first_days[0] == START, "windows_queried": trail, "error": None}


def target_products(identity_map, products):
    """Products to fetch: every USD/USDC/USDT product of every mapped record, with /products status."""
    status = {p["id"]: p["status"] for p in products}
    todo = sorted({p["id"] for r in identity_map["records"].values() if r["status"] == "mapped"
                   for p in r["products"]})
    missing = [p for p in todo if p not in status]
    if missing:
        raise SystemExit(f"products missing from /products: {missing}")
    return todo, {p: status[p] for p in todo}


def logged_request_count(out):
    path = out / "requests.jsonl"
    if not path.exists():
        return 0
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if json.loads(line)["n"] != i:
            raise SystemExit("requests.jsonl is not a contiguous log")
    return len(lines)


def main(argv=None, get=http_get, sleep=time.sleep, clock=time.monotonic, today=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--map-sha256", required=True)
    parser.add_argument("--products", type=Path, required=True)
    parser.add_argument("--products-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-requests", type=int, default=1600)
    parser.add_argument("--budget-seconds", type=float, default=120)
    args = parser.parse_args(argv)
    began = clock()
    for path, expected in ((args.map, args.map_sha256), (args.products, args.products_sha256)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"pinned input changed or unexpected: {path}")
    out = args.output_dir
    state_path = out / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if (state.get("schema") != SCHEMA_STATE or state["map_sha256"] != args.map_sha256
                or state["products_sha256"] != args.products_sha256):
            raise SystemExit("state.json does not match the pinned inputs")
    else:
        out.mkdir(parents=True, exist_ok=True)
        if any(out.iterdir()):
            raise SystemExit("output directory is not empty and has no state.json")
        (out / "raw").mkdir()
        todo, status = target_products(json.loads(args.map.read_bytes()), json.loads(args.products.read_bytes()))
        end_day = today or datetime.now(timezone.utc).date()
        state = {"schema": SCHEMA_STATE, "end_day": end_day.isoformat(), "search_start": START.isoformat(),
                 "window_days": WINDOW_DAYS, "map_sha256": args.map_sha256,
                 "products_sha256": args.products_sha256, "max_requests": args.max_requests,
                 "requests": 0, "todo": todo, "product_status": status, "done": {}, "started_utc": now()}
        write_json_atomic(state_path, state)
    state["requests"] = logged_request_count(out)  # the log, not state.json, is the count of record
    for raw in sorted((out / "raw").iterdir()):  # body saved but process stopped before its log line
        if raw.name[:5].isdigit() and int(raw.name[:5]) > state["requests"]:
            raw.rename(raw.with_name("unlogged_" + raw.name))
            state.setdefault("unlogged_files", []).append("raw/unlogged_" + raw.name)
    wins = windows(date.fromisoformat(state["end_day"]))
    fetcher = Fetcher(out, state, args.max_requests, get=get, sleep=sleep, clock=clock)
    stopped = None
    try:
        for product in state["todo"]:
            if product in state["done"]:
                continue
            if clock() - began > args.budget_seconds:
                stopped = "budget"
                break
            result = fetcher.product(product, wins)
            result["product_status"] = state["product_status"][product]
            state["done"][product] = result
            write_json_atomic(state_path, state)
    except RequestCapReached:
        stopped = "request_cap"
    finally:
        write_json_atomic(state_path, state)
    remaining = [p for p in state["todo"] if p not in state["done"]]
    if not remaining and not (out / "results.json").exists():
        doc = {"schema": SCHEMA_RESULTS, "end_day": state["end_day"], "search_start": state["search_start"],
               "window_days": state["window_days"], "map_sha256": state["map_sha256"],
               "products_sha256": state["products_sha256"], "requests": state["requests"],
               "products": state["done"], "written_utc": now()}
        with open(out / "results.json", "x") as stream:
            json.dump(doc, stream, indent=2, sort_keys=True)
    summary = {"requests_total": state["requests"], "products_done": len(state["done"]),
               "products_remaining": len(remaining), "stopped": stopped,
               "failed": sorted(p for p, r in state["done"].items() if r["error"])}
    print(json.dumps(summary))
    return summary


if __name__ == "__main__":
    main()

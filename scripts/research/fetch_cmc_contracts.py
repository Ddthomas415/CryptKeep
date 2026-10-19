"""ENTR-CB-1 identity map v3: CoinMarketCap contract addresses per CMC ID (operator-approved 2026-10-19).

Frozen preregistration (sha256 a7fb3662...) section 3.1 requires matching on "CMC name + slug + contract
address where one exists". This saves CMC's public coin-detail response for each ID in a pinned list
(one GET per ID, no key, no account), at most one request per second, with every body saved byte for
byte and logged with SHA256, HTTP status, URL and UTC times (requests.jsonl, append-only). Resumable:
an ID with a logged HTTP 200 body is not fetched again. Hard cap on total requests.

`--parse` writes cmc_contracts.json (schema "entr-cb1-cmc-contracts-v1") from the saved bodies only:
for each ID, the contract addresses CMC lists across platforms, plus the returned id, symbol and slug.
A returned id that differs from the requested one, or an unreadable body, is listed under "problems"
and that ID gets no record; a changed slug or ticker (CMC renames coins) is listed under
"renamed_since_list" and kept, because the CMC ID is the identity.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

URL = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail?id={}"
MIN_INTERVAL = 1.05
RETRY_WAITS = (5.0, 15.0)
SCHEMA = "entr-cb1-cmc-contracts-v1"


def now():
    return datetime.now(timezone.utc).isoformat()


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


def read_log(out):
    path = out / "requests.jsonl"
    lines = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    if [l["n"] for l in lines] != list(range(1, len(lines) + 1)):
        raise SystemExit("requests.jsonl is not a contiguous log")
    return lines


def fetch(ids, out, max_requests, budget, get=http_get, sleep=time.sleep, clock=time.monotonic):
    began = clock()
    (out / "raw").mkdir(parents=True, exist_ok=True)
    log = read_log(out)
    done = {l["cmc_id"] for l in log if l["http_status"] == 200}
    n, last_start, stopped = len(log), None, None
    for cmc_id in ids:
        if cmc_id in done:
            continue
        if clock() - began > budget:
            stopped = "budget"
            break
        for attempt in range(len(RETRY_WAITS) + 1):
            if n >= max_requests:
                return {"requests_total": n, "stopped": "request_cap"}
            if last_start is not None and MIN_INTERVAL - (clock() - last_start) > 0:
                sleep(MIN_INTERVAL - (clock() - last_start))
            last_start = clock()
            n += 1
            url, sent = URL.format(cmc_id), now()
            status, body = get(url)
            name = f"{n:04d}_{cmc_id}.json"
            with open(out / "raw" / name, "xb") as stream:
                stream.write(body)
            with open(out / "requests.jsonl", "a") as stream:
                stream.write(json.dumps({"n": n, "cmc_id": cmc_id, "url": url, "http_status": status,
                                         "sent_utc": sent, "received_utc": now(), "file": "raw/" + name,
                                         "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()},
                                        sort_keys=True) + "\n")
            if status == 200:
                break
            if status is None or status == 429 or status >= 500:
                if attempt < len(RETRY_WAITS):
                    sleep(RETRY_WAITS[attempt])
                    continue
            break
    remaining = [i for i in ids if i not in {l["cmc_id"] for l in read_log(out) if l["http_status"] == 200}]
    return {"requests_total": n, "remaining": len(remaining), "stopped": stopped}


def extract(body):
    """(id, symbol, slug, contracts, platforms) from one saved detail body."""
    doc = json.loads(body)
    if str((doc.get("status") or {}).get("error_code", "0")) != "0":
        raise ValueError(f"CMC error {doc['status']}")
    data = doc["data"]
    platforms = []
    for p in data.get("platforms") or []:
        address = (p.get("contractAddress") or "").strip()
        if address:
            platforms.append({"platform": p.get("contractPlatform") or p.get("contractChainName") or "",
                              "address": address})
    return int(data["id"]), data["symbol"], data["slug"], sorted({p["address"] for p in platforms}), platforms


def parse(rows, out):
    log = read_log(out)
    latest = {}
    for line in log:
        if line["http_status"] == 200:
            latest[line["cmc_id"]] = line
    assets, problems, renamed = {}, [], {}
    for row in rows:
        cmc_id = row["cmc_id"]
        line = latest.get(cmc_id)
        if line is None:
            problems.append(f"{cmc_id}: no HTTP 200 body")
            continue
        body = (out / line["file"]).read_bytes()
        if hashlib.sha256(body).hexdigest() != line["sha256"]:
            raise SystemExit(f"saved body changed: {line['file']}")
        try:
            got_id, symbol, slug, contracts, platforms = extract(body)
        except (ValueError, KeyError, TypeError) as error:
            problems.append(f"{cmc_id}: unreadable body ({error})")
            continue
        if got_id != int(cmc_id):
            problems.append(f"{cmc_id}: CMC returned id {got_id}")
            continue
        if slug != row["slug"] or symbol.upper() != row["symbol"].upper():
            # CMC renames slugs and tickers over time (e.g. render-token -> render); the ID is the identity.
            renamed[cmc_id] = {"list_symbol": row["symbol"], "list_slug": row["slug"], "cmc_symbol": symbol, "cmc_slug": slug}
        assets[cmc_id] = {"contracts": contracts, "platforms": platforms, "cmc_symbol": symbol, "cmc_slug": slug,
                          "source_file": line["file"], "source_sha256": line["sha256"]}
    return {"schema": SCHEMA, "source": URL, "assets": assets, "problems": problems, "renamed_since_list": renamed}


def main(argv=None, get=http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--ids-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-requests", type=int, default=230)
    parser.add_argument("--budget-seconds", type=float, default=140)
    parser.add_argument("--only", default="", help="comma-separated subset of IDs (probe)")
    parser.add_argument("--parse", action="store_true")
    args = parser.parse_args(argv)
    if hashlib.sha256(args.ids.read_bytes()).hexdigest() != args.ids_sha256:
        raise SystemExit("pinned ID list changed or unexpected")
    rows = list(csv.DictReader(open(args.ids)))
    if args.parse:
        doc = parse(rows, args.output_dir)
        doc["ids_sha256"] = args.ids_sha256
        with open(args.output_dir / "cmc_contracts.json", "x") as stream:
            json.dump(doc, stream, indent=2, sort_keys=True)
            stream.write("\n")
        summary = {"assets": len(doc["assets"]), "with_contracts": sum(bool(a["contracts"]) for a in doc["assets"].values()),
                   "problems": doc["problems"]}
    else:
        ids = [r["cmc_id"] for r in rows]
        if args.only:
            subset = args.only.split(",")
            if not set(subset) <= set(ids):
                raise SystemExit("--only names IDs outside the pinned list")
            ids = [i for i in ids if i in subset]
        summary = fetch(ids, args.output_dir, args.max_requests, args.budget_seconds, get=get, sleep=sleep)
    print(json.dumps(summary))
    return summary


if __name__ == "__main__":
    main()

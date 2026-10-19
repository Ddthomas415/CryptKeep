"""ENTR-CB-1 Step A probe: at most 20 public Coinbase Exchange requests, raw responses saved.

Frozen preregistration: docs/research/coinbase_tradable_entrants_20261019/PREREGISTRATION_DRAFT.md
(sha256 a7fb3662...), section 4, Step A. Public endpoints only, no credentials, no account access.
Each response body is saved byte for byte with its SHA256, HTTP status, URL and UTC send/receive
times; the manifest is written last. Refuses to reuse an existing output directory.

Questions this probe answers (evaluation happens separately, from the saved files):
1. Does /products return delisted products?
2. Does the daily-candle endpoint return history for a delisted product?
3. Does the first daily candle of a currently listed entrant (SEI-USD) mark its listing?
4. Is HEX absent from Coinbase Exchange?
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

BASE = "https://api.exchange.coinbase.com"
MAX_REQUESTS = 20
WINDOWS = (("2019-01-01", "2019-10-27"), ("2021-01-01", "2021-10-27"), ("2023-01-01", "2023-10-27"))


def now():
    return datetime.now(timezone.utc).isoformat()


class Prober:
    def __init__(self, out):
        self.out, self.count, self.records = out, 0, []

    def get(self, path, label):
        if self.count >= MAX_REQUESTS:
            raise SystemExit("request cap reached; stopping")
        self.count += 1
        url = BASE + path
        request = urllib.request.Request(url, headers={"User-Agent": "cryptkeep-research-probe/1",
                                                       "Accept": "application/json"})
        sent = now()
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                status, body = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, body = error.code, error.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            status, body = None, f"NETWORK_ERROR: {error}".encode()
        received = now()
        name = f"{self.count:02d}_{label}.json"
        with open(self.out / name, "xb") as stream:
            stream.write(body)
        self.records.append({"n": self.count, "label": label, "url": url, "http_status": status,
                             "sent_utc": sent, "received_utc": received, "file": name,
                             "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        time.sleep(0.5)
        return status, body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    probe = Prober(args.output)
    status, body = probe.get("/products", "products")
    delisted = []
    if status == 200:
        try:
            products = json.loads(body)
            delisted = sorted(p["id"] for p in products
                              if isinstance(p, dict) and p.get("status") == "delisted")[:2]
        except (ValueError, KeyError, TypeError):
            delisted = []
    for product in delisted:
        for start, end in WINDOWS:
            probe.get(f"/products/{product}/candles?granularity=86400&start={start}T00:00:00Z"
                      f"&end={end}T00:00:00Z", f"candles_{product}_{start[:4]}")
    probe.get("/products/SEI-USD/candles?granularity=86400&start=2023-08-01T00:00:00Z"
              "&end=2024-05-26T00:00:00Z", "candles_SEI-USD_2023")
    probe.get("/products/HEX-USD", "product_HEX-USD")
    manifest = {"schema": "entr-cb1-probe-v1", "base": BASE, "max_requests": MAX_REQUESTS,
                "requests_made": probe.count, "delisted_products_probed": delisted,
                "records": probe.records, "written_utc": now()}
    with open(args.output / "manifest.json", "x") as stream:
        json.dump(manifest, stream, indent=2)
    print(json.dumps({"requests_made": probe.count, "delisted_products_probed": delisted,
                      "statuses": [(r["label"], r["http_status"], r["bytes"]) for r in probe.records]}))


if __name__ == "__main__":
    main()

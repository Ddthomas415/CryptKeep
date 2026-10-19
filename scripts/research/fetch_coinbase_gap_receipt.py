"""Bounded public candle retrieval; preserve frozen files, no orders or keys."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

OUT = Path("research/research_corrections_20261009/coinbase_gap_20260508_v1.json")
PRODUCTS = ("TON-USD", "VVV-USD", "BTC-USD", "BCH-USD", "ZEC-USD", "JTO-USD", "FARTCOIN-USD")


def main():
    if OUT.exists():
        raise FileExistsError("receipt exists; no overwrite")
    records = []
    query = urllib.parse.urlencode({"start": "2026-05-08T01:00:00Z",
                                   "end": "2026-05-08T08:00:00Z", "granularity": 3600})
    for product in PRODUCTS:
        url = f"https://api.exchange.coinbase.com/products/{product}/candles?{query}"
        received = dt.datetime.now(dt.timezone.utc).isoformat()
        request = urllib.request.Request(url, headers={"User-Agent": "CryptKeep-research-gap-repair"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
            records.append({"product": product, "url": url, "request_started": received,
                            "received": dt.datetime.now(dt.timezone.utc).isoformat(),
                            "raw_response": raw.decode(), "response_sha256": hashlib.sha256(raw).hexdigest()})
        except Exception as exc:
            records.append({"product": product, "url": url, "error": str(exc)})
        time.sleep(.4)
    result = {"artifact_type": "public_gap_retrieval_receipt_not_original_archive",
              "candle_schema": "Coinbase time,low,high,open,close,volume",
              "target": "2026-05-08 02:00 through 06:00 UTC",
              "not_fresh_holdout": True, "records": records}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x") as stream:
        json.dump(result, stream, allow_nan=False)
    print(json.dumps({"file": str(OUT), "requests": len(records),
                      "errors": sum("error" in r for r in records)}))


if __name__ == "__main__":
    main()

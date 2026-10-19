"""Two bounded public-book observations; no fees, fills, scoring or orders."""
from datetime import datetime, timezone
import base64
import hashlib
import json
import time

import requests


URL = "https://api.coinbase.com/api/v3/brokerage/market/product_book"


def capture(product, session, clock=time):
    if product not in ("BTC-USD", "ETH-USD"):
        raise ValueError("unsupported_product")
    requested = clock.time_ns()
    started = clock.monotonic_ns()
    response = session.get(URL, params={"product_id": product, "limit": 50},
                           timeout=15, allow_redirects=False)
    received = clock.time_ns()
    duration = clock.monotonic_ns() - started
    if response.status_code != 200:
        raise ValueError("public_book_request_failed")
    raw = response.content
    payload = response.json()
    book = payload.get("pricebook", {})
    if (book.get("product_id") != product or not book.get("bids")
            or not book.get("asks")):
        raise ValueError("book_identity_or_sides_missing")
    return {"product_id": product, "request_utc_ns": requested,
            "receive_utc_ns": received, "request_duration_ns": duration,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "raw_response_base64": base64.b64encode(raw).decode("ascii"),
            "raw_payload": payload,
            "clock_uncertainty": "UNVERIFIED", "arrival_alignment": "UNVERIFIED",
            "execution_authority": False, "scoring_authorized": False}


def observe(product, session, clock=time):
    initial = capture(product, session, clock)
    # Receipt anchors the declared local target; neither proves exchange freshness.
    target = initial["receive_utc_ns"] + 2_000_000_000
    clock.sleep(2)
    arrival = capture(product, session, clock)
    return {"kind": "PUBLIC_ARRIVAL_OBSERVATION_NOT_EXECUTION_PROOF",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "local_target_utc_ns": target, "target_basis": "T0_local_receipt_plus_2s",
            "initial": initial, "arrival": arrival,
            "orders_submitted": False, "scoring_authorized": False}


def main():
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", required=True, choices=("BTC-USD", "ETH-USD"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.output.open("x") as output:
        with requests.Session() as session:
            session.trust_env = False
            result = observe(args.product, session)
        json.dump(result, output, indent=2, allow_nan=False)
    print(json.dumps({"status": "OBSERVATIONS_SAVED_NOT_QUALIFIED",
                      "product": args.product, "scoring_authorized": False}))


if __name__ == "__main__":
    main()

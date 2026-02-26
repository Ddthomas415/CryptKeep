#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


# CBP_BOOTSTRAP: ensure repo root on sys.path so `import services` works when running scripts directly
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import hmac
import hashlib
import json
import time
import urllib.request

from services.security.secret_store import get_evidence_hmac_secret

def compute_sig(secret: str, ts: str, body: bytes) -> str:
    msg = (str(ts) + ".").encode("utf-8") + body
    mac = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return "sha256=" + mac

def main():
    ap = argparse.ArgumentParser(description="Send an evidence webhook payload with HMAC signature.")
    ap.add_argument("--url", default="http://127.0.0.1:8787/evidence")
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--secret", help="Optional. If omitted, read from OS keyring/env.")
    ap.add_argument("--payload", help="Inline JSON string (single object or list).")
    ap.add_argument("--symbol", default="BTC/USD")
    ap.add_argument("--side", default="buy", choices=["buy","sell","long","short","flat"])
    ap.add_argument("--venue", default="coinbase")
    ap.add_argument("--confidence", type=float, default=0.7)
    ap.add_argument("--horizon-sec", type=int, default=3600)
    ap.add_argument("--notes", default="sender_test")
    args = ap.parse_args()

    secret = (args.secret or "").strip() or get_evidence_hmac_secret(args.source_id)
    if not secret:
        raise SystemExit("No secret found. Use --secret or store it via set_evidence_webhook_secret.py")

    if args.payload:
        payload_obj = json.loads(args.payload)
    else:
        payload_obj = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "symbol": args.symbol,
            "side": args.side,
            "venue": args.venue,
            "confidence": float(args.confidence),
            "horizon_sec": int(args.horizon_sec),
            "notes": args.notes,
        }

    body = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
    ts = str(int(time.time()))
    sig = compute_sig(secret, ts, body)

    req = urllib.request.Request(args.url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-CBP-Source-Id", args.source_id)
    req.add_header("X-CBP-Timestamp", ts)
    req.add_header("X-CBP-Signature", sig)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    main()

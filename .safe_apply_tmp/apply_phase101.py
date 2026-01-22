# apply_phase101.py – Phase 101 launcher (sender + test + bind guard)
from pathlib import Path
import re

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"Written/Updated: {path}")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        print(f"Cannot patch - file missing: {path}")
        return
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
    else:
        print(f"No changes needed: {path}")

# 1) Sender helper script
write("scripts/send_evidence_webhook.py", r'''#!/usr/bin/env python3
from __future__ import annotations
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
    ap.add_argument("--symbol", default="BTC/USDT")
    ap.add_argument("--side", default="buy", choices=["buy","sell","long","short","flat"])
    ap.add_argument("--venue", default="binance")
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
''')

# 2) Roundtrip test script
write("scripts/test_evidence_webhook_roundtrip.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
import time

def run(cmd):
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)

def main():
    source_id = "trader1"
    url = "http://127.0.0.1:8787/evidence"

    print("[roundtrip] Sending valid payload...")
    rc1 = run([
        sys.executable, "scripts/send_evidence_webhook.py",
        "--url", url,
        "--source-id", source_id,
        "--symbol", "BTC/USDT",
        "--side", "buy",
        "--venue", "binance",
        "--notes", "roundtrip_valid"
    ])
    time.sleep(1)

    print("[roundtrip] Sending invalid payload (should quarantine)...")
    bad_payload = '[{"ts":"2025-01-01T00:00:00Z","symbol":"INVALID!!!!","side":"buy"}]'
    rc2 = run([
        sys.executable, "scripts/send_evidence_webhook.py",
        "--url", url,
        "--source-id", source_id,
        "--payload", bad_payload
    ])

    print(f"Finished. Valid rc={rc1}, Invalid rc={rc2}")
    return 0 if rc1 == 0 and rc2 == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
''')

# 3) Patch webhook_server.py to add bind guard
def patch_webhook_server(t: str) -> str:
    if "allow_public_bind" in t and "public_bind_refused" in t:
        return t

    # Add config field
    t = t.replace(
        '"max_skew_sec": int(wh.get("max_skew_sec", 120) or 120),',
        '"max_skew_sec": int(wh.get("max_skew_sec", 120) or 120),\n        "allow_public_bind": bool(wh.get("allow_public_bind", False)),'
    )

    guard = r'''def _bind_guard(cfg: dict) -> None:
    host = str(cfg.get("host", "")).strip()
    allow = bool(cfg.get("allow_public_bind", False))
    if host in ("0.0.0.0", "::", "[::]") and not allow:
        raise RuntimeError("public_bind_refused: set evidence.webhook.allow_public_bind=true to bind on all interfaces")
'''

    if "_bind_guard" not in t:
        t = t.replace("def _compute_sig(", guard + "\n\ndef _compute_sig(", 1)

    if "_bind_guard(cfg)" not in t:
        t = t.replace("def run():\n    cfg = _cfg()\n", "def run():\n    cfg = _cfg()\n    _bind_guard(cfg)\n", 1)

    return t

patch("services/evidence/webhook_server.py", patch_webhook_server)

print("\nPhase 101 applied successfully.")
print("Next steps:")
print("  1. Make scripts executable (optional):")
print("     chmod +x scripts/send_evidence_webhook.py scripts/test_evidence_webhook_roundtrip.py")
print("  2. Ensure webhook server is running in another terminal:")
print("     python3 scripts/run_evidence_webhook.py")
print("  3. Run the roundtrip test:")
print("     python3 scripts/test_evidence_webhook_roundtrip.py")
print("  4. Or send single messages:")
print("     python3 scripts/send_evidence_webhook.py --source-id trader1 --notes 'manual test'")
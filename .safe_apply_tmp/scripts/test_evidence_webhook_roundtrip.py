#!/usr/bin/env python3
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

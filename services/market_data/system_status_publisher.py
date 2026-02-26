from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from services.os.app_paths import runtime_dir, ensure_dirs
from services.market_data.symbol_router import normalize_venue, normalize_symbol, map_symbol
from services.security.exchange_factory import make_exchange

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
SNAPSHOTS = runtime_dir() / "snapshots"
STOP_FILE = FLAGS / "tick_publisher.stop"
LOCK_FILE = LOCKS / "tick_publisher.lock"
STATUS_FILE = SNAPSHOTS / "system_status.latest.json"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _acquire_lock() -> bool:
    LOCKS.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        return False
    LOCK_FILE.write_text(json.dumps({"pid": os.getpid(), "ts": _now_iso()}, indent=2) + "\n", encoding="utf-8")
    return True

def _release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(_now_iso() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}

def fetch_status() -> dict:
    status = {
        "ts": _now_iso(),
        "ts_ms": int(time.time() * 1000),
        "venues": {}
    }
    venues = [v.strip() for v in (os.environ.get("CBP_VENUE") or "coinbase").split(",") if v.strip()]
    venues = [str(v).lower().strip() for v in venues]
    if not (os.environ.get("CBP_VENUE") or "").lower().startswith("binance"):
        venues = [v for v in venues if not v.startswith("binance")]

    symbol = "BTC/USD"
    for v in venues:
        print(f"\n=== Fetching from {v} ===")
        try:
            ex = make_exchange(v, {"apiKey": None, "secret": None}, enable_rate_limit=True)
            print(f"  Exchange loaded: {ex.id}")
            s = map_symbol(v, normalize_symbol(symbol))
            print(f"  Mapped symbol: {s}")
            t = ex.fetch_ticker(s)
            print(f"  Raw ticker response: {json.dumps(t, indent=2)}")
            status["venues"][v] = {
                "bid": t.get("bid"),
                "ask": t.get("ask"),
                "last": t.get("last"),
                "timestamp": t.get("timestamp"),
                "ok": True
            }
            print(f"  Success - bid/ask/last: {t.get('bid')}/{t.get('ask')}/{t.get('last')}")
        except Exception as e:
            print(f"  Fetch failed: {type(e).__name__}: {e}")
            status["venues"][v] = {"ok": False, "error": str(e)}
        finally:
            try:
                if hasattr(ex, "close"):
                    ex.close()
                    print("  Exchange closed")
            except Exception as e:
                print(f"  Close failed: {e}")
    return status

def run_forever() -> None:
    ensure_dirs()
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass
    if not _acquire_lock():
        print("Lock exists - another instance running")
        return
    try:
        while True:
            if STOP_FILE.exists():
                break
            data = fetch_status()
            STATUS_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote snapshot at {_now_iso()}\n")
            time.sleep(10)
    finally:
        _release_lock()
        print("Tick publisher stopped")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "stop"], default="run")
    args = ap.parse_args()
    if args.cmd == "stop":
        print(request_stop())
    else:
        run_forever()

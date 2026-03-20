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
DEFAULT_POLL_INTERVAL_SEC = 2.0

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


def _poll_interval_sec() -> float:
    raw = str(os.environ.get("CBP_TICK_PUBLISH_INTERVAL_SEC") or "").strip()
    if raw:
        try:
            return max(0.5, float(raw))
        except Exception:
            pass
    return float(DEFAULT_POLL_INTERVAL_SEC)


def _symbol() -> str:
    return _symbols()[0]


def _symbols() -> list[str]:
    env_symbols = [str(item).strip() for item in str(os.environ.get("CBP_SYMBOLS") or "").split(",") if str(item).strip()]
    if env_symbols:
        return env_symbols
    return ["BTC/USD"]

def fetch_status() -> dict:
    status = {
        "ts": _now_iso(),
        "ts_ms": int(time.time() * 1000),
        "venues": {},
        "ticks": [],
    }
    venues = [v.strip() for v in (os.environ.get("CBP_VENUE") or "coinbase").split(",") if v.strip()]
    venues = [str(v).lower().strip() for v in venues]
    if not (os.environ.get("CBP_VENUE") or "").lower().startswith("binance"):
        venues = [v for v in venues if not v.startswith("binance")]

    symbols = _symbols()
    for v in venues:
        print(f"\n=== Fetching from {v} ===")
        ex = None
        try:
            ex = make_exchange(v, {"apiKey": None, "secret": None}, enable_rate_limit=True)
            print(f"  Exchange loaded: {ex.id}")
            venue_ok = False
            venue_error = ""
            for symbol in symbols:
                s = map_symbol(v, normalize_symbol(symbol))
                print(f"  Mapped symbol: {symbol} -> {s}")
                try:
                    t = ex.fetch_ticker(s)
                    fetch_ts_ms = int(time.time() * 1000)
                    print(f"  Raw ticker response ({symbol}): {json.dumps(t, indent=2)}")
                    tick = {
                        "venue": v,
                        "symbol": normalize_symbol(symbol),
                        "symbol_mapped": s,
                        "bid": t.get("bid"),
                        "ask": t.get("ask"),
                        "last": t.get("last"),
                        "ts_ms": fetch_ts_ms,
                        "exchange_ts_ms": int(t.get("timestamp") or 0),
                    }
                    status["ticks"].append(tick)
                    if not venue_ok:
                        status["venues"][v] = {
                            "bid": t.get("bid"),
                            "ask": t.get("ask"),
                            "last": t.get("last"),
                            "timestamp": fetch_ts_ms,
                            "exchange_timestamp": t.get("timestamp"),
                            "ok": True,
                        }
                    venue_ok = True
                    print(f"  Success - bid/ask/last: {t.get('bid')}/{t.get('ask')}/{t.get('last')}")
                except Exception as e:
                    venue_error = f"{type(e).__name__}: {e}"
                    print(f"  Fetch failed for {symbol}: {venue_error}")
            if not venue_ok:
                status["venues"][v] = {"ok": False, "error": venue_error or "no_symbol_tickers"}
        except Exception as e:
            print(f"  Fetch failed: {type(e).__name__}: {e}")
            status["venues"][v] = {"ok": False, "error": str(e)}
        finally:
            try:
                if ex is not None and hasattr(ex, "close"):
                    ex.close()
                    print("  Exchange closed")
            except Exception as e:
                print(f"  Close failed: {e}")
    return status

def run_forever() -> None:
    ensure_dirs()
    poll_interval_sec = _poll_interval_sec()
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
            time.sleep(poll_interval_sec)
    finally:
        _release_lock()
        print("Tick publisher stopped")


def run_tick_publisher() -> None:
    """Compatibility entrypoint used by scripts/run_tick_publisher.py."""
    run_forever()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "stop"], default="run")
    args = ap.parse_args()
    if args.cmd == "stop":
        print(request_stop())
    else:
        run_forever()

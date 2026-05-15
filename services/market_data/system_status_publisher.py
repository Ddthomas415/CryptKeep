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
SAMPLE_OHLCV_DIR = Path(__file__).resolve().parents[2] / "sample_data" / "ohlcv"
_SAMPLE_TICK_CURSOR: dict[tuple[str, str], int] = {}

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


def _use_sample_ohlcv_ticks() -> bool:
    return str(os.environ.get("CBP_USE_SAMPLE_OHLCV") or "").strip().lower() in {"1", "true", "yes", "on"}


def _sample_ohlcv_rows(symbol: str, *, timeframe: str = "1d") -> list[list[float]]:
    normalized = normalize_symbol(symbol)
    sample = SAMPLE_OHLCV_DIR / f"{normalized.replace('/', '_')}_{timeframe}.json"
    if not sample.exists():
        return []
    try:
        rows = json.loads(sample.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(rows, list):
        return []
    out: list[list[float]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 6:
            continue
        try:
            out.append(
                [
                    int(row[0] or 0),
                    float(row[1]),
                    float(row[2]),
                    float(row[3]),
                    float(row[4]),
                    float(row[5]),
                ]
            )
        except Exception:
            continue
    return out


def _sample_tick(symbol: str, *, timeframe: str = "1d") -> dict | None:
    normalized = normalize_symbol(symbol)
    rows = _sample_ohlcv_rows(symbol, timeframe=timeframe)
    if not rows:
        return None
    key = (normalized, str(timeframe or "").strip().lower() or "1d")
    idx = int(_SAMPLE_TICK_CURSOR.get(key, 0))
    idx = max(0, min(idx, len(rows) - 1))
    row = rows[idx]
    _SAMPLE_TICK_CURSOR[key] = min(idx + 1, len(rows) - 1)
    ts_ms = int(row[0] or 0)
    close = float(row[4])
    return {
        "symbol": normalized,
        "ts_ms": ts_ms,
        "bid": close,
        "ask": close,
        "last": close,
    }
    return None

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
        if _use_sample_ohlcv_ticks():
            venue_ok = False
            venue_error = ""
            for symbol in symbols:
                sample_tick = _sample_tick(symbol)
                if not sample_tick:
                    venue_error = f"sample_tick_missing:{normalize_symbol(symbol)}"
                    continue
                fetch_ts_ms = int(time.time() * 1000)
                mapped = map_symbol(v, normalize_symbol(symbol))
                tick = {
                    "venue": v,
                    "symbol": normalize_symbol(symbol),
                    "symbol_mapped": mapped,
                    "bid": sample_tick.get("bid"),
                    "ask": sample_tick.get("ask"),
                    "last": sample_tick.get("last"),
                    "ts_ms": fetch_ts_ms,
                    "exchange_ts_ms": int(sample_tick.get("ts_ms") or 0),
                }
                status["ticks"].append(tick)
                if not venue_ok:
                    status["venues"][v] = {
                        "bid": sample_tick.get("bid"),
                        "ask": sample_tick.get("ask"),
                        "last": sample_tick.get("last"),
                        "timestamp": fetch_ts_ms,
                        "exchange_timestamp": int(sample_tick.get("ts_ms") or 0),
                        "ok": True,
                    }
                venue_ok = True
            if not venue_ok:
                status["venues"][v] = {"ok": False, "error": venue_error or "no_sample_ticks"}
            continue
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

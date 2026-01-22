from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from services.admin.config_editor import load_user_yaml
from services.os.app_paths import runtime_dir, ensure_dirs
from services.execution.paper_engine import PaperEngine

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "paper_engine.stop"
LOCK_FILE = LOCKS / "paper_engine.lock"
STATUS_FILE = FLAGS / "paper_engine.status.json"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _write_status(obj: dict) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _acquire_lock() -> bool:
    LOCKS.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        return False
    LOCK_FILE.write_text(json.dumps({"pid": os.getpid(), "ts": _now()}, indent=2) + "\n", encoding="utf-8")
    return True

def _release_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(_now() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}

def run_forever() -> None:
    ensure_dirs()
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass
    if not _acquire_lock():
        _write_status({"ok": False, "reason": "lock_exists", "lock_file": str(LOCK_FILE), "ts": _now()})
        return
    eng = PaperEngine()
    cfg = load_user_yaml()
    p = cfg.get("paper_trading") if isinstance(cfg.get("paper_trading"), dict) else {}
    venue = str(p.get("default_venue", "binance") or "binance").lower().strip()
    symbol = str(p.get("default_symbol", "BTC/USDT") or "BTC/USDT").strip()
    interval = float(p.get("loop_interval_sec", 1.0) or 1.0)
    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "venue": venue, "symbol": symbol, "ts": _now()})
    try:
        while True:
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "pid": os.getpid(), "ts": _now()})
                break
            rec = eng.evaluate_open_orders()
            mtm = eng.mark_to_market(venue, symbol)
            _write_status({
                "ok": True,
                "status": "running",
                "pid": os.getpid(),
                "ts": _now(),
                "venue": venue,
                "symbol": symbol,
                "reconcile": {"open_seen": rec.get("open_orders_seen"), "filled": rec.get("filled"), "rejected": rec.get("rejected")},
                "mtm": {"cash": mtm.get("cash_quote"), "equity": mtm.get("equity_quote"), "unreal": mtm.get("unrealized_pnl"), "realized": mtm.get("realized_pnl"), "mid": mtm.get("mid")},
            })
            time.sleep(max(0.25, interval))
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now()})

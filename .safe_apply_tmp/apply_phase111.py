# apply_phase111.py - Phase 111 launcher (EMA strategy runner → intents + state store + dashboard)
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
        print(f"Skipping patch - file missing: {path}")
        return
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
    else:
        print(f"No changes needed: {path}")

# 1) Strategy state store (SQLite KV)
write("storage/strategy_state_sqlite.py", r'''from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "strategy_state.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS strategy_state (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL,
  updated_ts TEXT NOT NULL
);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con

class StrategyStateSQLite:
    def __init__(self) -> None:
        _connect().close()

    def get(self, k: str) -> Optional[str]:
        con = _connect()
        try:
            r = con.execute("SELECT v FROM strategy_state WHERE k=?", (str(k),)).fetchone()
            return r[0] if r else None
        finally:
            con.close()

    def set(self, k: str, v: str) -> None:
        con = _connect()
        try:
            con.execute("INSERT OR REPLACE INTO strategy_state(k,v,updated_ts) VALUES(?,?,?)", (str(k), str(v), _now()))
        finally:
            con.close()
''')

# 2) EMA strategy runner
write("services/strategy/ema_crossover_runner.py", r'''from __future__ import annotations
import json
import math
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from services.admin.config_editor import load_user_yaml
from services.market_data.tick_reader import get_best_bid_ask_last, mid_price
from services.security.exchange_factory import make_exchange
from services.os.app_paths import runtime_dir, ensure_dirs
from storage.intent_queue_sqlite import IntentQueueSQLite
from storage.paper_trading_sqlite import PaperTradingSQLite
from storage.strategy_state_sqlite import StrategyStateSQLite

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "strategy_runner.stop"
LOCK_FILE = LOCKS / "strategy_runner.lock"
STATUS_FILE = FLAGS / "strategy_runner.status.json"

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

def _release_lock() -> None:
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

def _cfg() -> dict:
    cfg = load_user_yaml()
    s = cfg.get("strategy_runner") if isinstance(cfg.get("strategy_runner"), dict) else {}
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venue = str(s.get("venue", (pf.get("venues",[ "binance" ])[0] if isinstance(pf.get("venues"), list) and pf.get("venues") else "binance")) or "binance").lower().strip()
    symbol = str(s.get("symbol", (pf.get("symbols",[ "BTC/USDT" ])[0] if isinstance(pf.get("symbols"), list) and pf.get("symbols") else "BTC/USDT")) or "BTC/USDT").strip()
    return {
        "enabled": bool(s.get("enabled", True)),
        "strategy_id": str(s.get("strategy_id", "ema_xover_v1") or "ema_xover_v1"),
        "venue": venue,
        "symbol": symbol,
        "fast_n": int(s.get("fast_n", 12) or 12),
        "slow_n": int(s.get("slow_n", 26) or 26),
        "min_bars": int(s.get("min_bars", 60) or 60),
        "max_bars": int(s.get("max_bars", 400) or 400),
        "loop_interval_sec": float(s.get("loop_interval_sec", 1.0) or 1.0),
        "qty": float(s.get("qty", 0.001) or 0.001),
        "order_type": str(s.get("order_type", "market") or "market").lower().strip(),
        "allow_first_signal_trade": bool(s.get("allow_first_signal_trade", False)),
        "use_ccxt_fallback": bool(s.get("use_ccxt_fallback", True)),
        "max_tick_age_sec": float(s.get("max_tick_age_sec", 5.0) or 5.0),
        "position_aware": bool(s.get("position_aware", True)),
        "sell_full_position": bool(s.get("sell_full_position", True)),
    }

def _fetch_mid(cfg: dict) -> Optional[tuple[float, int]]:
    q = get_best_bid_ask_last(cfg["venue"], cfg["symbol"])
    if q:
        m = mid_price(q)
        ts_ms = int(q.get("ts_ms") or 0)
        if m is None:
            return None
        age = (time.time() * 1000.0 - float(ts_ms)) / 1000.0 if ts_ms else 9999.0
        if age > float(cfg["max_tick_age_sec"]):
            return None
        return float(m), ts_ms
    if not cfg["use_ccxt_fallback"]:
        return None
    ex = make_exchange(cfg["venue"], {"apiKey": None, "secret": None}, enable_rate_limit=True)
    try:
        t = ex.fetch_ticker(cfg["symbol"])
        bid = t.get("bid")
        ask = t.get("ask")
        last = t.get("last")
        if bid is not None and ask is not None:
            m = (float(bid) + float(ask)) / 2.0
        elif last is not None:
            m = float(last)
        else:
            return None
        ts_ms = int(t.get("timestamp") or (time.time() * 1000))
        return m, ts_ms
    finally:
        try:
            if hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass

def _ema(series: List[float], n: int) -> Optional[float]:
    if n <= 1 or len(series) < n:
        return None
    alpha = 2.0 / (n + 1.0)
    e = series[0]
    for x in series[1:]:
        e = alpha * x + (1.0 - alpha) * e
    return float(e)

def run_forever() -> None:
    ensure_dirs()
    cfg = _cfg()
    if not cfg["enabled"]:
        _write_status({"ok": False, "reason": "disabled", "ts": _now()})
        return
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass
    if not _acquire_lock():
        _write_status({"ok": False, "reason": "lock_exists", "lock_file": str(LOCK_FILE), "ts": _now()})
        return
    qdb = IntentQueueSQLite()
    pdb = PaperTradingSQLite()
    sdb = StrategyStateSQLite()
    k_prices = f"prices:{cfg['venue']}:{cfg['symbol']}:{cfg['strategy_id']}"
    k_last_sig = f"last_sig:{cfg['venue']}:{cfg['symbol']}:{cfg['strategy_id']}"
    k_warm = f"warmed:{cfg['venue']}:{cfg['symbol']}:{cfg['strategy_id']}"
    try:
        prices = json.loads(sdb.get(k_prices) or "[]")
        if not isinstance(prices, list):
            prices = []
        prices = [float(x) for x in prices if isinstance(x, (int,float)) and math.isfinite(float(x))]
    except Exception:
        prices = []
    warmed = (sdb.get(k_warm) or "") == "1"
    last_sig = sdb.get(k_last_sig)
    try:
        last_sig_i = int(last_sig) if last_sig is not None else 0
    except Exception:
        last_sig_i = 0
    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "cfg": cfg, "ts": _now()})
    loops = 0
    enqueued = 0
    try:
        while True:
            loops += 1
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "pid": os.getpid(), "ts": _now(), "loops": loops, "enqueued": enqueued})
                break
            tick = _fetch_mid(cfg)
            if not tick:
                _write_status({"ok": True, "status": "running", "pid": os.getpid(), "ts": _now(), "note": "no_fresh_tick", "loops": loops, "enqueued": enqueued})
                time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
                continue
            m, ts_ms = tick
            prices.append(float(m))
            if len(prices) > int(cfg["max_bars"]):
                prices = prices[-int(cfg["max_bars"]):]
            if loops % 5 == 0:
                sdb.set(k_prices, json.dumps(prices))
            if len(prices) < int(cfg["min_bars"]):
                _write_status({"ok": True, "status": "running", "pid": os.getpid(), "ts": _now(), "mid": m, "bars": len(prices), "note": "warming", "enqueued": enqueued})
                time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
                continue
            ef = _ema(prices[-int(cfg["min_bars"]):], int(cfg["fast_n"]))
            es = _ema(prices[-int(cfg["min_bars"]):], int(cfg["slow_n"]))
            if ef is None or es is None:
                time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
                continue
            sig = 1 if ef > es else -1
            if not warmed:
                sdb.set(k_last_sig, str(sig))
                sdb.set(k_warm, "1")
                warmed = True
                last_sig_i = sig
                _write_status({"ok": True, "status": "running", "pid": os.getpid(), "ts": _now(), "mid": m, "ema_fast": ef, "ema_slow": es, "sig": sig, "note": "warmed_no_trade"})
                time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
                continue
            changed = (sig != last_sig_i)
            action = None
            pos = pdb.get_position(cfg["symbol"]) or {"qty": 0.0, "avg_price": 0.0}
            pos_qty = float(pos.get("qty") or 0.0)
            if changed:
                if sig == 1:
                    if (not cfg["position_aware"]) or (pos_qty <= 0.0):
                        action = "buy"
                else:
                    if (not cfg["position_aware"]) or (pos_qty > 0.0):
                        action = "sell"
            if action:
                intent_id = str(uuid.uuid4())
                qty = float(cfg["qty"])
                if action == "sell" and bool(cfg["sell_full_position"]) and pos_qty > 0.0:
                    qty = pos_qty
                qdb.upsert_intent({
                    "intent_id": intent_id,
                    "created_ts": _now(),
                    "ts": _now(),
                    "source": "strategy",
                    "strategy_id": cfg["strategy_id"],
                    "venue": cfg["venue"],
                    "symbol": cfg["symbol"],
                    "side": action,
                    "order_type": cfg["order_type"],
                    "qty": float(qty),
                    "limit_price": None,
                    "status": "queued",
                    "last_error": None,
                    "client_order_id": None,
                    "linked_order_id": None,
                })
                enqueued += 1
            if changed:
                last_sig_i = sig
                sdb.set(k_last_sig, str(sig))
            _write_status({
                "ok": True,
                "status": "running",
                "pid": os.getpid(),
                "ts": _now(),
                "mid": m,
                "ts_ms": ts_ms,
                "bars": len(prices),
                "ema_fast": ef,
                "ema_slow": es,
                "sig": sig,
                "sig_changed": bool(changed),
                "pos_qty": pos_qty,
                "action": action,
                "enqueued_total": enqueued,
                "cfg": {"venue": cfg["venue"], "symbol": cfg["symbol"], "fast_n": cfg["fast_n"], "slow_n": cfg["slow_n"], "min_bars": cfg["min_bars"], "order_type": cfg["order_type"]},
            })
            time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
    finally:
        try:
            sdb.set(k_prices, json.dumps(prices))
            sdb.set(k_last_sig, str(last_sig_i))
        except Exception:
            pass
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now(), "loops": loops, "enqueued_total": enqueued})
''')

# 3) Runner script
write("scripts/run_strategy_runner.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from services.strategy.ema_crossover_runner import run_forever, request_stop

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run","stop"], nargs="?", default="run")
    args = ap.parse_args()
    if args.cmd == "stop":
        print(request_stop())
        return 0
    run_forever()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 4) Dashboard panel
def patch_dashboard(t: str) -> str:
    if "Strategy Runner v1 (EMA → Intents)" in t and "scripts/run_strategy_runner.py" in t:
        return t
    add = r'''
st.divider()
st.header("Strategy Runner v1 (EMA → Intents)")
st.caption("Paper-only. Produces intents into intent_queue.sqlite (status=queued). Position-aware by default: buys only when flat, sells only when in position. No trading on first warm-up signal unless enabled in config.")
try:
    import time as _time
    import platform as _platform
    import subprocess as _subprocess
    import sys as _sys
    import json as _json
    from pathlib import Path as _Path
    status_file = _Path("runtime") / "flags" / "strategy_runner.status.json"
    lock_file = _Path("runtime") / "locks" / "strategy_runner.lock"
    stop_file = _Path("runtime") / "flags" / "strategy_runner.stop"
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Start Strategy Runner (background)"):
            cmd = [_sys.executable, "scripts/run_strategy_runner.py", "run"]
            try:
                if _platform.system().lower().startswith("win"):
                    DETACHED_PROCESS = 0x00000008
                    _subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                else:
                    _subprocess.Popen(cmd, start_new_session=True, stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                st.success({"ok": True, "started": cmd})
            except Exception as e:
                st.error(f"Start failed: {type(e).__name__}: {e}")
    with c2:
        if st.button("Request stop Strategy Runner"):
            stop_file.parent.mkdir(parents=True, exist_ok=True)
            stop_file.write_text(str(int(_time.time())) + "\n", encoding="utf-8")
            st.success({"ok": True, "stop_file": str(stop_file)})
    with c3:
        if st.button("Show commands"):
            st.code("python3 scripts/run_strategy_runner.py run\npython3 scripts/run_strategy_runner.py stop", language="bash")
    st.subheader("Runner status")
    st.caption(f"Lock: {lock_file}")
    if status_file.exists():
        st.json(_json.loads(status_file.read_text(encoding="utf-8")))
    else:
        st.info("No strategy runner status file yet.")
except Exception as e:
    st.error(f"Strategy runner panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 5) Config validation
def patch_config_editor(t: str) -> str:
    if "strategy_runner.enabled" in t and "strategy_runner.fast_n" in t:
        return t
    insert = """
    # Strategy runner (optional)
    sr = cfg.get("strategy_runner", {})
    if sr is not None and not isinstance(sr, dict):
        errors.append("strategy_runner:must_be_mapping")
        sr = {}
    if isinstance(sr, dict):
        if "enabled" in sr and sr["enabled"] is not None and not _is_bool(sr["enabled"]):
            errors.append("strategy_runner.enabled:must_be_bool")
        for k in ("fast_n","slow_n","min_bars","max_bars"):
            if k in sr and sr[k] is not None and not _is_int(sr[k]):
                errors.append(f"strategy_runner.{k}:must_be_int")
        for k in ("loop_interval_sec","qty","max_tick_age_sec"):
            if k in sr and sr[k] is not None and not _is_float(sr[k]):
                errors.append(f"strategy_runner.{k}:must_be_float")
        for k in ("venue","symbol","strategy_id","order_type"):
            if k in sr and sr[k] is not None:
                try:
                    str(sr[k])
                except Exception:
                    errors.append(f"strategy_runner.{k}:must_be_string")
        for k in ("allow_first_signal_trade","use_ccxt_fallback","position_aware","sell_full_position"):
            if k in sr and sr[k] is not None and not _is_bool(sr[k]):
                errors.append(f"strategy_runner.{k}:must_be_bool")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 6) Default config in install.py
def patch_install_py(t: str) -> str:
    if "strategy_runner:" in t:
        return t
    marker = "intent_consumer:\n"
    if marker not in t:
        return t
    return t.replace(
        marker,
        marker + (
            "strategy_runner:\n"
            " enabled: true\n"
            " strategy_id: \"ema_xover_v1\"\n"
            " venue: \"binance\"\n"
            " symbol: \"BTC/USDT\"\n"
            " fast_n: 12\n"
            " slow_n: 26\n"
            " min_bars: 60\n"
            " max_bars: 400\n"
            " loop_interval_sec: 1.0\n"
            " qty: 0.001\n"
            " order_type: \"market\"\n"
            " allow_first_signal_trade: false\n"
            " use_ccxt_fallback: true\n"
            " max_tick_age_sec: 5.0\n"
            " position_aware: true\n"
            " sell_full_position: true\n\n"
        ),
        1
    )

patch("install.py", patch_install_py)

# 7) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DG) Strategy Runner v1 (EMA → Intents)" in t:
        return t
    return t + (
        "\n## DG) Strategy Runner v1 (EMA → Intents)\n"
        "- ✅ DG1: EMA crossover runner reads mid price (tick publisher; CCXT fallback optional)\n"
        "- ✅ DG2: Stateful (persists price buffer + last signal) to avoid repeated intent spam\n"
        "- ✅ DG3: Position-aware default: buy only when flat, sell only when in position (option to sell full position)\n"
        "- ✅ DG4: Produces intents into intent_queue.sqlite (queued), consumed by intent consumer → paper engine\n"
        "- ✅ DG5: Start/stop/status via runtime files + dashboard panel\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 111 applied (EMA strategy runner → intents + state store + dashboard + config + checkpoints).")
print("Next steps:")
print("  1. Run strategy runner: python3 scripts/run_strategy_runner.py run")
print("  2. Check dashboard 'Strategy Runner v1' panel for status")
print("  3. Test stop: python3 scripts/run_strategy_runner.py stop")
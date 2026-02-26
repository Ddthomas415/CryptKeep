from __future__ import annotations
import json
import math
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from services.admin.config_editor import load_user_yaml
from services.market_data.tick_reader import get_best_bid_ask_last, mid_price
from services.market_data.symbol_router import normalize_venue, map_symbol
from services.market_data.multi_venue_view import best_venue
from services.risk.market_quality_guard import check as mq_check
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

    default_symbol = globals().get("DEFAULT_SYMBOL", "BTC/USD")
    pf_venues = pf.get("venues") if isinstance(pf.get("venues"), list) else []
    pf_symbols = pf.get("symbols") if isinstance(pf.get("symbols"), list) else []

    env_v = (os.environ.get("CBP_VENUE") or "").strip().lower()
    venue = str(env_v or s.get("venue") or (pf_venues[0] if pf_venues else "coinbase")).lower().strip()

    env_syms = [x.strip() for x in (os.environ.get("CBP_SYMBOLS") or "").split(",") if x.strip()]
    symbol = str(env_syms[0] if env_syms else (s.get("symbol") or (pf_symbols[0] if pf_symbols else default_symbol))).strip()

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
            # Optional: choose best venue
            if bool(cfg.get("auto_select_best_venue")):
                candidates = cfg.get("venue_candidates")
                if not isinstance(candidates, list) or not candidates:
                    # fall back to preflight venues if present
                    base_cfg = load_user_yaml()
                    pf = base_cfg.get("preflight") if isinstance(base_cfg.get("preflight"), dict) else {}
                    candidates = pf.get("venues") if isinstance(pf.get("venues"), list) else [cfg["venue"]]
                candidates = [normalize_venue(str(v)) for v in candidates]
                current_venue = normalize_venue(cfg["venue"])
                cfg["venue"] = current_venue

                if bool(cfg.get("switch_only_when_blocked", True)):
                    g = mq_check(cfg["venue"], cfg["symbol"])
                    if not g.get("ok"):
                        bv = best_venue(candidates, cfg["symbol"], require_ok=True)
                        if bv and bv.get("venue") and bv["venue"] != cfg["venue"]:
                            cfg["venue"] = str(bv["venue"])
                else:
                    bv = best_venue(candidates, cfg["symbol"], require_ok=True)
                    if bv and bv.get("venue"):
                        cfg["venue"] = str(bv["venue"])

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


# ---- runtime defaults (override by env set from scripts/bot_ctl.py) ----
DEFAULT_SYMBOL = ([x.strip() for x in (os.environ.get("CBP_SYMBOLS") or "").split(",") if x.strip()] or ["BTC/USD"])[0]

from __future__ import annotations
import time
import uuid
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_symbol, normalize_venue
from services.meta.meta_composer import compose, routing_cfg
from storage.meta_decisions_sqlite import MetaDecisionsSQLite
from storage.intent_queue_sqlite import IntentQueueSQLite
from services.os.app_paths import runtime_dir

FLAGS = runtime_dir() / "flags"
STOP_FILE = FLAGS / "meta_strategy.stop"

def _cfg() -> dict:
    cfg = load_user_yaml()
    m = cfg.get("meta_strategy") if isinstance(cfg.get("meta_strategy"), dict) else {}
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    symbols = pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USDT"]
    return {
        "enabled": bool(m.get("enabled", False)),
        "poll_sec": int(m.get("poll_sec", 15) or 15),
        "symbols": [normalize_symbol(str(s)) for s in symbols],
    }

def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

class Cooldown:
    def __init__(self):
        self.last_ts = {}  # symbol -> unix
    def ok(self, symbol: str, cooldown_sec: int) -> bool:
        t = self.last_ts.get(symbol, 0.0)
        return (time.time() - t) >= float(cooldown_sec)
    def mark(self, symbol: str) -> None:
        self.last_ts[symbol] = time.time()

def run_forever() -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    if STOP_FILE.exists():
        STOP_FILE.unlink(missing_ok=True)
    meta_db = MetaDecisionsSQLite()
    qdb = IntentQueueSQLite()
    cd = Cooldown()
    while True:
        if STOP_FILE.exists():
            break
        cfg = _cfg()
        if not cfg["enabled"]:
            time.sleep(2.0)
            continue
        r = routing_cfg()
        paper_enabled = bool(r.get("paper_enabled", False))
        base_qty = float(r.get("base_qty") or 0.001)
        cooldown_sec = int(r.get("cooldown_sec") or 300)
        for sym in cfg["symbols"]:
            d = compose(sym)
            meta_db.insert({
                "decision_id": d["decision_id"],
                "ts": _now_iso(),
                "symbol": d["symbol"],
                "venue": d["venue"],
                "timeframe": d["timeframe"],
                "action": d["action"],
                "score": d["score"],
                "confidence": d["confidence"],
                "internal_action": (d.get("internal") or {}).get("action"),
                "internal_score": (d.get("internal") or {}).get("score"),
                "external_action": (d.get("external") or {}).get("action"),
                "external_score": (d.get("external") or {}).get("score"),
                "details": d,
            })
            if not paper_enabled:
                continue
            if d["action"] not in ("buy", "sell"):
                continue
            if not cd.ok(sym, cooldown_sec):
                continue
            qty = float(base_qty)
            if bool(r.get("qty_scale_by_score", True)):
                x = min(1.0, max(0.0, abs(float(d["score"]))))
                qmin = float(r.get("min_qty_scale") or 0.5)
                qmax = float(r.get("max_qty_scale") or 1.5)
                scale = qmin + (qmax - qmin) * x
                qty = qty * scale
            intent_id = str(uuid.uuid4())
            it = {
                "intent_id": intent_id,
                "ts": str(int(time.time())),
                "source": "meta_strategy",
                "venue": d["venue"],
                "symbol": d["symbol"],
                "side": d["action"],
                "order_type": "market",
                "qty": float(qty),
                "limit_price": None,
                "status": "queued",
                "last_error": None,
            }
            qdb.upsert_intent(it)
            cd.mark(sym)
        time.sleep(float(cfg["poll_sec"]))

def stop() -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text("stop\n", encoding="utf-8")

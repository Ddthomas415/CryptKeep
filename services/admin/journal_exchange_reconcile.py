from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any

from services.security.credential_store import get_exchange_credentials
from services.security.exchange_factory import make_exchange
from services.admin.state_report import maybe_auto_update_state_on_snapshot
from services.os.app_paths import data_dir, runtime_dir, ensure_dirs

ensure_dirs()
SNAPSHOT_DIR = runtime_dir() / "snapshots"
LOCAL_DB_DIRS = [data_dir(), runtime_dir(), runtime_dir() / "db", runtime_dir() / "data"]
_LOG = logging.getLogger(__name__)

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def _save_snapshot(obj: dict) -> str:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    p = SNAPSHOT_DIR / f"journal_reconcile.{_tag()}.json"
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    try:
        maybe_auto_update_state_on_snapshot(tag="journal_reconcile_snapshot")
    except Exception as e:
        _LOG.warning("state auto-update failed after journal snapshot: %s: %s", type(e).__name__, e)
    return str(p)

def _list_sqlite_files() -> list[Path]:
    out, seen = [], set()
    for d in LOCAL_DB_DIRS:
        if not d.exists(): continue
        for p in d.glob("*.sqlite"):
            rp = str(p.resolve())
            if rp not in seen and p.is_file():
                out.append(p); seen.add(rp)
        for p in d.glob("*.db"):
            rp = str(p.resolve())
            if rp not in seen and p.is_file():
                out.append(p); seen.add(rp)
    out.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return out

def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def _safe_float(x) -> float | None:
    try:
        return None if x is None else float(x)
    except Exception:
        return None

def _to_epoch_ms(x) -> int | None:
    if x is None:
        return None
    try:
        if isinstance(x, (int, float)):
            v = float(x)
            return int(v) if v > 1e10 else int(v * 1000)
    except Exception:
        return None
    try:
        s = str(x).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None

def scan_local_journals(limit: int = 500, symbol: str | None = None) -> dict:
    # Simplified scan for trades/orders; returns list of normalized dicts
    found = {"trades": [], "orders": [], "sources": [], "errors": []}
    for db in _list_sqlite_files():
        try:
            con = _connect(db)
            try:
                for tbl in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                    tbl_name = tbl[0]
                    rows = con.execute(f'SELECT * FROM "{tbl_name}" LIMIT ?', (limit,)).fetchall()
                    for r in rows:
                        d = dict(r)
                        d["_db"], d["_table"] = str(db), tbl_name
                        found["trades"].append(d)
            finally: con.close()
        except Exception as e:
            found["errors"].append({"db": str(db), "error": f"{type(e).__name__}: {e}"})
    return found

def _fingerprint(symbol: str, side: str, qty: float | None, price: float | None, ts_ms: int | None, bucket_ms: int) -> str:
    q, p, t = 0.0 if qty is None else float(qty), 0.0 if price is None else float(price), 0 if ts_ms is None else int(ts_ms)
    b = int(t // bucket_ms) if bucket_ms>0 else t
    return f"{symbol}|{side}|{round(q,8)}|{round(p,8)}|{b}"

def fetch_exchange_history(venue: str, symbol: str | None, limit: int = 200) -> dict:
    v = str(venue).lower().strip()
    creds = get_exchange_credentials(v)
    if not creds: return {"ok": False, "venue": v, "reason": "missing_credentials"}
    ex = make_exchange(v, creds, enable_rate_limit=True)
    out = {"ok": True, "venue": v, "trades": [], "orders": [], "errors": []}
    try:
        try: tr = ex.fetch_my_trades(symbol, limit=limit) if symbol else ex.fetch_my_trades(limit=limit)
        except Exception as e: tr=[]; out["errors"].append({"where":"fetch_my_trades","error":f"{type(e).__name__}: {e}"})
        for t in tr or []: out["trades"].append({"id": t.get("id"), "client_id": t.get("clientOrderId"), "symbol": t.get("symbol"), "side": t.get("side"), "qty": t.get("amount"), "price": t.get("price"), "ts_ms": t.get("timestamp")})
        return out
    finally:
        try: ex.close()
        except Exception as e:
            _LOG.warning("exchange close failed after history fetch (%s): %s: %s", v, type(e).__name__, e)

def reconcile_journal_vs_exchange(venue: str, symbol: str | None = None, *, local_limit: int=600, exchange_limit: int=300, bucket_seconds: int=10) -> dict:
    bucket_ms = bucket_seconds*1000
    local = scan_local_journals(limit=local_limit, symbol=symbol)
    exch = fetch_exchange_history(venue, symbol, limit=exchange_limit)
    local_fp = set(_fingerprint(x.get("symbol",""), x.get("side",""), x.get("qty"), x.get("price"), x.get("ts_ms"), bucket_ms) for x in local.get("trades",[]))
    ex_fp = set(_fingerprint(x.get("symbol",""), x.get("side",""), x.get("qty"), x.get("price"), x.get("ts_ms"), bucket_ms) for x in exch.get("trades",[]) if exch.get("ok"))
    missing_local = sorted(list(ex_fp - local_fp))[:200]
    missing_exchange = sorted(list(local_fp - ex_fp))[:200]
    ghost_risk = len(missing_exchange)>0 and len(ex_fp)>0 and (len(missing_exchange)/max(1,len(ex_fp)))>0.25
    report = {"ts":_now(),"venue":venue,"symbol":symbol,"ok":bool(exch.get("ok",False)),
              "bucket_seconds":bucket_seconds,"counts":{"local_trades":len(local_fp),"exchange_trades":len(ex_fp),
              "missing_local":len(missing_local),"missing_exchange":len(missing_exchange)},
              "signals":{"ghost_position_risk":ghost_risk,"note":"Heuristic-only; investigate missing items."},
              "missing_local_fingerprints_sample":missing_local,"missing_exchange_fingerprints_sample":missing_exchange,
              "local_sources":local.get("sources",[])[:30],"exchange_errors":exch.get("errors",[]),"local_errors":local.get("errors",[])}

    report["snapshot_path"] = _save_snapshot(report)
    return report

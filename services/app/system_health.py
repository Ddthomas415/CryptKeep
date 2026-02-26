from __future__ import annotations
import os
import json
from pathlib import Path
from services.os.app_paths import runtime_dir
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from services.market_data.multi_venue_view import venue_rows, rank_rows

def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def collect_process_files() -> dict:
    rt = runtime_dir()
    flags = rt / "flags"
    locks = rt / "locks"
    sup = rt / "supervisor"
    snaps = rt / "snapshots"
    def list_files(d: Path):
        if not d.exists():
            return []
        out = []
        for p in sorted(d.glob("*")):
            if p.is_file():
                out.append({"path": str(p), "name": p.name, "mtime": p.stat().st_mtime})
        return out
    return {
        "flags": list_files(flags),
        "locks": list_files(locks),
        "supervisor": list_files(sup),
        "snapshots": list_files(snaps),
        "pids": _read_json(sup / "pids.json") if (sup / "pids.json").exists() else None,
    }

def collect_market_health() -> list[dict]:
    cfg = load_user_yaml()
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues = pf.get("venues") if isinstance(pf.get("venues"), list) else ["coinbase","gateio"]
    _env_v = (os.environ.get("CBP_VENUE") or "").strip().lower()
    if _env_v:
        venues = [_env_v]
    elif isinstance(venues, list):
        venues = [v for v in venues if not str(v).lower().startswith("binance")]

    symbols = pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USD"]

    _env_syms = [x.strip() for x in (os.environ.get("CBP_SYMBOLS") or "").split(",") if x.strip()]

    if _env_syms:

        symbols = _env_syms

    venues = [normalize_venue(str(v)) for v in venues]
    symbols = [normalize_symbol(str(s)) for s in symbols]
    rows_all = []
    for sym in symbols:
        rows = rank_rows(venue_rows(venues, sym))
        for r in rows:
            r2 = dict(r)
            r2["symbol"] = sym
            rows_all.append(r2)
    return rows_all

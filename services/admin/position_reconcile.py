from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

from services.admin.journal_exchange_reconcile import scan_local_journals
from services.market_data.symbol_normalize import normalize_symbols, normalize_symbol
from services.security.credential_store import get_exchange_credentials
from services.security.exchange_factory import make_exchange
from services.os.app_paths import runtime_dir, ensure_dirs

ensure_dirs()
SNAPSHOT_DIR = runtime_dir() / "snapshots"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def _save_snapshot(obj: dict) -> str:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    p = SNAPSHOT_DIR / f"position_reconcile.{_tag()}.json"
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(p)

def _base_from_symbol(symbol: str) -> str:
    s = normalize_symbol(symbol)
    return s.split("/", 1)[0].strip() if "/" in s else s.strip()

def _local_net_positions_from_trades(trades: List[dict], bases_filter: Optional[set] = None) -> Dict[str, float]:
    out: dict[str, float] = {}
    for t in trades or []:
        sym = str(t.get("symbol") or "").strip()
        side = str(t.get("side") or "").lower().strip()
        qty = t.get("qty")
        if not sym or qty is None:
            continue
        try:
            q = float(qty)
        except Exception:
            continue
        base = _base_from_symbol(sym)
        if bases_filter and base not in bases_filter:
            continue
        out[base] = out.get(base, 0.0) + (q if side == "buy" else -q)
    return out

def _exchange_spot_balances(venue: str) -> dict:
    creds = get_exchange_credentials(venue)
    if not creds:
        return {"ok": False, "venue": venue, "reason": "missing_credentials"}
    ex = make_exchange(venue, creds, enable_rate_limit=True)
    try:
        bal = ex.fetch_balance()
        total = bal.get("total") if isinstance(bal, dict) else {}
        return {"ok": True, "venue": venue, "balances_total": {str(k).upper(): float(v) for k,v in total.items() if isinstance(v,(int,float))}}
    except Exception as e:
        return {"ok": False, "venue": venue, "reason": type(e).__name__, "error": str(e)[:700]}
    finally:
        if hasattr(ex, "close"):
            ex.close()

def _exchange_derivatives_positions(venue: str, symbols: Optional[List[str]] = None) -> dict:
    creds = get_exchange_credentials(venue)
    if not creds:
        return {"ok": False, "venue": venue, "reason": "missing_credentials"}
    ex = make_exchange(venue, creds, enable_rate_limit=True)
    try:
        if not getattr(ex, "has", {}).get("fetchPositions", False):
            return {"ok": False, "venue": venue, "reason": "fetchPositions_not_supported"}
        pos = ex.fetch_positions(symbols) if symbols else ex.fetch_positions()
        net: dict[str, float] = {}
        unknown = 0
        for p in pos or []:
            if not isinstance(p, dict):
                unknown += 1
                continue
            sym = str(p.get("symbol") or "").strip()
            if not sym:
                unknown += 1
                continue
            contracts = p.get("contracts")
            contract_size = p.get("contractSize") or p.get("contract_size")
            side = str(p.get("side") or "").lower().strip()
            amt = p.get("amount") or p.get("positionAmt") or p.get("position_amt")
            qty_base = None
            try:
                if contracts is not None and contract_size is not None:
                    qty_base = float(contracts) * float(contract_size)
                elif amt is not None:
                    qty_base = float(amt)
            except Exception:
                qty_base = None
            if qty_base is None:
                unknown += 1
                continue
            if side == "short":
                qty_base = -abs(qty_base)
            elif side == "long":
                qty_base = abs(qty_base)
            base = _base_from_symbol(sym)
            net[base] = net.get(base, 0.0) + qty_base
        if pos and not net:
            return {"ok": False, "venue": venue, "reason": "positions_uninterpretable", "rows": len(pos)}
        return {"ok": True, "venue": venue, "net_base": net, "rows": len(pos), "unknown_rows": unknown}
    except Exception as e:
        return {"ok": False, "venue": venue, "reason": type(e).__name__, "error": str(e)[:700]}
    finally:
        if hasattr(ex, "close"):
            ex.close()

def reconcile_positions(venue: str, symbols: Optional[List[str]] = None, *, mode: str = "spot", local_limit: int = 4000, tolerance_abs: float = 1e-8, tolerance_pct: float = 0.02, require_exchange_ok: bool = True) -> dict:
    v = venue.lower().strip()
    m = mode.lower().strip()
    syms = symbols or []
    syms_norm = normalize_symbols([str(s) for s in syms]).get("normalized", [])
    bases = {_base_from_symbol(s) for s in syms_norm} if syms_norm else None

    local = scan_local_journals(limit=int(local_limit), symbol=None)
    local_net = _local_net_positions_from_trades(local.get("trades", []) or [], bases_filter=bases)

    if m == "derivatives":
        exs = _exchange_derivatives_positions(v, syms_norm if syms_norm else None)
        if require_exchange_ok and not exs.get("ok", False):
            rep = {"ts": _now(), "venue": v, "mode": m, "ok": False, "reason": "exchange_positions_unavailable", "exchange": exs, "local": local}
            rep["snapshot_path"] = _save_snapshot(rep)
            return rep
        ex_map = exs.get("net_base") or {}
        exchange_meta = {k: exs.get(k) for k in ["ok","reason","error","rows","unknown_rows"]}
    else:
        exb = _exchange_spot_balances(v)
        if require_exchange_ok and not exb.get("ok", False):
            rep = {"ts": _now(), "venue": v, "mode": m, "ok": False, "reason": "exchange_balance_unavailable", "exchange": exb, "local": local}
            rep["snapshot_path"] = _save_snapshot(rep)
            return rep
        ex_map = {k: float(vv) for k,vv in (exb.get("balances_total") or {}).items()}
        exchange_meta = {k: exb.get(k) for k in ["ok","reason","error"]}

    tracked = set(local_net.keys())
    if bases:
        tracked |= set(bases)
    for b in ex_map.keys():
        if not bases or b in bases:
            tracked.add(b)

    mismatches = []
    details = []
    for b in sorted(tracked):
        ex_qty = float(ex_map.get(b,0.0))
        loc_qty = float(local_net.get(b,0.0))
        diff = abs(ex_qty - loc_qty)
        pct_base = max(abs(ex_qty), 1e-12)
        ok = diff <= tolerance_abs or diff <= pct_base * tolerance_pct
        row = {"base": b, "exchange_qty": ex_qty, "local_net_qty": loc_qty, "diff": diff, "ok": ok, "tolerance_abs": tolerance_abs, "tolerance_pct": tolerance_pct}
        details.append(row)
        if not ok:
            mismatches.append(row)

    rep = {"ts": _now(), "venue": v, "mode": m, "ok": len(mismatches) == 0 and exchange_meta.get("ok", True), "symbols_norm": syms_norm, "tracked_bases_count": len(tracked), "mismatch_count": len(mismatches), "mismatches": mismatches[:200], "details": details[:400], "exchange": exchange_meta, "local": local}
    rep["snapshot_path"] = _save_snapshot(rep)
    return rep

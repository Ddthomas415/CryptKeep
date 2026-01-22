python3 - <<'PY'
from pathlib import Path
import re

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        return
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")

# 1) Guard service: reads latest system_status snapshot and infers per-venue/symbol freshness + spread if available
write("services/execution/market_data_staleness_guard.py", r"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from services.admin.config_editor import load_user_yaml

SNAPSHOT_DIR = Path("runtime") / "snapshots"

def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)

def _latest_system_status() -> Optional[Path]:
    if not SNAPSHOT_DIR.exists():
        return None
    files = sorted(SNAPSHOT_DIR.glob("system_status.*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def _load_json(p: Path) -> Optional[dict]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def _to_ms(x) -> Optional[int]:
    if x is None:
        return None
    try:
        if isinstance(x, (int, float)):
            v = float(x)
            if v > 1e12:  # micro/nano-ish
                return int(v / 1e6)
            if v > 1e10:  # already ms
                return int(v)
            if v > 1e9:   # seconds
                return int(v * 1000)
            return int(v)
    except Exception:
        pass
    try:
        s = str(x).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None

def get_md_guard_config() -> dict:
    cfg = load_user_yaml()
    ex = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    return {
        "market_data_guard_enabled": bool(ex.get("market_data_guard_enabled", True)),
        "market_data_max_age_sec": int(ex.get("market_data_max_age_sec", 5) or 5),
        # spread guard (optional)
        "spread_guard_enabled": bool(ex.get("spread_guard_enabled", False)),
        "max_spread_bps": float(ex.get("max_spread_bps", 30.0) or 30.0),
    }

def _walk_find_tick(obj: Any, venue: str, symbol: str) -> dict | None:
    """
    Best-effort: find a dict containing venue+symbol and timestamp-like fields.
    We do not assume schema; we scan common places.
    """
    if isinstance(obj, dict):
        # direct match attempt
        v = str(obj.get("venue") or obj.get("exchange") or "").lower().strip()
        s = str(obj.get("symbol") or obj.get("pair") or obj.get("market") or "").strip()
        if v == venue and s == symbol:
            return obj

        # common containers
        for k in ("ticks", "tickers", "quotes", "markets", "cache", "cache_state", "market_data", "data"):
            if k in obj:
                found = _walk_find_tick(obj.get(k), venue, symbol)
                if found:
                    return found

        # scan all dict values
        for vv in obj.values():
            found = _walk_find_tick(vv, venue, symbol)
            if found:
                return found

    elif isinstance(obj, list):
        for it in obj:
            found = _walk_find_tick(it, venue, symbol)
            if found:
                return found

    return None

def _extract_ts_bid_ask(d: dict) -> tuple[Optional[int], Optional[float], Optional[float]]:
    ts = None
    bid = None
    ask = None

    # timestamp candidates
    for k in ("ts_ms", "timestamp_ms", "timestamp", "time", "last", "last_ts", "last_update_ts", "updated_at", "created_at"):
        if k in d:
            ts = _to_ms(d.get(k))
            if ts:
                break

    # bid/ask candidates
    for kb in ("bid", "best_bid", "b", "bid_price"):
        if kb in d:
            try: bid = float(d.get(kb))
            except Exception: pass
            if bid is not None:
                break
    for ka in ("ask", "best_ask", "a", "ask_price"):
        if ka in d:
            try: ask = float(d.get(ka))
            except Exception: pass
            if ask is not None:
                break

    # sometimes nested in "ticker" or "quote"
    for nest in ("ticker", "quote"):
        if nest in d and isinstance(d[nest], dict):
            nd = d[nest]
            if ts is None:
                for k in ("ts_ms", "timestamp", "time", "last_update_ts"):
                    if k in nd:
                        ts = _to_ms(nd.get(k))
                        if ts:
                            break
            if bid is None:
                for kb in ("bid", "bestBid", "best_bid"):
                    if kb in nd:
                        try: bid = float(nd.get(kb))
                        except Exception: pass
                        if bid is not None:
                            break
            if ask is None:
                for ka in ("ask", "bestAsk", "best_ask"):
                    if ka in nd:
                        try: ask = float(nd.get(ka))
                        except Exception: pass
                        if ask is not None:
                            break

    return ts, bid, ask

def evaluate_market_data_guard(venue: str, symbol: str) -> dict:
    c = get_md_guard_config()
    v = str(venue).lower().strip()
    s = str(symbol).strip()

    if not c["market_data_guard_enabled"]:
        return {"ok": True, "venue": v, "symbol": s, "enabled": False, "reason": "md_guard_disabled"}

    p = _latest_system_status()
    if not p or not p.exists():
        # fail-safe when enabled: no freshness proof
        return {"ok": False, "venue": v, "symbol": s, "enabled": True, "reason": "no_system_status_snapshot"}

    obj = _load_json(p)
    if not isinstance(obj, dict):
        return {"ok": False, "venue": v, "symbol": s, "enabled": True, "reason": "bad_system_status_snapshot", "path": str(p)}

    tick = _walk_find_tick(obj, v, s)
    if not isinstance(tick, dict):
        return {"ok": False, "venue": v, "symbol": s, "enabled": True, "reason": "no_tick_info_found", "snapshot_path": str(p)}

    ts_ms, bid, ask = _extract_ts_bid_ask(tick)
    if ts_ms is None:
        return {"ok": False, "venue": v, "symbol": s, "enabled": True, "reason": "tick_missing_timestamp", "snapshot_path": str(p), "tick_keys": list(tick.keys())[:80]}

    age_ms = _now_ms() - int(ts_ms)
    age_ok = age_ms <= int(c["market_data_max_age_sec"]) * 1000

    spread_bps = None
    spread_ok = True
    if c["spread_guard_enabled"] and bid is not None and ask is not None and bid > 0:
        spread_bps = ((ask - bid) / bid) * 10000.0
        spread_ok = float(spread_bps) <= float(c["max_spread_bps"])
    elif c["spread_guard_enabled"]:
        # if spread guard enabled but no bid/ask, fail-safe
        spread_ok = False

    ok = bool(age_ok and spread_ok)
    reason = "ok" if ok else ("stale_market_data" if not age_ok else "spread_too_wide_or_missing")

    return {
        "ok": ok,
        "venue": v,
        "symbol": s,
        "enabled": True,
        "reason": reason,
        "snapshot_path": str(p),
        "ts_ms": int(ts_ms),
        "age_ms": int(age_ms),
        "cfg": c,
        "bid": bid,
        "ask": ask,
        "spread_bps": spread_bps,
        "age_ok": bool(age_ok),
        "spread_ok": bool(spread_ok),
    }
""")

# 2) Router integration: call evaluate_market_data_guard and block if not ok
def patch_router(t: str) -> str:
    if "market_data_staleness_guard" in t and "evaluate_market_data_guard" in t:
        return t

    if "from services.execution.market_data_staleness_guard import evaluate_market_data_guard" not in t:
        t = t.replace(
            "from services.execution.latency_slippage_guard import evaluate_guard\n",
            "from services.execution.latency_slippage_guard import evaluate_guard\n"
            "from services.execution.market_data_staleness_guard import evaluate_market_data_guard\n"
        )

    marker = "# Exchange safety locks (defense-in-depth)"
    if marker in t and "gate='market_data_staleness_guard'" not in t:
        block = (
            "                # market_data_staleness_guard: block if tick is stale/missing (reads latest system_status snapshot)\n"
            "                try:\n"
            "                    mdg = evaluate_market_data_guard(str(venue), str(symbol_norm))\n"
            "                    meta['market_data_guard'] = mdg\n"
            "                    if not bool(mdg.get('ok')):\n"
            "                        meta['safety_ok'] = False\n"
            "                        try:\n"
            "                            did = str(meta.get('decision_id')) if isinstance(meta, dict) and meta.get('decision_id') else None\n"
            "                            _ = record_block(venue=str(venue), symbol=str(symbol_norm), side=str(side), qty=float(qty), price=float(limit_price), gate='market_data_staleness_guard', reason=str(mdg.get('reason')), details=mdg, meta=(dict(meta) if isinstance(meta, dict) else {}), decision_id=did)\n"
            "                        except Exception:\n"
            "                            pass\n"
            "                        try:\n"
            "                            log_event(str(venue), str(symbol_norm), 'order_blocked', ref_id=None, payload={\n"
            "                                'gate': 'market_data_staleness_guard',\n"
            "                                'reason_code': str(mdg.get('reason')),\n"
            "                                'reason': f\"market_data_staleness_guard:{mdg.get('reason')}\",\n"
            "                                'details': mdg,\n"
            "                                'source': 'router_market_data_staleness_guard',\n"
            "                            })\n"
            "                        except Exception:\n"
            "                            pass\n"
            "                        return {'ok': False, 'reason': f\"market_data_staleness_guard:{mdg.get('reason')}\", 'details': mdg, 'meta': meta}\n"
            "                except Exception:\n"
            "                    # fail safe: if guard check errors, block\n"
            "                    return {'ok': False, 'reason': 'market_data_staleness_guard:check_failed'}\n\n"
        )
        t = t.replace(marker, block + marker, 1)

    return t

patch("services/live_router/router.py", patch_router)

# 3) Config validation (execution fields)
def patch_config_editor(t: str) -> str:
    if "execution.market_data_max_age_sec" in t and "execution.max_spread_bps" in t and "execution.market_data_guard_enabled" in t:
        return t

    insert = """
    # Market data guards (optional)
    execution = cfg.get("execution", {})
    if execution is not None and not isinstance(execution, dict):
        errors.append("execution:must_be_mapping")
        execution = {}
    if isinstance(execution, dict):
        if "market_data_guard_enabled" in execution and execution["market_data_guard_enabled"] is not None and not _is_bool(execution["market_data_guard_enabled"]):
            errors.append("execution.market_data_guard_enabled:must_be_bool")
        if "market_data_max_age_sec" in execution and execution["market_data_max_age_sec"] is not None and not _is_int(execution["market_data_max_age_sec"]):
            errors.append("execution.market_data_max_age_sec:must_be_int")
        if "spread_guard_enabled" in execution and execution["spread_guard_enabled"] is not None and not _is_bool(execution["spread_guard_enabled"]):
            errors.append("execution.spread_guard_enabled:must_be_bool")
        if "max_spread_bps" in execution and execution["max_spread_bps"] is not None:
            try:
                float(execution["max_spread_bps"])
            except Exception:
                errors.append("execution.max_spread_bps:must_be_number")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 4) Dashboard panel
def patch_dashboard(t: str) -> str:
    if "Market Data Staleness Guard" in t and "evaluate_market_data_guard" in t:
        return t

    add = r"""
st.divider()
st.header("Market Data Staleness Guard")

st.caption("Blocks order routing if tick data is stale or missing (when enabled). Reads the latest runtime/snapshots/system_status.*.json snapshot and tries to infer freshness for (venue, symbol).")

try:
    from services.execution.market_data_staleness_guard import evaluate_market_data_guard, get_md_guard_config
    from services.admin.config_editor import load_user_yaml, save_user_yaml
    from pathlib import Path as _Path
    import json as _json

    cfg = load_user_yaml()
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues = pf.get("venues") or ["binance","coinbase","gateio"]
    symbols = pf.get("symbols") or ["BTC/USDT"]

    venue = st.selectbox("Venue", [str(v).lower().strip() for v in venues], index=0, key="mdg_venue")
    symbol = st.selectbox("Symbol", [str(s) for s in symbols], index=0, key="mdg_symbol")

    st.subheader("Guard evaluation (now)")
    st.json(evaluate_market_data_guard(venue, symbol))

    st.subheader("Guard config (from user.yaml with defaults)")
    st.json(get_md_guard_config())

    # show latest system_status snapshot path and preview
    sd = _Path("runtime") / "snapshots"
    files = sorted(sd.glob("system_status.*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if sd.exists() else []
    if files:
        st.caption(f"Latest system_status snapshot: {files[0]}")
        with st.expander("Preview system_status snapshot (first ~16k chars)"):
            st.code(files[0].read_text(encoding="utf-8")[:16000], language="json")
    else:
        st.warning("No system_status snapshots found yet. If md guard is enabled, routing will be blocked until at least one snapshot exists.")

    st.subheader("Edit market-data guard thresholds (safe write)")
    ex = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}

    cur_en = bool(ex.get("market_data_guard_enabled", True))
    cur_age = int(ex.get("market_data_max_age_sec", 5) or 5)
    cur_sen = bool(ex.get("spread_guard_enabled", False))
    cur_sp  = float(ex.get("max_spread_bps", 30.0) or 30.0)

    en = st.checkbox("execution.market_data_guard_enabled", value=cur_en)
    age = st.number_input("execution.market_data_max_age_sec", min_value=1, max_value=600, value=cur_age, step=1)
    sen = st.checkbox("execution.spread_guard_enabled", value=cur_sen)
    spb = st.number_input("execution.max_spread_bps", min_value=0.0, max_value=5000.0, value=cur_sp, step=1.0)

    new_cfg = dict(cfg)
    new_ex = dict(ex)
    new_ex["market_data_guard_enabled"] = bool(en)
    new_ex["market_data_max_age_sec"] = int(age)
    new_ex["spread_guard_enabled"] = bool(sen)
    new_ex["max_spread_bps"] = float(spb)
    new_cfg["execution"] = new_ex

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Dry-run (diff only) — market data guard"):
            out = save_user_yaml(new_cfg, create_backup=False, dry_run=True)
            st.code(out.get("diff",""), language="diff")
            if not out.get("ok"):
                st.error(out.get("validation"))
    with c2:
        if st.button("Save — market data guard (backup + atomic)"):
            out = save_user_yaml(new_cfg, create_backup=True, dry_run=False)
            if out.get("ok"):
                st.success({"written": out.get("written"), "backup": out.get("backup")})
            else:
                st.error(out.get("validation"))
            st.code(out.get("diff",""), language="diff")

except Exception as e:
    st.error(f"Market data guard panel failed: {type(e).__name__}: {e}")
"""
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 5) CHECKPOINTS
def patch_cp(t: str) -> str:
    if "## CR) Market Data Staleness Guard" in t:
        return t
    return t + (
        "\n## CR) Market Data Staleness Guard\n"
        "- ✅ CR1: evaluate_market_data_guard reads latest system_status snapshot and infers (venue, symbol) freshness\n"
        "- ✅ CR2: Optional spread guard using bid/ask if present (fail-safe if enabled but missing bid/ask)\n"
        "- ✅ CR3: Router blocks when guard fails (gate=market_data_staleness_guard)\n"
        "- ✅ CR4: Dashboard panel to evaluate guard, preview snapshot, and safely edit thresholds\n"
    )

patch("CHECKPOINTS.md", patch_cp)

print("OK: Phase 96 applied (market-data staleness/spread guard + router gate + UI + config validation + checkpoints).")
PY


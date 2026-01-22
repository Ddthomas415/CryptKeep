# apply_phase114.py - Phase 114 launcher (symbol routing + market quality guard)
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

# 1) Symbol Router (normalize venue + symbol, optional explicit mapping)
write("services/market_data/symbol_router.py", r'''from __future__ import annotations
from services.admin.config_editor import load_user_yaml

VENUE_ALIASES = {
    "gate.io": "gateio",
    "gate": "gateio",
    "gateio": "gateio",
    "binance": "binance",
    "coinbase": "coinbase",
    "coinbasepro": "coinbase",
}

def normalize_venue(venue: str) -> str:
    v = (venue or "").strip().lower()
    return VENUE_ALIASES.get(v, v)

def normalize_symbol(symbol: str) -> str:
    """
    Accepts:
      - BTC/USD (preferred)
      - BTC-USD (converted -> BTC/USD)
      - btc/usdt (uppercased)
    """
    s = (symbol or "").strip()
    if "-" in s and "/" not in s:
        s = s.replace("-", "/")
    parts = s.split("/")
    if len(parts) == 2:
        return f"{parts[0].upper()}/{parts[1].upper()}"
    return s.upper()

def _mapping_cfg() -> dict:
    cfg = load_user_yaml()
    sr = cfg.get("symbol_router") if isinstance(cfg.get("symbol_router"), dict) else {}
    m = sr.get("map") if isinstance(sr.get("map"), dict) else {}
    return m

def map_symbol(venue: str, canonical_symbol: str) -> str:
    v = normalize_venue(venue)
    sym = normalize_symbol(canonical_symbol)
    m = _mapping_cfg()
    per = m.get(sym) if isinstance(m.get(sym), dict) else None
    if isinstance(per, dict):
        mapped = per.get(v)
        if mapped:
            return normalize_symbol(str(mapped))
    return sym
''')

# 2) Market Quality Guard (stale ticks + spread bps)
write("services/risk/market_quality_guard.py", r'''from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Optional
from services.admin.config_editor import load_user_yaml
from services.market_data.tick_reader import get_best_bid_ask_last

def _cfg() -> dict:
    cfg = load_user_yaml()
    g = cfg.get("market_quality_guard") if isinstance(cfg.get("market_quality_guard"), dict) else {}
    return {
        "enabled": bool(g.get("enabled", True)),
        "max_tick_age_sec": float(g.get("max_tick_age_sec", 3.0) or 3.0),
        "max_spread_bps": float(g.get("max_spread_bps", 80.0) or 80.0),
        "require_bid_ask": bool(g.get("require_bid_ask", True)),
        "block_when_unknown": bool(g.get("block_when_unknown", True)),
    }

def check(venue: str, symbol: str) -> dict:
    cfg = _cfg()
    if not cfg["enabled"]:
        return {"ok": True, "enabled": False}
    q = get_best_bid_ask_last(venue, symbol)
    if not q:
        return {"ok": (not cfg["block_when_unknown"]), "reason": "no_quote"}
    ts_ms = int(q.get("ts_ms") or 0)
    age = 9999.0
    if ts_ms > 0:
        age = (time.time() * 1000.0 - float(ts_ms)) / 1000.0
    bid = q.get("bid")
    ask = q.get("ask")
    last = q.get("last")
    if cfg["require_bid_ask"] and (bid is None or ask is None):
        return {"ok": (not cfg["block_when_unknown"]), "reason": "missing_bid_ask", "age_sec": age, "bid": bid, "ask": ask, "last": last}
    spread_bps = _compute_spread_bps(bid, ask, last)
    if age > cfg["max_tick_age_sec"]:
        return {"ok": False, "reason": "stale_tick", "age_sec": age, "spread_bps": spread_bps}
    if spread_bps is None:
        return {"ok": (not cfg["block_when_unknown"]), "reason": "unknown_spread", "age_sec": age}
    if spread_bps > cfg["max_spread_bps"]:
        return {"ok": False, "reason": "spread_too_wide", "age_sec": age, "spread_bps": spread_bps}
    return {"ok": True, "age_sec": age, "spread_bps": spread_bps, "bid": bid, "ask": ask, "last": last}
''')

# 3) Patch tick_reader to normalize venue/symbol + compute spread helper
def patch_tick_reader(t: str) -> str:
    if "from services.market_data.symbol_router import normalize_venue, map_symbol" not in t:
        t = t.replace(
            "from services.os.app_paths import runtime_dir\n",
            "from services.os.app_paths import runtime_dir\nfrom services.market_data.symbol_router import normalize_venue, map_symbol\n",
            1
        )
    if "def _compute_spread_bps" not in t:
        t += "\n\n" + r"""
def _compute_spread_bps(bid, ask, last=None):
    try:
        if bid is None or ask is None:
            return None
        b = float(bid)
        a = float(ask)
        if b <= 0 or a <= 0:
            return None
        mid = (a + b) / 2.0
        if mid <= 0:
            return None
        return ((a - b) / mid) * 10000.0
    except Exception:
        return None
"""
    if "v = normalize_venue" not in t:
        t = t.replace(
            "v = str(venue).lower().strip()\n s = str(symbol).strip()\n",
            "v = normalize_venue(str(venue))\n s = map_symbol(v, str(symbol))\n",
            1
        )
    return t

patch("services/market_data/tick_reader.py", patch_tick_reader)

# 4) Patch paper_engine to use mapped symbol consistently
def patch_paper_engine(t: str) -> str:
    if "from services.market_data.symbol_router import normalize_venue, map_symbol" in t:
        return t
    t = t.replace(
        "from services.market_data.tick_reader import get_best_bid_ask_last, mid_price\n",
        "from services.market_data.tick_reader import get_best_bid_ask_last, mid_price\nfrom services.market_data.symbol_router import normalize_venue, map_symbol\n",
        1
    )
    t = t.replace(
        '"venue": str(venue).lower().strip(),\n "symbol": str(symbol).strip(),\n',
        '"venue": normalize_venue(str(venue)),\n "symbol": map_symbol(normalize_venue(str(venue)), str(symbol)),\n'
    )
    return t

patch("services/execution/paper_engine.py", patch_paper_engine)

# 5) Patch intent_consumer: market quality gate before submitting
def patch_intent_consumer(t: str) -> str:
    if "from services.risk.market_quality_guard import check as mq_check" in t:
        return t
    t = t.replace(
        "from services.execution.paper_engine import PaperEngine\n",
        "from services.execution.paper_engine import PaperEngine\nfrom services.risk.market_quality_guard import check as mq_check\n",
        1
    )
    needle = "out = eng.submit_order("
    if needle in t:
        t = t.replace(
            needle,
            " mq = mq_check(it['venue'], it['symbol'])\n"
            " if not mq.get('ok'):\n"
            "     _write_status({\n"
            "         'ok': True, 'status': 'running', 'ts': _now(),\n"
            "         'note': 'market_quality_blocked', 'blocked': mq,\n"
            "         'last_blocked_intent': it.get('intent_id')\n"
            "     })\n"
            "     continue\n\n"
            + needle,
            1
        )
    return t

patch("services/execution/intent_consumer.py", patch_intent_consumer)

# 6) Dashboard panel: Market Quality Monitor + symbol mapping hints
def patch_dashboard(t: str) -> str:
    if "Market Quality Monitor (Latency + Spread)" in t:
        return t
    add = r'''
st.divider()
st.header("Market Quality Monitor (Latency + Spread)")
st.caption("Blocks intent submission when tick data is stale or spreads are too wide. Also shows per-venue symbol routing (example: Coinbase often uses BTC/USD while others use BTC/USDT).")
try:
    import json as _json
    import time as _time
    from services.admin.config_editor import load_user_yaml
    from services.os.app_paths import runtime_dir
    from services.market_data.symbol_router import normalize_venue, normalize_symbol, map_symbol
    from services.market_data.tick_reader import get_best_bid_ask_last
    from services.risk.market_quality_guard import check as mq_check
    cfg = load_user_yaml()
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues = pf.get("venues") if isinstance(pf.get("venues"), list) else ["binance", "coinbase", "gateio"]
    symbols = pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USDT"]
    venues = [normalize_venue(str(v)) for v in venues]
    symbols = [normalize_symbol(str(s)) for s in symbols]
    sel_v = st.selectbox("Venue", venues, index=0)
    sel_s = st.selectbox("Canonical symbol", symbols, index=0)
    mapped = map_symbol(sel_v, sel_s)
    st.code(f"Mapped for {sel_v}: {sel_s} -> {mapped}", language="text")
    q = get_best_bid_ask_last(sel_v, sel_s)
    mq = mq_check(sel_v, sel_s)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Gate ok?", "YES" if mq.get("ok") else "NO")
    with c2:
        st.metric("age_sec", f"{mq.get('age_sec', '—')}")
    with c3:
        st.metric("spread_bps", f"{mq.get('spread_bps', '—')}")
    st.subheader("Quote")
    st.json(q or {"note": "no_quote_found_in_latest_snapshot_or_fallback"})
    st.subheader("Guard decision")
    st.json(mq)
    st.subheader("Latest system snapshot presence")
    latest = runtime_dir() / "snapshots" / "system_status.latest.json"
    st.caption(str(latest))
    st.write("exists:", latest.exists())
    with st.expander("How to override symbol routing (config/user.yaml)"):
        st.code(
            "symbol_router:\n"
            " map:\n"
            " \"BTC/USDT\":\n"
            " binance: \"BTC/USDT\"\n"
            " gateio: \"BTC/USDT\"\n"
            " coinbase: \"BTC/USD\"\n",
            language="yaml",
        )
except Exception as e:
    st.error(f"Market quality panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 7) Config validation
def patch_config_editor(t: str) -> str:
    if "market_quality_guard.max_spread_bps" in t and "symbol_router.map" in t:
        return t
    insert = """
    # Market quality guard (optional)
    mqg = cfg.get("market_quality_guard", {})
    if mqg is not None and not isinstance(mqg, dict):
        errors.append("market_quality_guard:must_be_mapping")
        mqg = {}
    if isinstance(mqg, dict):
        for k in ("enabled","require_bid_ask","block_when_unknown"):
            if k in mqg and mqg[k] is not None and not _is_bool(mqg[k]):
                errors.append(f"market_quality_guard.{k}:must_be_bool")
        for k in ("max_tick_age_sec","max_spread_bps"):
            if k in mqg and mqg[k] is not None and not _is_float(mqg[k]):
                errors.append(f"market_quality_guard.{k}:must_be_float")
    # Symbol router (optional)
    sr = cfg.get("symbol_router", {})
    if sr is not None and not isinstance(sr, dict):
        errors.append("symbol_router:must_be_mapping")
        sr = {}
    if isinstance(sr, dict):
        mp = sr.get("map", {})
        if mp is not None and not isinstance(mp, dict):
            errors.append("symbol_router.map:must_be_mapping")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 8) Default config in install.py
def patch_install_py(t: str) -> str:
    if "market_quality_guard:" in t and "symbol_router:" in t:
        return t
    block = (
        "symbol_router:\n"
        " map:\n"
        " \"BTC/USDT\":\n"
        " binance: \"BTC/USDT\"\n"
        " gateio: \"BTC/USDT\"\n"
        " coinbase: \"BTC/USD\"\n\n"
        "market_quality_guard:\n"
        " enabled: true\n"
        " max_tick_age_sec: 3.0\n"
        " max_spread_bps: 80.0\n"
        " require_bid_ask: true\n"
        " block_when_unknown: true\n\n"
    )
    if "preflight:\n" in t and "paper_trading:\n" in t:
        return t.replace("paper_trading:\n", block + "paper_trading:\n", 1)
    return t + "\n# Added by Phase 114\n" + block

patch("install.py", patch_install_py)

# 9) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DJ) Multi-Venue Routing + Market Quality Guard" in t:
        return t
    return t + (
        "\n## DJ) Multi-Venue Routing + Market Quality Guard\n"
        "- ✅ DJ1: Venue normalization (gate.io/gate → gateio) and symbol normalization (BTC-USD → BTC/USD)\n"
        "- ✅ DJ2: Optional per-venue symbol mapping via symbol_router.map (canonical → venue-specific)\n"
        "- ✅ DJ3: Market quality guard blocks intent submission on stale ticks or wide spreads\n"
        "- ✅ DJ4: Intent consumer integrates market quality gate (keeps intents queued for retry)\n"
        "- ✅ DJ5: Dashboard monitor for quote + age/spread + mapping examples\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 114 applied (symbol routing + market quality guard + consumer gate + dashboard + config + checkpoints).")
print("Next steps:")
print("  1. Restart intent consumer: python3 scripts/run_intent_consumer.py run")
print("  2. Check dashboard 'Market Quality Monitor' panel for quote + guard status")
print("  3. Submit paper order → see if market quality blocks/rejects")
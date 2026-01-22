# apply_phase115.py - Phase 115 launcher (multi-venue market view + ranked best venue + optional strategy auto-switch)
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

# 1) Multi-venue market view helper
write("services/market_data/multi_venue_view.py", r'''from __future__ import annotations
import time
from typing import List, Optional
from services.market_data.symbol_router import normalize_venue, normalize_symbol, map_symbol
from services.market_data.tick_reader import get_best_bid_ask_last
from services.risk.market_quality_guard import check as mq_check

def _age_sec(ts_ms: int | None) -> float | None:
    try:
        if not ts_ms:
            return None
        return (time.time() * 1000.0 - float(ts_ms)) / 1000.0
    except Exception:
        return None

def venue_rows(venues: List[str], canonical_symbol: str) -> list[dict]:
    sym = normalize_symbol(canonical_symbol)
    out = []
    for v0 in venues:
        v = normalize_venue(v0)
        mapped = map_symbol(v, sym)
        q = get_best_bid_ask_last(v, sym)
        bid = q.get("bid") if q else None
        ask = q.get("ask") if q else None
        last = q.get("last") if q else None
        ts_ms = int(q.get("ts_ms") or 0) if q else 0
        age = _age_sec(ts_ms) if ts_ms else None
        spread_bps = _compute_spread_bps(bid, ask, last)
        guard = mq_check(v, sym)
        out.append({
            "venue": v,
            "canonical_symbol": sym,
            "mapped_symbol": mapped,
            "bid": bid,
            "ask": ask,
            "last": last,
            "ts_ms": ts_ms if ts_ms else None,
            "age_sec": age,
            "spread_bps": spread_bps,
            "guard_ok": bool(guard.get("ok")),
            "guard_reason": guard.get("reason"),
        })
    return out

def rank_rows(rows: list[dict]) -> list[dict]:
    def key(r: dict):
        ok = 0 if r.get("guard_ok") else 1
        age = r.get("age_sec")
        spread = r.get("spread_bps")
        age_key = float(age) if age is not None else 1e9
        spread_key = float(spread) if spread is not None else 1e9
        return (ok, age_key, spread_key, str(r.get("venue") or ""))
    return sorted(rows, key=key)

def best_venue(venues: List[str], canonical_symbol: str, *, require_ok: bool = True) -> dict | None:
    rows = rank_rows(venue_rows(venues, canonical_symbol))
    if not rows:
        return None
    if require_ok:
        for r in rows:
            if r.get("guard_ok"):
                return r
        return None
    return rows[0]
''')

# 2) Patch Strategy Runner to optionally choose best venue
def patch_strategy_runner(t: str) -> str:
    if "auto_select_best_venue" in t and "venue_candidates" in t and "switch_only_when_blocked" in t:
        return t
    if "from services.market_data.symbol_router import normalize_venue, map_symbol" not in t:
        t = t.replace(
            "from services.market_data.tick_reader import get_best_bid_ask_last, mid_price\n",
            "from services.market_data.tick_reader import get_best_bid_ask_last, mid_price\nfrom services.market_data.symbol_router import normalize_venue, map_symbol\n",
            1
        )
    if "from services.market_data.multi_venue_view import best_venue" not in t:
        t = t.replace(
            "from services.market_data.symbol_router import normalize_venue, map_symbol\n",
            "from services.market_data.symbol_router import normalize_venue, map_symbol\nfrom services.market_data.multi_venue_view import best_venue\n",
            1
        )
    if "from services.risk.market_quality_guard import check as mq_check" not in t:
        t = t.replace(
            "from services.market_data.multi_venue_view import best_venue\n",
            "from services.market_data.multi_venue_view import best_venue\nfrom services.risk.market_quality_guard import check as mq_check\n",
            1
        )
    # Ensure _cfg() includes new keys
    def patch_cfg_block(txt: str) -> str:
        if '"auto_select_best_venue"' in txt:
            return txt
        return txt.replace(
            '"sell_full_position": bool(s.get("sell_full_position", True)),\n }\n',
            '"sell_full_position": bool(s.get("sell_full_position", True)),\n'
            ' "auto_select_best_venue": bool(s.get("auto_select_best_venue", False)),\n'
            ' "switch_only_when_blocked": bool(s.get("switch_only_when_blocked", True)),\n'
            ' "venue_candidates": (s.get("venue_candidates") if isinstance(s.get("venue_candidates"), list) else None),\n'
            " }\n",
            1
        )
    t = patch_cfg_block(t)
    # Patch _fetch_mid to use mapped symbol for CCXT fallback
    if "mapped_symbol = map_symbol" not in t:
        t = t.replace(
            " ex = make_exchange(cfg[\"venue\"], {\"apiKey\": None, \"secret\": None}, enable_rate_limit=True)\n try:\n t = ex.fetch_ticker(cfg[\"symbol\"])",
            " mapped_symbol = map_symbol(cfg[\"venue\"], cfg[\"symbol\"])\n"
            " ex = make_exchange(cfg[\"venue\"], {\"apiKey\": None, \"secret\": None}, enable_rate_limit=True)\n"
            " try:\n t = ex.fetch_ticker(mapped_symbol)"
        )
    # Inject venue selection logic in run_forever loop before _fetch_mid call
    if "best_venue(" not in t:
        marker = " tick = _fetch_mid(cfg)\n"
        if marker in t:
            inject = (
                " # Optional: choose best venue\n"
                " if bool(cfg.get('auto_select_best_venue')):\n"
                "     candidates = cfg.get('venue_candidates')\n"
                "     if not isinstance(candidates, list) or not candidates:\n"
                "         # fall back to preflight venues if present\n"
                "         base_cfg = load_user_yaml()\n"
                "         pf = base_cfg.get('preflight') if isinstance(base_cfg.get('preflight'), dict) else {}\n"
                "         candidates = pf.get('venues') if isinstance(pf.get('venues'), list) else [cfg['venue']]\n"
                "     candidates = [normalize_venue(str(v)) for v in candidates]\n"
                "     current_venue = normalize_venue(cfg['venue'])\n"
                "     cfg['venue'] = current_venue\n"
                "\n"
                "     if bool(cfg.get('switch_only_when_blocked', True)):\n"
                "         g = mq_check(cfg['venue'], cfg['symbol'])\n"
                "         if not g.get('ok'):\n"
                "             bv = best_venue(candidates, cfg['symbol'], require_ok=True)\n"
                "             if bv and bv.get('venue') and bv['venue'] != cfg['venue']:\n"
                "                 cfg['venue'] = str(bv['venue'])\n"
                "     else:\n"
                "         bv = best_venue(candidates, cfg['symbol'], require_ok=True)\n"
                "         if bv and bv.get('venue'):\n"
                "             cfg['venue'] = str(bv['venue'])\n"
                "\n"
                + marker
            )
            t = t.replace(marker, inject, 1)
    return t

patch("services/strategy/ema_crossover_runner.py", patch_strategy_runner)

# 3) Dashboard: multi indicating table (ranked)
def patch_dashboard(t: str) -> str:
    if "Multi-Venue Market View (Ranked)" in t:
        return t
    add = r'''
st.divider()
st.header("Multi-Venue Market View (Ranked)")
st.caption("Shows all venues side-by-side for a canonical symbol (routing/mapping applied). Ranked by: guard_ok → age_sec → spread_bps.")
try:
    import pandas as pd
    from services.admin.config_editor import load_user_yaml
    from services.market_data.symbol_router import normalize_venue, normalize_symbol
    from services.market_data.multi_venue_view import venue_rows, rank_rows, best_venue
    cfg = load_user_yaml()
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues = pf.get("venues") if isinstance(pf.get("venues"), list) else ["binance", "coinbase", "gateio"]
    symbols = pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USDT"]
    venues = [normalize_venue(str(v)) for v in venues]
    symbols = [normalize_symbol(str(s)) for s in symbols]
    sym = st.selectbox("Canonical symbol", symbols, index=0)
    rows = rank_rows(venue_rows(venues, sym))
    df = pd.DataFrame(rows)
    bv = best_venue(venues, sym, require_ok=True)
    if bv:
        st.success({"best_venue": bv.get("venue"), "mapped_symbol": bv.get("mapped_symbol"), "age_sec": bv.get("age_sec"), "spread_bps": bv.get("spread_bps")})
    else:
        st.warning("No venue currently passes the market quality guard for this symbol.")
    st.dataframe(df, use_container_width=True, height=320)
except Exception as e:
    st.error(f"Multi-venue panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 4) Config validation additions (strategy_runner auto venue + candidates)
def patch_config_editor(t: str) -> str:
    if "strategy_runner.auto_select_best_venue" in t and "strategy_runner.venue_candidates" in t:
        return t
    insert = """
        # auto venue selection options
        if "auto_select_best_venue" in sr and sr["auto_select_best_venue"] is not None and not _is_bool(sr["auto_select_best_venue"]):
            errors.append("strategy_runner.auto_select_best_venue:must_be_bool")
        if "switch_only_when_blocked" in sr and sr["switch_only_when_blocked"] is not None and not _is_bool(sr["switch_only_when_blocked"]):
            errors.append("strategy_runner.switch_only_when_blocked:must_be_bool")
        if "venue_candidates" in sr and sr["venue_candidates"] is not None:
            if not isinstance(sr["venue_candidates"], list):
                errors.append("strategy_runner.venue_candidates:must_be_list")
            else:
                for i, v in enumerate(sr["venue_candidates"]):
                    try:
                        str(v)
                    except Exception:
                        errors.append(f"strategy_runner.venue_candidates[{i}]:must_be_string")
"""
    anchor = 'for k in ("allow_first_signal_trade","use_ccxt_fallback","position_aware","sell_full_position")'
    if anchor in t:
        return t.replace(anchor, anchor + insert, 1)
    ok_anchor = "ok = len(errors) == 0"
    if ok_anchor in t:
        return t.replace(ok_anchor, insert + "\n" + ok_anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 5) install.py defaults: add fields to strategy_runner block
def patch_install_py(t: str) -> str:
    if "auto_select_best_venue" in t and "venue_candidates" in t:
        return t
    if "strategy_runner:\n" not in t:
        return t
    t2 = t.replace(
        " symbol: \"BTC/USDT\"\n",
        " symbol: \"BTC/USDT\"\n"
        " auto_select_best_venue: false\n"
        " switch_only_when_blocked: true\n"
        " venue_candidates: [\"binance\", \"coinbase\", \"gateio\"]\n",
        1
    )
    return t2

patch("install.py", patch_install_py)

# 6) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DK) Multi-Venue Market View + Best Venue Selection" in t:
        return t
    return t + (
        "\n## DK) Multi-Venue Market View + Best Venue Selection\n"
        "- ✅ DK1: Multi-venue market view ranks venues by guard_ok → age_sec → spread_bps\n"
        "- ✅ DK2: Dashboard panel shows per-venue quote metrics and the current best venue\n"
        "- ✅ DK3: Strategy Runner optional auto_select_best_venue (default off) with safe switching (only when blocked)\n"
        "- ✅ DK4: Strategy Runner CCXT fallback uses mapped_symbol for the chosen venue\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 115 applied (multi-venue market view + ranked best venue + optional strategy auto-switch + config + checkpoints).")
print("Next steps:")
print("  1. Restart strategy runner: python3 scripts/run_strategy_runner.py run")
print("  2. Check dashboard 'Multi-Venue Market View' panel for ranked venues")
print("  3. Test auto-switch: set strategy_runner.auto_select_best_venue: true in config/user.yaml, restart runner")
import streamlit as st
import json
from pathlib import Path
import subprocess
import sys
import time
import pandas as pd

st.set_page_config(page_title="Crypto Bot Pro", layout="wide")
st.title("Crypto Bot Pro - Dev Mode")

# Quick start & Feeds
col1, col2 = st.columns(2)
with col1:
    st.subheader("Quick start")
    st.code("docker compose up -d\n# or docker compose up -d --build", language="bash")
with col2:
    st.subheader("Feeds")
    st.write("Set env vars to control symbols:")
    st.code(
        "CBP_BINANCE_SYMBOLS=btcusdt,ethusdt\n"
        "CBP_COINBASE_PRODUCTS=BTC-USD,ETH-USD\n"
        "CBP_GATEIO_PAIRS=BTC_USDT,ETH_USDT\n"
        "CBP_CHANNELS=trades,book_l2\n"
        "CBP_FEEDS=binance,coinbase,gateio",
        language="text",
    )

st.divider()

# Live Enable Wizard (Phase 162)
st.header("Live Enable Wizard (Safe Workflow)")
try:
    from services.execution.live_arming import issue_token, status as token_status
    from services.execution.live_preflight import run_preflight
    from services.execution.live_enable import enable_live
    from services.admin.config_editor import load_user_yaml
    cfg = load_user_yaml()
    lt = cfg.get("live_trading", {}) if isinstance(cfg.get("live_trading"), dict) else {}
    st.subheader("Current live flags")
    st.json({"enabled": lt.get("enabled"), "dry_run": lt.get("dry_run")})
    c1, c2 = st.columns(2)
    with c1:
        ttl = st.number_input("ARM token TTL (minutes)", min_value=5, max_value=180, value=30, step=5)
        if st.button("Generate ARM token"):
            tok = issue_token(ttl_minutes=int(ttl))
            st.success("Token generated (copy it now; it will not be shown again after you refresh).")
            st.code(tok.get("token"))
            st.json({"expires_epoch": tok.get("expires_epoch"), "state_path": tok.get("path")})
    with c2:
        st.subheader("Token status (hash only)")
        st.json(token_status())
    st.subheader("Checklist (must be all checked)")
    checklist = {
        "i_understand_live_risk": st.checkbox("I understand live trading can lose money", value=False),
        "api_keys_configured": st.checkbox("API keys are configured for the venues I selected", value=False),
        "risk_limits_set": st.checkbox("Risk limits are set (min/max order, max position, max daily trades)", value=False),
        "dry_run_tested": st.checkbox("I tested strategies in dry_run and reviewed logs/leaderboards", value=False),
        "i_accept_no_guarantees": st.checkbox("I accept there are no guarantees (latency, slippage, outages)", value=False),
    }
    st.subheader("Preflight (read-only checks)")
    if st.button("Run preflight"):
        pre = run_preflight()
        st.json(pre)
    st.subheader("Enable live (sets live_trading.dry_run = false)")
    token_in = st.text_input("Paste ARM token here", value="", type="password")
    if st.button("Enable LIVE (dry_run=false)"):
        out = enable_live(token=token_in.strip(), checklist=checklist)
        if out.get("ok"):
            st.success("LIVE enabled: dry_run is now false.")
        else:
            st.error("LIVE enable failed.")
        st.json(out)
except Exception as e:
    st.error(f"Live Enable Wizard failed: {type(e).__name__}: {e}")

# Manual Intent Enqueue (Paper/Live)
st.divider()
st.header("Manual Intent Enqueue (Paper/Live)")
with st.form("intent_form"):
    is_live = st.checkbox("Live", value=False, key="intent_live")
    venue = st.selectbox("Venue", ["coinbase", "gateio"], key="intent_venue")
    symbol = st.text_input("Symbol", "BTC/USDT", key="intent_symbol")
    side = st.selectbox("Side", ["buy", "sell"], key="intent_side")
    qty = st.number_input("Quantity", min_value=0.0001, value=0.0001, step=0.0001, key="intent_qty")
    submitted = st.form_submit_button("Enqueue Intent")

    if submitted:
        st.info(f"Enqueuing {'LIVE' if is_live else 'PAPER'} intent...")

# Tick Publisher
st.divider()
st.header("Tick Publisher")
c1, c2 = st.columns(2)
with c1:
    if st.button("Start", key="tick_start"):
        subprocess.Popen([sys.executable, "scripts/run_tick_publisher.py", "run"])
        st.success("Started")
with c2:
    if st.button("Stop", key="tick_stop"):
        subprocess.Popen([sys.executable, "scripts/run_tick_publisher.py", "stop"])
        st.success("Stopped")

# System Health + Snapshot
st.divider()
st.header("System Health + Snapshot")
try:
    p = Path("runtime/snapshots/system_status.latest.json")
    if p.exists():
        data = json.loads(p.read_text())
        st.subheader("Market Snapshot")
        prices = []
        for v, vd in data.get("venues", {}).items():
            prices.append({
                "Venue": v,
                "OK": vd.get("ok", False),
                "Bid": vd.get("bid", "—"),
                "Ask": vd.get("ask", "—"),
                "Last": vd.get("last", "—"),
                "Reason": vd.get("reason", "")
            })
        st.dataframe(pd.DataFrame(prices), width='stretch')
    else:
        st.warning("No snapshot")
except Exception as e:
    st.error(f"Health failed: {e}")

# Signal Inbox
st.divider()
st.header("Signal Inbox")
st.info("Webhook: POST http://127.0.0.1:8787/signal")
st.code('''{ "symbol": "BTC/USDT", "action": "buy", "confidence": 0.7 }''', language="json")

# Signal Learning
st.divider()
st.header("Signal Learning v1")
if st.button("Compute Reliability", key="learning_compute"):
    st.info("Computing... (stub)")

# Adaptive Meta-Strategy
st.divider()
st.header("Adaptive Meta-Strategy")
if st.button("Run Meta", key="meta_run"):
    st.info("Running... (stub)")

# Config Editor
st.divider()
st.header("Config Editor")
if st.button("Open Editor", key="config_open"):
    st.info("Editor opening... (stub)")

# Live Trading
st.divider()
st.header("Live Trading")
if st.button("Enqueue Live", key="live_enqueue"):
    st.info("Live enqueue... (stub)")

st.caption("Phase 162 applied. Dashboard fully restored. Test Live Enable Wizard above.")


st.divider()
st.header("Why was my order blocked? (Idempotency Inspector)")

st.caption("Shows the most recent idempotent order attempts and the exact failure payloads (limits/rounding/retries/exchange errors).")

try:
    import pandas as pd
    from services.execution.idempotency_inspector import list_recent, filter_rows

    c1, c2, c3 = st.columns(3)
    with c1:
        v = st.selectbox("Filter venue", ["", "binance", "coinbase", "gateio"], index=0, key="idem_f_v")
    with c2:
        s = st.text_input("Filter symbol", value="", key="idem_f_s", help="Example: BTC/USDT")
    with c3:
        lim = st.number_input("Rows", min_value=10, max_value=500, value=80, step=10, key="idem_f_n")

    if st.button("Load recent idempotency rows"):
        data = list_recent(limit=int(lim))
        if not data.get("ok"):
            st.error(str(data))
        else:
            rows = filter_rows(data.get("rows", []), venue=v or None, symbol=s or None)
            st.subheader("DB location")
            st.json({"path": data.get("path"), "table": data.get("table")})

            # compact table view
            table_rows = []
            for r in rows:
                payload = r.get("payload") or {}
                err = None
                if isinstance(payload, dict):
                    err = payload.get("error") or payload.get("reason")
                table_rows.append({
                    "ts": r.get("ts"),
                    "status": r.get("status"),
                    "venue": r.get("venue"),
                    "symbol": r.get("symbol"),
                    "key": r.get("key"),
                    "payload_error": err,
                })

            if table_rows:
                df = pd.DataFrame(table_rows)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No rows matched your filter.")

            st.subheader("Click a row key and paste below to inspect full payload")
            pick_key = st.text_input("Inspect key", value="", key="idem_pick_key")
            if pick_key.strip():
                match = None
                for r in rows:
                    if str(r.get("key")) == pick_key.strip():
                        match = r
                        break
                if match is None:
                    st.warning("Key not found in filtered rows.")
                else:
                    st.json({
                        "key": match.get("key"),
                        "status": match.get("status"),
                        "venue": match.get("venue"),
                        "symbol": match.get("symbol"),
                        "ts": match.get("ts"),
                        "payload": match.get("payload"),
                        "raw_row": match.get("raw"),
                    })

except Exception as e:
    st.error(f"Idempotency inspector failed: {type(e).__name__}: {e}")

st.divider()
st.header("Preflight (Hard Gate)")

st.caption("Runs a strict readiness check for cockpit + live execution. If preflight fails, do NOT run live.")

try:
    from services.preflight.preflight import run_preflight
    venue = st.text_input("Venue", value="binance", key="pf_venue")
    syms = st.text_input("Symbols (comma)", value="BTC/USDT", key="pf_syms")

    if st.button("Run preflight"):
        sym_list = [s.strip().upper().replace("-", "/") for s in syms.split(",") if s.strip()]
        st.json(run_preflight(venue=venue, symbols=sym_list))

    st.code("CLI: python scripts/run_bot_safe.py --venue binance --symbols BTC/USDT", language="bash")
except Exception as e:
    st.error(f"Preflight panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Process Control")

st.caption("Start/Stop the bot safely. PID tracking prevents mystery background processes. Bot output is captured to data/logs/bot.log.")

try:
    import yaml
    from services.process.bot_process import status as bot_status, start_bot, stop_bot, stop_all
    from services.process.heartbeat import read_heartbeat
    from services.logging.app_logger import log_path
    from services.os.app_paths import data_dir

    c1, c2, c3 = st.columns(3)
    with c1:
        venue = st.text_input("Venue", value="binance", key="pc_venue")
    with c2:
        syms = st.text_input("Symbols (comma)", value="BTC/USDT", key="pc_syms")
    with c3:
        force = st.checkbox("Force start (unsafe)", value=False, key="pc_force")

    stt = bot_status()
    st.json(stt)

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Start Bot"):
            sym_list = [s.strip().upper().replace("-", "/") for s in syms.split(",") if s.strip()]
            st.json(start_bot(venue=venue, symbols=sym_list, force=bool(force)))
    with b2:
        if st.button("Stop Bot (hard)"):
            st.json(stop_bot(hard=True))
    with b3:
        if st.button("STOP ALL (hard)"):
            st.json(stop_all(hard=True))

    st.subheader("Heartbeat")
    st.code(yaml.safe_dump(read_heartbeat(), sort_keys=False)[:6000], language="yaml")

    st.subheader("Bot log (tail)")
    botlog = data_dir() / "logs" / "bot.log"
    n = st.number_input("Tail lines", min_value=50, max_value=5000, value=300, step=50, key="botlog_tail_n")
    if botlog.exists():
        txt = botlog.read_text(encoding="utf-8", errors="replace")
        lines = txt.splitlines()
        st.code("\n".join(lines[-int(n):]), language="text")
        st.download_button("Download bot.log", data=botlog.read_bytes(), file_name="bot.log", mime="text/plain")
    else:
        st.write("bot.log not found yet (start bot to generate).")

except Exception as e:
    st.error(f"Process Control panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Crash Snapshot")

st.caption("Forensics when the bot crashes or is hard-killed: controller writes crash_snapshot.json including log tails.")

try:
    import yaml
    from services.process.crash_snapshot import read_crash_snapshot

    snap = read_crash_snapshot()
    if not snap:
        st.info("No crash snapshot found yet.")
    else:
        st.code(yaml.safe_dump(snap, sort_keys=False)[:20000], language="yaml")

except Exception as e:
    st.error(f"Crash Snapshot panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Watchdog (Heartbeat Staleness)")

st.caption("Detects bot process that is alive but not ticking. On stale heartbeat: writes crash snapshot + turns kill switch ON. Optional auto-stop is OFF by default.")

try:
    import yaml
    from services.admin.config_editor import load_user_yaml
    from services.process.watchdog import run_watchdog_once, read_last

    cfg = load_user_yaml()
    st.json(cfg.get("watchdog", {}))

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Run watchdog check now"):
            st.json(run_watchdog_once())
    with c2:
        if st.button("Load last watchdog result"):
            st.json(read_last())

    st.subheader("Last watchdog result (stored)")
    st.code(yaml.safe_dump(read_last(), sort_keys=False)[:16000], language="yaml")

except Exception as e:
    st.error(f"Watchdog panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Supervisor Status")

st.caption("Supervisor runs cockpit + watchdog together. Use this to confirm there are no orphan processes.")

try:
    import yaml
    from services.process.supervisor_process import status as sup_status
    from services.os.app_paths import data_dir

    st.json(sup_status())

    log_dir = data_dir() / "logs"
    c_log = log_dir / "cockpit.log"
    w_log = log_dir / "watchdog.log"

    st.subheader("watchdog.log (tail)")
    if w_log.exists():
        txt = w_log.read_text(encoding="utf-8", errors="replace")
        lines = txt.splitlines()
        st.code("\n".join(lines[-200:]), language="text")
    else:
        st.write("watchdog.log not found yet.")

    st.subheader("cockpit.log (tail)")
    if c_log.exists():
        txt = c_log.read_text(encoding="utf-8", errors="replace")
        lines = txt.splitlines()
        st.code("\n".join(lines[-200:]), language="text")
    else:
        st.write("cockpit.log not found yet.")

except Exception as e:
    st.error(f"Supervisor Status panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Watchdog Control")

st.caption("Runs the watchdog loop as a managed background process (PID-tracked). Use this if you are NOT running Supervisor mode.")

try:
    import yaml
    from services.process.watchdog_process import status as wd_status, start_watchdog, stop_watchdog, clear_stale
    from services.os.app_paths import data_dir

    st.json(wd_status())

    c1, c2, c3 = st.columns(3)
    with c1:
        interval = st.number_input("Interval (sec)", min_value=5, max_value=300, value=15, step=5, key="wd_int")
        if st.button("Start Watchdog Loop"):
            st.json(start_watchdog(interval_sec=int(interval)))
    with c2:
        if st.button("Stop Watchdog (soft)"):
            st.json(stop_watchdog(hard=False))
        if st.button("Stop Watchdog (hard)"):
            st.json(stop_watchdog(hard=True))
    with c3:
        if st.button("Clear stale PID file"):
            st.json(clear_stale())

    st.subheader("watchdog_loop.log (tail)")
    p = data_dir() / "logs" / "watchdog_loop.log"
    if p.exists():
        txt = p.read_text(encoding="utf-8", errors="replace")
        lines = txt.splitlines()
        st.code("\n".join(lines[-200:]), language="text")
        st.download_button("Download watchdog_loop.log", data=p.read_bytes(), file_name="watchdog_loop.log", mime="text/plain")
    else:
        st.write("watchdog_loop.log not found yet.")

except Exception as e:
    st.error(f"Watchdog Control panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Order Audit Viewer")

st.caption("Read-only view of data/execution_audit.sqlite (orders + fills). This is the truth-source for what place_order attempted and what it recorded.")

try:
    from storage.execution_audit_reader import db_exists, DB_PATH, list_orders, list_fills, list_statuses

    if not db_exists():
        st.info(f"No audit DB yet at: {DB_PATH}. Run a dry-run order: python scripts/place_order_smoke.py ...")
    else:
        st.write(f"DB: {DB_PATH}")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            limit = st.number_input("Limit", min_value=10, max_value=2000, value=200, step=10, key="audit_limit")
        with c2:
            venue = st.text_input("Venue filter", value="", key="audit_venue")
        with c3:
            symbol = st.text_input("Symbol filter", value="", key="audit_symbol")
        with c4:
            statuses = [""] + (list_statuses() or [])
            status = st.selectbox("Status filter", options=statuses, index=0, key="audit_status")

        v = venue.strip().lower() or None
        s = symbol.strip().upper() or None
        stt = status.strip() or None

        orders = list_orders(limit=int(limit), venue=v, symbol=s, status=stt)
        st.subheader("Orders")
        try:
            import pandas as pd
            st.dataframe(pd.DataFrame(orders))
        except Exception:
            st.json(orders[:200])

        st.subheader("Fills (recent)")
        exid = st.text_input("Filter by exchange_order_id (optional)", value="", key="audit_exid")
        fills = list_fills(limit=min(int(limit), 500), venue=v, symbol=s, exchange_order_id=(exid.strip() or None))
        try:
            import pandas as pd
            st.dataframe(pd.DataFrame(fills))
        except Exception:
            st.json(fills[:200])

except Exception as e:
    st.error(f"Order Audit Viewer failed: {type(e).__name__}: {e}")

st.subheader("Alert health (last send)")
try:
    from services.alerts.alert_dispatcher import read_last_send
    st.json(read_last_send())
except Exception as e:
    st.error(f"Alert health read failed: {type(e).__name__}: {e}")

st.divider()
st.header("Startup Status")

st.caption("Live start is gated by a recent successful startup reconciliation (configurable). This panel shows the last status and lets you run it now.")

try:
    from services.admin.config_editor import load_user_yaml
    from services.execution.exchange_provider import get_exchange
    from services.execution.startup_reconcile import run_startup_reconciliation
    from services.execution.startup_status import get_status, is_fresh

    cfg = load_user_yaml()
    sr_cfg = cfg.get("startup_reconciliation", {}) if isinstance(cfg.get("startup_reconciliation"), dict) else {}

    venue = st.text_input("Venue", value=str((cfg.get("venues", {}) or {}).get("default_venue") or "binance"), key="ss_venue")
    within = st.number_input("Freshness window (hours)", min_value=1, max_value=168, value=int(sr_cfg.get("fresh_within_hours", 24)), step=1, key="ss_within")
    st.json(is_fresh(venue=venue, within_hours=int(within)))
    st.json(get_status(venue=venue))

    syms = st.text_input("Symbols (comma)", value="BTC/USDT", key="ss_syms")
    dry_run = st.checkbox("Treat as dry_run/paper", value=True, key="ss_dry")

    if st.button("Run startup reconciliation now (network)"):
        ex = get_exchange(venue=venue, sandbox=False)
        sym_list = [s.strip() for s in syms.split(",") if s.strip()]
        st.json(run_startup_reconciliation(ex=ex, cfg=cfg, venue=venue, symbols=sym_list, dry_run=bool(dry_run)))

except Exception as e:
    st.error(f"Startup Status panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Strategy Selector")

st.caption("Select strategy via config: strategy.name. Only EMA cross is enabled by default; others are safe hold until enabled.")

try:
    from services.admin.config_editor import load_user_yaml
    from services.strategies.registry import list_strategies, get_strategy

    cfg = load_user_yaml()
    strat_cfg = cfg.get("strategy", {}) if isinstance(cfg.get("strategy"), dict) else {}
    current = str(strat_cfg.get("name", "ema_cross")).strip().lower()

    st.write("Available strategies:", list_strategies())
    st.json({"current": current, "strategy_config": strat_cfg})

    # Quick sanity: show selected strategy object name
    st.json({"selected": get_strategy(current).name})

except Exception as e:
    st.error(f"Strategy Selector panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("WS Feature Blacklist")

st.caption("Auto-disabled WS features (per venue+symbol+feature). You can clear entries to re-enable.")

try:
    from services.marketdata.ws_feature_blacklist import list_items, clear_all, clear_one

    items = list_items()
    st.json({"path": items.get("path"), "count": len((items.get("items") or {}).keys())})

    st.subheader("Items")
    st.json(items.get("items", {}))

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Clear ALL"):
            st.json(clear_all())
    with c2:
        venue = st.text_input("Venue", value="binance", key="bl_v")
        symbol = st.text_input("Symbol", value="BTC/USDT", key="bl_s")
        feature = st.selectbox("Feature", options=["watch_order_book","watch_trades"], index=0, key="bl_f")
        if st.button("Clear ONE"):
            st.json(clear_one(venue=venue, symbol=symbol, feature=feature))

except Exception as e:
    st.error(f"Blacklist panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Strategy Selector + Presets")

st.caption("Select a strategy, tune parameters, and write back to config. Records a governance config_change event.")

try:
    import yaml
    from services.admin.config_editor import load_user_yaml, save_user_yaml
    from services.governance.config_change_log import record_config_change

    cfg = load_user_yaml()
    before = dict(cfg)

    st_cfg = cfg.get("strategy", {}) if isinstance(cfg.get("strategy"), dict) else {}

    strat = st.selectbox(
        "Strategy",
        ["ema_cross", "mean_reversion_rsi", "breakout_donchian"],
        index=["ema_cross","mean_reversion_rsi","breakout_donchian"].index(str(st_cfg.get("name","ema_cross")) if str(st_cfg.get("name","ema_cross")) in ["ema_cross","mean_reversion_rsi","breakout_donchian"] else "ema_cross"),
        key="strat_name",
    )
    trade_enabled = st.checkbox("trade_enabled", value=bool(st_cfg.get("trade_enabled", True)), key="strat_enabled")

    # presets (safe defaults)
    preset = st.selectbox("Preset", ["Custom", "Conservative", "Balanced", "Aggressive"], index=0, key="strat_preset")

    proposed = dict(cfg)
    proposed.setdefault("strategy", {})
    s2 = proposed["strategy"] if isinstance(proposed["strategy"], dict) else {}
    s2["name"] = strat
    s2["trade_enabled"] = bool(trade_enabled)

    if strat == "ema_cross":
        if preset != "Custom":
            if preset == "Conservative":
                s2["ema_fast"], s2["ema_slow"] = 12, 35
            elif preset == "Balanced":
                s2["ema_fast"], s2["ema_slow"] = 12, 26
            else:
                s2["ema_fast"], s2["ema_slow"] = 9, 21

        s2["ema_fast"] = int(st.number_input("ema_fast", min_value=2, max_value=200, value=int(s2.get("ema_fast", st_cfg.get("ema_fast", 12))), step=1))
        s2["ema_slow"] = int(st.number_input("ema_slow", min_value=3, max_value=400, value=int(s2.get("ema_slow", st_cfg.get("ema_slow", 26))), step=1))

    elif strat == "mean_reversion_rsi":
        if preset != "Custom":
            if preset == "Conservative":
                s2.update({"rsi_len": 14, "rsi_buy": 28.0, "rsi_sell": 72.0, "sma_len": 100})
            elif preset == "Balanced":
                s2.update({"rsi_len": 14, "rsi_buy": 30.0, "rsi_sell": 70.0, "sma_len": 50})
            else:
                s2.update({"rsi_len": 10, "rsi_buy": 35.0, "rsi_sell": 65.0, "sma_len": 30})

        s2["rsi_len"] = int(st.number_input("rsi_len", min_value=2, max_value=100, value=int(s2.get("rsi_len", st_cfg.get("rsi_len", 14))), step=1))
        s2["rsi_buy"] = float(st.number_input("rsi_buy", min_value=1.0, max_value=49.0, value=float(s2.get("rsi_buy", st_cfg.get("rsi_buy", 30.0))), step=0.5))
        s2["rsi_sell"] = float(st.number_input("rsi_sell", min_value=51.0, max_value=99.0, value=float(s2.get("rsi_sell", st_cfg.get("rsi_sell", 70.0))), step=0.5))
        s2["sma_len"] = int(st.number_input("sma_len", min_value=5, max_value=400, value=int(s2.get("sma_len", st_cfg.get("sma_len", 50))), step=1))

    else:  # breakout_donchian
        if preset != "Custom":
            if preset == "Conservative":
                s2["donchian_len"] = 30
            elif preset == "Balanced":
                s2["donchian_len"] = 20
            else:
                s2["donchian_len"] = 15

        s2["donchian_len"] = int(st.number_input("donchian_len", min_value=5, max_value=200, value=int(s2.get("donchian_len", st_cfg.get("donchian_len", 20))), step=1))

    proposed["strategy"] = s2

    st.subheader("Proposed YAML")
    y = yaml.safe_dump(proposed, sort_keys=False, default_flow_style=False, allow_unicode=True)
    st.code(y, language="yaml")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("WRITE Strategy to config"):
            res = save_user_yaml(proposed)
            st.json({"write": res})
            gov = record_config_change(actor="dashboard", action="update_strategy", before_cfg=before, after_cfg=proposed, meta={"panel": "Strategy Selector", "strategy": strat, "preset": preset})
            st.json({"governance": gov})
    with c2:
        st.download_button("Download proposed config.yaml", data=y.encode("utf-8"), file_name="user_config.yaml", mime="text/yaml")

except Exception as e:
    st.error(f"Strategy panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Execution Loop (Intents → Orders)")

st.caption("Paper-first executor. Create intents → executor places orders via adapter → events journaled → reconciler updates status. Live mode is hard-gated by execution.live_enabled=false by default.")

try:
    import uuid
    from services.admin.config_editor import load_user_yaml
    from services.execution.intent_executor_supervisor import start as ex_start, stop as ex_stop, status as ex_status
    from services.execution.intent_store import create_intent, list_intents, active_counts
    from services.journal.order_event_store import last_events

    cfg = load_user_yaml()
    ex = cfg.get("execution", {}) if isinstance(cfg.get("execution"), dict) else {}

    st.json({"execution": ex, "executor_process": ex_status(), "intent_counts": active_counts()})

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("START Executor (background)"):
            st.json(ex_start())
    with c2:
        if st.button("STOP Executor (background)"):
            st.json(ex_stop(force=True))
    with c3:
        if st.button("Create TEST paper intent (market buy)"):
            intent_id = f"test_{uuid.uuid4().hex[:12]}"
            venue = str(ex.get("venue", "binance"))
            create_intent(
                intent_id=intent_id,
                mode="paper",
                venue=venue,
                symbol="BTC/USDT",
                side="buy",
                order_type="market",
                amount=0.001,
                meta={"source": "dashboard_test"},
            )
            st.success(f"Created intent: {intent_id}")

    st.subheader("Recent intents")
    st.json(list_intents(40))

    st.subheader("Recent order events")
    st.json(last_events(80))

except Exception as e:
    st.error(f"Execution panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Strategy Presets (No Config Editing)")

st.caption("Pick a preset and run the strategy once using those params/filters without modifying your config file.")

try:
    from copy import deepcopy
    from services.admin.config_editor import load_user_yaml
    from services.strategy.presets import PRESETS
    from services.strategy.intent_builder import build_one as build_one_cfg

    cfg0 = load_user_yaml()

    preset_name = st.selectbox("Preset", list(PRESETS.keys()), index=0)
    preset = PRESETS.get(preset_name, {})
    st.json({"preset": preset})

    if st.button("RUN once with preset (no save)"):
        cfg = deepcopy(cfg0)
        cfg.setdefault("strategy", {})
        cfg["strategy"]["type"] = preset.get("type", cfg["strategy"].get("type", "ema_crossover"))
        cfg["strategy"]["params"] = preset.get("params", {})
        cfg["strategy"]["filters"] = preset.get("filters", {})
        st.json(build_one_cfg(cfg=cfg))

except Exception as e:
    st.error(f"Preset panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("One-Click Service Controls")

st.caption("Starts/stops background Strategy Builder + Intent Executor processes (PID-supervised). Useful for packaged desktop runs.")

try:
    from services.execution.intent_executor_supervisor import start as ex_start, stop as ex_stop, status as ex_status
    from services.strategy.strategy_builder_supervisor import start as sb_start, stop as sb_stop, status as sb_status

    st.json({"strategy_builder": sb_status(), "intent_executor": ex_status()})

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("START ALL"):
            st.json({"strategy_builder": sb_start(), "intent_executor": ex_start()})
    with c2:
        if st.button("STOP ALL"):
            st.json({"intent_executor": ex_stop(force=True), "strategy_builder": sb_stop(force=True)})
    with c3:
        if st.button("REFRESH STATUS"):
            st.json({"strategy_builder": sb_status(), "intent_executor": ex_status()})

except Exception as e:
    st.error(f"Service controls failed: {type(e).__name__}: {e}")

st.divider()
st.header("Reconciliation Wizard (Step-by-step)")

st.caption("Guided recovery flow. Steps are locked so you can’t resume live until reconciliation is clean and local issues are resolved.")

try:
    from services.admin.config_editor import load_user_yaml
    from services.admin.resume_gate import resume_if_safe
    from services.admin.reconcile_gate import ensure_clean_reconcile_for_live
    from services.execution.reconciliation import reconcile_once
    from services.execution.reconciliation_actions import export_report, cancel_unknown_exchange_open_orders, get_reconcile_needed, resolve_reconcile_needed_intents
    from services.admin.wizard_state import load as wiz_load, save as wiz_save, reset as wiz_reset, advance as wiz_advance

    cfg = load_user_yaml()
    st_w = wiz_load()
    step = int(st_w.get("step", 1))

    # Always show top-level status
    gate = ensure_clean_reconcile_for_live(cfg=cfg)
    rn = get_reconcile_needed(limit=200)

    st.json({
        "wizard_step": step,
        "live_resume_gate": gate,
        "reconcile_needed_count": len(rn.get("rows") or []) if rn.get("ok") else None,
        "wizard_state_path": "data/wizard_reconcile.json",
    })

    # Reset wizard (typed)
    st.subheader("Reset Wizard (optional)")
    typed_reset = st.text_input("Type RESET_WIZARD to reset:", value="", max_chars=32)
    if st.button("RESET Wizard") and typed_reset.strip().upper() == "RESET_WIZARD":
        st_w = wiz_reset()
        step = int(st_w.get("step", 1))
        st.success("Wizard reset.")
    elif st.button("RESET Wizard") and typed_reset.strip().upper() != "RESET_WIZARD":
        st.info("Blocked: type RESET_WIZARD first.")

    st.divider()

    # STEP 1: Run reconcile
    st.subheader("Step 1 — Run Reconciliation")
    if step != 1:
        st.info("Locked (complete previous steps or reset wizard).")
    else:
        if st.button("RUN reconcile_once"):
            rep = reconcile_once(cfg=cfg)
            st_w["last_reconcile"] = rep
            wiz_save(st_w)
            st.json(rep)
            # Step advance logic: always require export next
            wiz_advance(st_w, 2)
            st.success("Step 1 complete → Step 2 unlocked.")

    # STEP 2: Export report
    st.subheader("Step 2 — Export Report")
    if step < 2:
        st.info("Locked until Step 1 complete.")
    elif step > 2:
        st.info("Already completed.")
    else:
        if st.button("EXPORT report"):
            rep = export_report(cfg=cfg)
            st_w["last_export_path"] = rep.get("path")
            st_w["last_export_report"] = rep.get("report")
            wiz_save(st_w)
            st.json({"path": rep.get("path"), "ok": rep.get("ok")})
            wiz_advance(st_w, 3)
            st.success("Step 2 complete → Step 3 unlocked.")

    # STEP 3: Optional cancel unknown open orders (typed)
    st.subheader("Step 3 — Optional: Cancel UNKNOWN Exchange Open Orders")
    st.warning("Only cancel if you confirm they are orphaned. This affects your real exchange account.")
    if step < 3:
        st.info("Locked until Step 2 complete.")
    elif step > 3:
        st.info("Already completed.")
    else:
        typed = st.text_input("Type CANCEL_UNKNOWN to unlock (optional):", value="", max_chars=24)
        max_n = st.number_input("Max cancels this step", min_value=0, max_value=200, value=0, step=1)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("SKIP (no cancels)"):
                st_w["last_cancel_unknown"] = {"skipped": True}
                wiz_save(st_w)
                wiz_advance(st_w, 4)
                st.success("Skipped cancels → Step 4 unlocked.")
        with c2:
            if st.button("CANCEL unknown orders") and typed.strip().upper() == "CANCEL_UNKNOWN":
                rep = cancel_unknown_exchange_open_orders(cfg=cfg, max_n=int(max_n))
                st_w["last_cancel_unknown"] = rep
                wiz_save(st_w)
                st.json(rep)
                wiz_advance(st_w, 4)
                st.success("Cancel attempt recorded → Step 4 unlocked.")
            elif st.button("CANCEL unknown orders") and typed.strip().upper() != "CANCEL_UNKNOWN":
                st.info("Blocked: type CANCEL_UNKNOWN first (or press SKIP).")

    # STEP 4: Re-run reconcile and require clean (or proceed to resolve locals)
    st.subheader("Step 4 — Re-run Reconciliation (must converge)")
    if step < 4:
        st.info("Locked until Step 3 complete.")
    elif step > 4:
        st.info("Already completed.")
    else:
        if st.button("RUN reconcile_once (after cancels/skip)"):
            rep = reconcile_once(cfg=cfg)
            st_w["last_reconcile_after_cancel"] = rep
            wiz_save(st_w)
            st.json(rep)
            # You can proceed either to resolving local intents or directly to resume if clean and no locals.
            wiz_advance(st_w, 5)
            st.success("Step 4 complete → Step 5 unlocked.")

    # STEP 5: Resolve RECONCILE_NEEDED local intents
    st.subheader("Step 5 — Resolve Local RECONCILE_NEEDED Intents")
    if step < 5:
        st.info("Locked until Step 4 complete.")
    elif step > 5:
        st.info("Already completed.")
    else:
        rep = get_reconcile_needed(limit=200)
        rows = rep.get("rows") or []
        st.json({"reconcile_needed_ok": rep.get("ok"), "count": len(rows)})
        if rows:
            st.dataframe(rows)

        st.caption("If count > 0, you must resolve them (CANCELLED/RESOLVED/etc.) before Step 6.")
        ids_text = st.text_area("Intent IDs to resolve (one per line)", value="")
        status = st.selectbox("New status", ["CANCELLED", "RESOLVED", "ERROR", "IGNORED"], index=0)
        note = st.text_input("Note", value="wizard_resolved")

        typed2 = st.text_input("Type RESOLVE_INTENTS to unlock:", value="", max_chars=24)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("APPLY Resolve") and typed2.strip().upper() == "RESOLVE_INTENTS":
                ids = [x.strip() for x in ids_text.splitlines() if x.strip()]
                rr = resolve_reconcile_needed_intents(intent_ids=ids, status=status, note=note)
                st_w["last_resolve"] = rr
                wiz_save(st_w)
                st.json(rr)
            elif st.button("APPLY Resolve") and typed2.strip().upper() != "RESOLVE_INTENTS":
                st.info("Blocked: type RESOLVE_INTENTS first.")
        with c2:
            if st.button("CONTINUE to Step 6 (only if count==0)"):
                rep2 = get_reconcile_needed(limit=50)
                cnt = len(rep2.get("rows") or []) if rep2.get("ok") else 999999
                if cnt == 0:
                    wiz_advance(st_w, 6)
                    st.success("Step 5 complete → Step 6 unlocked.")
                else:
                    st.error(f"Blocked: {cnt} intents still RECONCILE_NEEDED.")

    # STEP 6: Resume (live-gated) — requires reconcile clean
    st.subheader("Step 6 — Resume Trading (Live-gated)")
    if step < 6:
        st.info("Locked until Step 5 complete.")
    else:
        st.caption("This will run the existing live resume gate: preflight + private auth + reconciliation clean (already integrated).")
        typed3 = st.text_input("Type RESUME to unlock:", value="", max_chars=16)
        if st.button("RESUME NOW") and typed3.strip().upper() == "RESUME":
            rep = resume_if_safe(cfg=cfg)
            st_w["last_resume"] = rep
            wiz_save(st_w)
            st.json(rep)
            if rep.get("resumed"):
                st.success("Resume succeeded. Wizard complete.")
            else:
                st.warning("Resume blocked by safety gate. Fix issues and rerun Step 4/5 as needed.")
        elif st.button("RESUME NOW") and typed3.strip().upper() != "RESUME":
            st.info("Blocked: type RESUME first.")

except Exception as e:
    st.error(f"Reconciliation Wizard failed: {type(e).__name__}: {e}")

st.divider()
st.header("Release Checklist (Manifest)")

st.caption("Creates a release manifest with hashes and step results. UI button runs DRY-RUN only (no changes).")

try:
    import subprocess, sys
    if st.button("RUN Release Checklist (dry-run)"):
        p = subprocess.run([sys.executable, "scripts/release_checklist.py", "--dry-run"], capture_output=True, text=True)
        st.code((p.stdout or "") + ("\n" + p.stderr if p.stderr else ""), language="text")
except Exception as e:
    st.error(f"Release checklist panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Release Notes Preview")

st.caption("Preview and generate releases/RELEASE_NOTES.md locally (safe: no tagging, no publishing).")

notes_path = "releases/RELEASE_NOTES.md"
changelog_path = "CHANGELOG.md"

colA, colB = st.columns([1, 1])

with colA:
    tag = st.text_input("Tag (optional)", value="v0.1.0", help="Used to select the matching CHANGELOG section. Example: v0.1.0")

with colB:
    top_n = st.number_input("Top artifacts in summary", min_value=3, max_value=50, value=12, step=1)

try:
    import subprocess, sys
    if st.button("Generate Release Notes now"):
        # Use downloaded manifests if present, otherwise repo local
        manifest_glob = "releases/release_manifest_*.json"
        cmd = [
            sys.executable, "scripts/generate_release_notes.py",
            "--tag", (tag or "").strip(),
            "--manifest-glob", manifest_glob,
            "--out", notes_path,
            "--top-artifacts", str(int(top_n)),
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        st.code((p.stdout or "") + ("\n" + p.stderr if p.stderr else ""), language="text")
except Exception as e:
    st.error(f"Release notes generator failed: {type(e).__name__}: {e}")

st.subheader("Current RELEASE_NOTES.md")
try:
    p = Path(notes_path)
    if p.exists():
        st.markdown(p.read_text(encoding="utf-8", errors="replace"))
    else:
        st.info("No releases/RELEASE_NOTES.md yet. Click 'Generate Release Notes now'.")
except Exception as e:
    st.error(f"Could not read {notes_path}: {type(e).__name__}: {e}")

st.subheader("Current CHANGELOG.md")
try:
    p = Path(changelog_path)
    if p.exists():
        st.markdown(p.read_text(encoding="utf-8", errors="replace"))
    else:
        st.warning("CHANGELOG.md not found.")
except Exception as e:
    st.error(f"Could not read {changelog_path}: {type(e).__name__}: {e}")

st.divider()
st.header("Local Tag Helper (Safe)")

st.caption("Creates a local git tag only after strict checks. Never pushes automatically.")

try:
    import subprocess, sys
    tag = st.text_input("Tag (vX.Y.Z)", value="v0.1.0")
    col1, col2 = st.columns(2)
    with col1:
        run_tests = st.checkbox("Run tests first (if tests/ exists)", value=False)
    with col2:
        dry = st.checkbox("Dry-run (validate only)", value=True)

    if st.button("Run Tag Helper"):
        cmd = [sys.executable, "scripts/tag_release.py", "--tag", tag]
        if run_tests:
            cmd.append("--run-tests")
        if dry:
            cmd.append("--dry-run")
        p = subprocess.run(cmd, capture_output=True, text=True)
        st.code((p.stdout or "") + ("\n" + p.stderr if p.stderr else ""), language="text")
except Exception as e:
    st.error(f"Tag helper panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Pre-release Sanity Suite")

st.caption("Runs ruff + mypy + config validation + import smoke (+ pytest if tests exist). Safe: no trading, no publishing.")

try:
    import subprocess, sys
    fix = st.checkbox("Auto-fix with ruff --fix (still fail-closed)", value=False)
    if st.button("RUN Sanity Suite now"):
        cmd = [sys.executable, "scripts/pre_release_sanity.py"]
        if fix:
            cmd.append("--fix")
        p = subprocess.run(cmd, capture_output=True, text=True)
        st.code((p.stdout or "") + ("\n" + p.stderr if p.stderr else ""), language="text")
except Exception as e:
    st.error(f"Sanity suite panel failed: {type(e).__name__}: {e}")

st.divider()
st.header("Repair Wizard (Role-Gated)")

st.caption("Generate → Approve → Execute runbooks from reconciliation drift. Execution is fail-closed and requires env gates.")

try:
    import os
    import asyncio
    from pathlib import Path

    from dashboard.role_guard import RolePolicy, require_role
    from storage.reconciliation_store_sqlite import SQLiteReconciliationStore
    from storage.repair_runbook_store_sqlite import SQLiteRepairRunbookStore
    from services.runbooks.drift_repair_planner import RepairPolicy, build_repair_plan_from_latest_recon
    from services.runbooks.ccxt_repair_executor import ExecutePolicy, execute_plan
    import yaml

    # Simple local role switch (until real auth is added)
    if "role" not in st.session_state:
        st.session_state["role"] = "VIEWER"

    colA, colB, colC = st.columns(3)
    with colA:
        st.session_state["role"] = st.selectbox("Current role", ["VIEWER", "OPERATOR", "ADMIN"], index=["VIEWER","OPERATOR","ADMIN"].index(st.session_state["role"]))
    with colB:
        recon_db = st.text_input("Reconciliation DB", value="data/reconciliation.sqlite")
    with colC:
        runbook_db = st.text_input("Runbooks DB", value="data/repair_runbooks.sqlite")

    role = st.session_state["role"]
    policy = RolePolicy()

    cfg_path = st.text_input("Trading config", value="config/trading.yaml")

    # Load config for exchange + symbols + runbook policy defaults
    cfg = {}
    try:
        cfg = yaml.safe_load(Path(cfg_path).read_text(encoding="utf-8", errors="replace")) or {}
    except Exception:
        cfg = {}

    live = cfg.get("live") or {}
    exchange = st.text_input("Exchange", value=str(live.get("exchange_id") or "coinbase").strip().lower())

    symbols = [str(s) for s in (cfg.get("symbols") or [])]
    if not symbols:
        st.warning("Config symbols is empty. Execution actions need symbols list.")

    # Show latest reconciliation snapshot
    recon_store = SQLiteReconciliationStore(path=Path(recon_db))
    latest = recon_store.read_last_n_sync(n=1, exchange=exchange) or []
    if latest:
        st.subheader("Latest Reconciliation")
        st.json(latest[0]["summary"])
    else:
        st.info("No reconciliation found for this exchange yet.")

    rb_store = SQLiteRepairRunbookStore(path=Path(runbook_db))

    st.subheader("1) Generate Plan (no execution)")
    try:
        require_role(role, policy.generate_required)
        if st.button("Generate repair plan from latest reconciliation"):
            rr = cfg.get("repair_runbooks") or {}
            allowed = list(rr.get("allowed_actions") or ["CANCEL_OPEN_ORDERS"])
            defaults = list(rr.get("default_actions") or ["CANCEL_OPEN_ORDERS"])
            max_flatten = int(rr.get("max_flatten_symbols") or 5)

            plan = build_repair_plan_from_latest_recon(
                recon_store=recon_store,
                exchange=exchange,
                policy=RepairPolicy(allowed_actions=allowed, default_actions=defaults, max_flatten_symbols=max_flatten),
            )
            rb_store.create_plan_sync(
                plan_id=plan["plan_id"],
                exchange=plan["exchange"],
                plan_hash=plan["plan_hash"],
                summary=plan["summary"],
                actions=plan["actions"],
                meta=plan["meta"],
            )
            st.success(f"Plan created: {plan['plan_id']}")
            st.json(plan)
    except PermissionError as e:
        st.info(str(e))

    st.subheader("2) Approve Plan (audited)")
    plan_id_to_approve = st.text_input("Plan ID to approve", value="")
    approver = st.text_input("Approver name", value="")
    note = st.text_input("Approval note", value="approved after review")
    try:
        require_role(role, policy.approve_required)
        if st.button("Approve plan"):
            if not plan_id_to_approve.strip():
                st.error("Plan ID required")
            elif not approver.strip():
                st.error("Approver required")
            else:
                p = rb_store.get_plan_sync(plan_id_to_approve.strip())
                if not p:
                    st.error("Plan not found")
                elif p["status"] != "DRAFT":
                    st.error(f"Plan status must be DRAFT; got {p['status']}")
                else:
                    rb_store.approve_plan_sync(plan_id_to_approve.strip(), approver.strip(), note.strip())
                    st.success("Approved")
    except PermissionError as e:
        st.info(str(e))

    st.subheader("3) Execute Approved Plan (dangerous, fail-closed)")
    plan_id_to_exec = st.text_input("Plan ID to execute", value="")
    typed = st.text_input("Type to confirm", value="", placeholder="Type: EXECUTE <PLAN_ID>")
    st.caption("Execution requires: mode=live, live.enabled=true, ENABLE_LIVE_TRADING=YES, ENABLE_REPAIR_EXECUTION=YES (and ENABLE_FLATTEN=YES if flatten).")

    try:
        require_role(role, policy.execute_required)
        if st.button("EXECUTE (only if gates satisfied)"):
            pid = plan_id_to_exec.strip()
            if not pid:
                st.error("Plan ID required")
            elif typed.strip() != f"EXECUTE {pid}":
                st.error("Typed confirmation mismatch")
            else:
                plan = rb_store.get_plan_sync(pid)
                if not plan:
                    st.error("Plan not found")
                elif plan["status"] != "APPROVED":
                    st.error(f"Plan status must be APPROVED; got {plan['status']}")
                else:
                    mode = str(cfg.get("mode") or "paper").strip().lower()
                    if mode != "live":
                        st.error("Config mode must be live (fail-closed).")
                    elif not bool((cfg.get("live") or {}).get("enabled", False)):
                        st.error("Config live.enabled must be true (fail-closed).")
                    else:
                        rr = cfg.get("repair_runbooks") or {}
                        pol = ExecutePolicy(
                            require_env_confirm=bool(rr.get("require_env_confirm", True)),
                            env_var=str(rr.get("env_confirm_var") or "ENABLE_REPAIR_EXECUTION"),
                            require_flatten_env_confirm=bool(rr.get("require_flatten_env_confirm", True)),
                            flatten_env_var=str(rr.get("flatten_env_confirm_var") or "ENABLE_FLATTEN"),
                            sandbox=bool((cfg.get("live") or {}).get("sandbox", True)),
                        )

                        # Mark start
                        rb_store.set_status_sync(pid, "EXECUTE_START", "Execution started from UI", {"exchange": exchange, "sandbox": pol.sandbox})

                        async def _do():
                            return await execute_plan(exchange_id=exchange, symbols=symbols, plan_actions=plan["actions"], policy=pol)

                        try:
                            res = asyncio.run(_do())
                            rb_store.set_status_sync(pid, "EXECUTED", "Execution complete (UI)", res)
                            st.success("EXECUTED")
                            st.json(res)
                        except Exception as e:
                            rb_store.set_status_sync(pid, "FAILED", "Execution failed (UI)", {"error": f"{type(e).__name__}:{e}"})
                            st.error(f"Execution failed: {type(e).__name__}: {e}")

    except PermissionError as e:
        st.info(str(e))

    st.subheader("Export Runbook Report")
    export_plan_id = st.text_input("Plan ID to export", value="")
    out_dir = st.text_input("Export directory", value="data/runbook_exports")
    if st.button("Export (MD+JSON, PDF optional)"):
        if not export_plan_id.strip():
            st.error("Plan ID required")
        else:
            # run exporter inline (no subprocess)
            from scripts.repair_export import to_markdown, try_write_pdf
            p = rb_store.get_plan_sync(export_plan_id.strip())
            if not p:
                st.error("Plan not found")
            else:
                events = rb_store.list_events_sync(export_plan_id.strip())
                md = to_markdown(p, events)
                od = Path(out_dir)
                od.mkdir(parents=True, exist_ok=True)
                base = export_plan_id.strip().replace(":", "_")
                md_path = od / f"{base}.md"
                js_path = od / f"{base}.json"
                pdf_path = od / f"{base}.pdf"
                md_path.write_text(md, encoding="utf-8")
                import json as _json
                js_path.write_text(_json.dumps({"plan": p, "events": events}, indent=2, sort_keys=True), encoding="utf-8")
                pdf_ok = try_write_pdf(md, pdf_path)
                st.success(f"Exported: {md_path} and {js_path}" + (f" and {pdf_path}" if pdf_ok else " (PDF skipped)"))

except Exception as e:
    st.error(f"Repair Wizard error: {type(e).__name__}: {e}")

st.subheader("Execution Latency (submit→ack, ack→fill)")
try:
    import pandas as pd
    from storage.market_ws_store_sqlite import SQLiteMarketWsStore
    import yaml
    from pathlib import Path

    cfg = yaml.safe_load(Path("config/trading.yaml").read_text(encoding="utf-8", errors="replace")) or {}
    es = cfg.get("execution_safety") or {}
    dbp = str(es.get("latency_db_path", "data/market_ws.sqlite"))
    store = SQLiteMarketWsStore(path=dbp)
    rows = [r for r in store.recent_latency(n=400) if str(r.get("category")) == "execution"]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
except Exception as e:
    st.error(f"Execution latency panel error: {type(e).__name__}: {e}")

st.divider()
st.header("Services Manager")

try:
    import json, time, subprocess, sys
    from pathlib import Path
    import pandas as pd

    data_dir = Path("data/supervisor")
    status_path = data_dir / "status.json"
    pid_path = data_dir / "daemon.pid"
    stop_path = data_dir / "STOP"

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Supervisor"):
            subprocess.Popen([sys.executable, "scripts/start_supervisor.py"])
            st.success("Starting supervisor...")
    with col2:
        if st.button("Stop Supervisor"):
            subprocess.Popen([sys.executable, "scripts/stop_supervisor.py"])
            st.warning("Stopping supervisor...")
    with col3:
        st.caption("Supervisor manages WS collector + (optional) bot runner")

    st.subheader("Current Status")
    if status_path.exists():
        try:
            s = json.loads(status_path.read_text(encoding="utf-8", errors="replace"))
            st.json({"ts_ms": s.get("ts_ms"), "daemon_pid": s.get("daemon_pid")})
            rows = []
            for name, info in (s.get("services") or {}).items():
                rows.append({
                    "service": name,
                    "running": info.get("running"),
                    "pid": info.get("pid"),
                    "uptime_ms": info.get("uptime_ms"),
                    "restarts": info.get("restarts"),
                    "last_exit_code": info.get("last_exit_code"),
                    "log_path": info.get("log_path"),
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
            else:
                st.info("No services listed yet.")
        except Exception as e:
            st.error(f"Status parse error: {type(e).__name__}: {e}")
    else:
        st.info("No status file yet. Click Start Supervisor.")

    st.caption("Logs: data/supervisor/logs/*.log")
except Exception as e:
    st.error(f"Services Manager error: {type(e).__name__}: {e}")

st.divider()
st.header("First-Run Wizard")

try:
    import yaml
    from pathlib import Path
    from services.diagnostics.preflight import run_preflight, PreflightConfig, diagnostics_text
    from services.diagnostics.config_restore import restore_missing_configs

    # Load packaging defaults if possible
    host = "127.0.0.1"
    port = 8501
    cfg_path = Path("config/trading.yaml")
    cfg = {}
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8", errors="replace")) or {}
        host = str((cfg.get("packaging") or {}).get("default_host") or host)
        port = int((cfg.get("packaging") or {}).get("default_port") or port)

    st.subheader("1) Preflight")
    if st.button("Run Preflight"):
        pf = run_preflight(PreflightConfig(host=host, port=port))
        st.session_state["__preflight"] = pf

    pf = st.session_state.get("__preflight")
    if pf:
        st.json(pf)
        st.download_button(
            "Download Diagnostics JSON",
            data=diagnostics_text(pf).encode("utf-8"),
            file_name="cryptobotpro_diagnostics.json",
            mime="application/json",
        )
        st.text_area("Copy Diagnostics (paste into support / next chat)", diagnostics_text(pf), height=240)

    st.subheader("2) Restore missing configs (safe)")
    st.caption("Creates config/trading.yaml from template if missing. Never overwrites existing files.")
    if st.button("Restore Missing Configs"):
        rr = restore_missing_configs(".")
        st.json({"ok": rr.ok, "restored": rr.restored, "skipped": rr.skipped, "errors": rr.errors})
        # rerun preflight after restore
        pf2 = run_preflight(PreflightConfig(host=host, port=port))
        st.session_state["__preflight"] = pf2

    st.subheader("3) Keys & Safety")
    st.caption("Keys are read from environment variables only (presence shown; values never displayed).")
    st.write("Required env vars:")
    st.code("EXCHANGE_API_KEY\nEXCHANGE_API_SECRET\nEXCHANGE_API_PASSPHRASE (exchange-dependent)\nENABLE_RUNBOOK_EXECUTION=NO (default)")
    st.caption("Tip: a template file is created at repo root as .env.template (never contains real keys).")

except Exception as e:
    st.error(f"First-Run Wizard error: {type(e).__name__}: {e}")


st.divider()
st.subheader("Collector Control")

from pathlib import Path

STATE_FILE = Path("runtime/collector_state.txt")

def _state():
    return STATE_FILE.read_text().strip() if STATE_FILE.exists() else "stopped"

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("▶ Start Collector"):
        import services.health.feed_health  # ensure module load
        from __main__ import start_collector
        start_collector()
        st.success("Collector started")

with col2:
    if st.button("⏹ Stop Collector"):
        from __main__ import stop_collector
        stop_collector()
        st.warning("Collector stopped")

with col3:
    st.metric("Status", _state().upper())

st.divider()
st.header("Bot Control (Single Source)")

try:
    import os
    import yaml
    from services.bot.start_manager import start as start_bot, stop as stop_bot, decide_start
    from services.bot.process_manager import read_status

    cfg = {}
    try:
        cfg = yaml.safe_load(open("config/trading.yaml", "r", encoding="utf-8").read()) or {}
    except Exception:
        cfg = {}

    st.subheader("Status")
    st.json(read_status().__dict__)

    colA, colB, colC = st.columns(3)

    with colA:
        if st.button("Start PAPER Bot"):
            dec, st2 = start_bot("paper")
            st.session_state["__bot_last"] = {"decision": dec.__dict__, "status": st2.__dict__}

    with colB:
        dec_live = decide_start("live", cfg)
        disabled = not bool(dec_live.ok)
        if st.button("Start LIVE Bot", disabled=disabled):
            dec, st2 = start_bot("live")
            st.session_state["__bot_last"] = {"decision": dec.__dict__, "status": st2.__dict__}

    with colC:
        if st.button("STOP Bot"):
            st2 = stop_bot()
            st.session_state["__bot_last"] = {"stopped": True, "status": st2.__dict__}

    if not dec_live.ok:
        st.error("LIVE start blocked:")
        st.code("\n".join(dec_live.reasons))
        st.caption(dec_live.note)
    else:
        if dec_live.status == "WARN":
            st.warning("LIVE start allowed but WARN present (watch feed/latency).")

    if st.session_state.get("__bot_last"):
        st.subheader("Last action")
        st.json(st.session_state["__bot_last"])

    st.subheader("Logs")
    st.caption("Logs write to data/logs/*.log")
    st.code("data/logs/live_bot.log\n"
            "data/logs/paper_bot.log\n"
            "data/bot_process.json")

except Exception as e:
    st.error(f"Bot Control error: {type(e).__name__}: {e}")

st.divider()
st.header("Live Start Gate (UI)")

try:
    import yaml
    from services.diagnostics.ui_live_gate import evaluate_live_ui_gate

    cfg = {}
    try:
        cfg = yaml.safe_load(open("config/trading.yaml", "r", encoding="utf-8").read()) or {}
    except Exception:
        cfg = {}

    g = evaluate_live_ui_gate(cfg)

    st.write(f"Gate status: **{g.status}**")
    if g.ok and g.status == "OK":
        st.success("Live start allowed (collector running, no BLOCK feeds, WS gate OK).")
    elif g.ok and g.status == "WARN":
        st.warning("Live start allowed but WARN present (watch staleness/spread).")
    else:
        st.error("Live start BLOCKED. Fix the reasons below, then retest.")

    if g.reasons:
        st.code("\n".join(g.reasons))

    with st.expander("Gate details"):
        st.json(g.details)

except Exception as e:
    st.error(f"Live gate panel error: {type(e).__name__}: {e}")


st.divider()
try:
    from services.meta.version import get_version
    st.caption(f"CryptoBotPro — version {get_version()}")
except Exception:
    pass

st.subheader("Local build actions (this machine only)")

try:
    import platform
    from services.release.local_build import build_windows_pyinstaller, build_windows_installer_inno, build_macos_app_and_dmg

    sysname = platform.system().lower()
    st.caption(f"Detected OS: {platform.system()} — build buttons are OS-gated.")

    if sysname == "windows":
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Build Windows app (PyInstaller)"):
                st.session_state["__build_last"] = build_windows_pyinstaller().__dict__
        with c2:
            if st.button("Build Windows installer (Inno)"):
                st.session_state["__build_last"] = build_windows_installer_inno().__dict__

    if sysname == "darwin":
        if st.button("Build macOS .app + DMG"):
            st.session_state["__build_last"] = build_macos_app_and_dmg().__dict__

    if st.session_state.get("__build_last"):
        r = st.session_state["__build_last"]
        st.json(r)
        if r.get("out"):
            st.text_area("build stdout", r["out"], height=180)
        if r.get("err"):
            st.text_area("build stderr", r["err"], height=180)

except Exception as e:
    st.error(f"Local build panel error: {type(e).__name__}: {e}")

st.divider()
st.header("UI Live Gate (Phase 5)")
# Placeholder for live gate panel

st.divider()
st.header("Multi-Exchange Monitor")

try:
    import yaml
    import pandas as pd
    from storage.market_store_sqlite import MarketStore
    from services.data.unified_view import latest_mid_by_exchange, cross_exchange_spread_bps

    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    symbol = str((cfg.get("symbols") or ["BTC/USDT"])[0])
    raw_db = str(((cfg.get("collector") or {}).get("db_path")) or "data/market_raw.sqlite")

    multi = cfg.get("multi_exchanges") or {}
    venues = multi.get("venues") or [
        {"exchange_id": "coinbase"},
        {"exchange_id": "binance"},
        {"exchange_id": "gateio"},
    ]
    exchanges = [str(v.get("exchange_id")).lower() for v in venues if v.get("exchange_id")]

    st.caption("Collector: python scripts/collect_market_data_multi.py --once  (or run loop).")
    st.write({"symbol": symbol, "exchanges": exchanges, "db": raw_db})

    store = MarketStore(path=raw_db)
    mids = latest_mid_by_exchange(store=store, exchanges=exchanges, symbol=symbol)
    spread = cross_exchange_spread_bps(mids=mids)

    df = pd.DataFrame([
        {"exchange": ex, **mids[ex]}
        for ex in exchanges
    ])
    st.subheader("Latest ticker snapshot (per exchange)")
    st.dataframe(df, use_container_width=True)

    st.subheader("Cross-exchange spread")
    if spread is None:
        st.info("Not enough mids yet to compute spread.")
    else:
        st.metric("max-min spread (bps)", value=f"{spread:.2f}")

except Exception as e:
    st.error(f"Multi-Exchange Monitor error: {type(e).__name__}: {e}")

st.divider()
st.header("Live Execution (HARD-OFF by default)")

try:
    import os, yaml, pandas as pd
    from storage.execution_store_sqlite import ExecutionStore
    from services.execution.live_executor import cfg_from_yaml, submit_pending_live, reconcile_live

    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    live = cfg.get("live") or {}
    ex = str(live.get("exchange_id") or "coinbase").lower()

    ex_cfg = cfg.get("execution") or {}
    db = str(ex_cfg.get("db_path") or "data/execution.sqlite")
    store = ExecutionStore(path=db)

    st.subheader("Safety gate status")
    st.json({
        "live.enabled": bool(live.get("enabled", False)),
        "LIVE_TRADING env": os.environ.get("LIVE_TRADING"),
        "exchange_id": ex,
        "sandbox": bool(live.get("sandbox", False)),
        "note": "Live orders will not be sent unless live.enabled=true AND LIVE_TRADING=YES."
    })

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send pending live intents (if enabled)"):
            st.session_state["__live_submit"] = submit_pending_live(cfg_from_yaml())
    with col2:
        if st.button("Reconcile live (if enabled)"):
            st.session_state["__live_recon"] = reconcile_live(cfg_from_yaml())

    if st.session_state.get("__live_submit"):
        st.json(st.session_state["__live_submit"])
    if st.session_state.get("__live_recon"):
        st.json(st.session_state["__live_recon"])

    st.subheader("Recent LIVE intents")
    intents = store.list_intents(mode="live", exchange=ex, limit=200)
    st.dataframe(pd.DataFrame(intents) if intents else pd.DataFrame([]), use_container_width=True)

    st.subheader("Recent LIVE fills")
    fills = store.list_fills(mode="live", exchange=ex, limit=200)
    st.dataframe(pd.DataFrame(fills) if fills else pd.DataFrame([]), use_container_width=True)

except Exception as e:
    st.error(f"Live panel error: {type(e).__name__}: {e}")

st.divider()
st.header("Scheduling & Approval Gate")

try:
    import json
    from pathlib import Path
    import yaml

    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    learn = cfg.get("learning") or {}

    st.subheader("Install commands")

    st.code(
        "# macOS (from repo root)\n"
        "bash scripts/schedule/install_mac_monitor.sh 300\n"
        "bash scripts/schedule/install_mac_recommend_apply.sh 1800\n"
        "# uninstall\n"
        "bash scripts/schedule/uninstall_mac_monitor.sh\n"
        "bash scripts/schedule/uninstall_mac_recommend_apply.sh\n\n"
        "# Windows PowerShell (Run as current user)\n"
        "powershell -ExecutionPolicy Bypass -File scripts\\schedule\\install_windows_monitor.ps1 -IntervalMinutes 5\n"
        "powershell -ExecutionPolicy Bypass -File scripts\\schedule\\install_windows_recommend_apply.ps1 -IntervalMinutes 30\n"
        "# uninstall\n"
        "powershell -ExecutionPolicy Bypass -File scripts\\schedule\\uninstall_windows_monitor.ps1\n"
        "powershell -ExecutionPolicy Bypass -File scripts\\schedule\\uninstall_windows_recommend_apply.ps1\n",
        language="bash"
    )

    st.subheader("Approval status (required to switch)")
    reco_p = Path(str(learn.get("recommended_model_path") or "data/learning/recommended_model.json"))
    appr_p = Path(str(learn.get("approval_path") or "data/learning/model_switch_approval.json"))

    reco = json.loads(reco_p.read_text(encoding="utf-8")) if reco_p.exists() else None
    appr = json.loads(appr_p.read_text(encoding="utf-8")) if appr_p.exists() else None

    st.json({
        "model_switch_requires_approval": bool(learn.get("model_switch_requires_approval", True)),
        "active_model_id": learn.get("active_model_id"),
        "recommendation_file_exists": reco_p.exists(),
        "approval_file_exists": appr_p.exists(),
        "recommendation_note": (reco or {}).get("note") if reco else None,
        "recommended_model_id": ((reco or {}).get("best") or {}).get("model_id") if reco else None,
        "approved_model_id": (appr or {}).get("approved_model_id") if appr else None,
    })

    st.subheader("Manual approve (explicit)")
    st.code("python3 scripts/approve_model_switch.py --model_id m_XXXXXXXXXXXXXXXXXXXX --approved_by operator", language="bash")
    st.caption("Approval is consumed after apply; it can't be reused accidentally.")

except Exception as e:
    st.error(f"Scheduling panel error: {type(e).__name__}: {e}")

st.divider()
st.title("Setup Wizard (First Run)")

st.caption("Goal: no manual file edits. This wizard can generate and update config/trading.yaml, run preflight checks, and start/stop the bot loops.")

try:
    import yaml
    import pandas as pd
    from services.setup.config_manager import ConfigManager, apply_risk_preset
    from services.preflight.preflight import run_preflight
    from services.runtime.process_supervisor import status as proc_status
    import subprocess
    import sys

    cm = ConfigManager("config/trading.yaml")
    cfg = cm.load()

    st.subheader("1) Core settings")
    col1, col2, col3 = st.columns(3)
    with col1:
        cfg["pipeline"]["exchange_id"] = st.selectbox("Exchange", ["coinbase","binance","gateio"], index=["coinbase","binance","gateio"].index(str(cfg["pipeline"].get("exchange_id","coinbase")).lower()))
        cfg["execution"]["executor_mode"] = st.selectbox("Mode", ["paper","live"], index=["paper","live"].index(str(cfg["execution"].get("executor_mode","paper")).lower()))
    with col2:
        sym = (cfg.get("symbols") or ["BTC/USDT"])[0]
        sym = st.text_input("Symbol (first symbol used)", value=str(sym))
        cfg["symbols"] = [sym.upper().strip()]
        cfg["pipeline"]["timeframe"] = st.text_input("Timeframe", value=str(cfg["pipeline"].get("timeframe","5m")))
    with col3:
        cfg["pipeline"]["strategy"] = st.selectbox("Strategy", ["ema","mean_reversion"], index=["ema","mean_reversion"].index(str(cfg["pipeline"].get("strategy","ema")).lower()))
        cfg["pipeline"]["poll_sec"] = st.number_input("Pipeline poll seconds", min_value=1.0, max_value=120.0, value=float(cfg["pipeline"].get("poll_sec",10.0)), step=1.0)

    st.subheader("2) Strategy parameters")
    if str(cfg["pipeline"]["strategy"]).lower() == "ema":
        c1, c2 = st.columns(2)
        with c1:
            cfg["pipeline"]["ema_fast"] = int(st.number_input("EMA fast", min_value=2, max_value=200, value=int(cfg["pipeline"].get("ema_fast",12))))
        with c2:
            cfg["pipeline"]["ema_slow"] = int(st.number_input("EMA slow", min_value=3, max_value=400, value=int(cfg["pipeline"].get("ema_slow",26))))
    else:
        c1, c2 = st.columns(2)
        with c1:
            cfg["pipeline"]["bb_window"] = int(st.number_input("BB window", min_value=5, max_value=200, value=int(cfg["pipeline"].get("bb_window",20))))
        with c2:
            cfg["pipeline"]["bb_k"] = float(st.number_input("BB k", min_value=0.5, max_value=5.0, value=float(cfg["pipeline"].get("bb_k",2.0)), step=0.1))

    st.subheader("3) Sizing (choose ONE)")
    c1, c2 = st.columns(2)
    with c1:
        cfg["pipeline"]["fixed_qty"] = float(st.number_input("Fixed qty (base units)", min_value=0.0, value=float(cfg["pipeline"].get("fixed_qty",0.0)), step=0.0001, format="%.6f"))
    with c2:
        cfg["pipeline"]["quote_notional"] = float(st.number_input("Quote notional ($)", min_value=0.0, value=float(cfg["pipeline"].get("quote_notional",0.0)), step=1.0))

    if cfg["pipeline"]["fixed_qty"] > 0 and cfg["pipeline"]["quote_notional"] > 0:
        st.warning("Both fixed_qty and quote_notional are set. Set ONE to 0 to avoid unintended sizing.")

    st.subheader("4) Live safety toggle")
    if str(cfg["execution"]["executor_mode"]).lower() == "live":
        cfg["execution"]["live_enabled"] = st.checkbox("Enable LIVE trading (required)", value=bool(cfg["execution"].get("live_enabled", False)))
        st.caption("If unchecked, live intents will be blocked at RiskGate/IntentWriter.")
    else:
        cfg["execution"]["live_enabled"] = False

    st.subheader("5) Risk presets (optional)")
    preset = st.selectbox("Preset", ["(none)","safe_paper","paper_relaxed","live_locked"])
    if st.button("Apply preset"):
        if preset != "(none)":
            cfg = apply_risk_preset(cfg, preset)
            st.success(f"Applied preset: {preset}")

    st.subheader("6) Save / Generate config")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save config/trading.yaml"):
            cm.save(cfg)
            st.success("Saved config/trading.yaml")
    with c2:
        if st.button("Generate config if missing"):
            cm.ensure()
            st.success("Ensured config/trading.yaml exists (generated if missing).")

    with st.expander("Show current config"):
        st.code(yaml.safe_dump(cfg, sort_keys=False), language="yaml")

    st.subheader("7) Preflight checks")
    if st.button("Run preflight now"):
        res = run_preflight("config/trading.yaml")
        st.write({"ok": res.ok})
        st.dataframe(pd.DataFrame(res.checks), use_container_width=True)
        if not res.ok:
            st.error("Preflight FAILED. Fix errors above before starting.")
        else:
            st.success("Preflight OK.")

    st.subheader("8) Start / Stop Bot (one button)")
    st.caption("Starts pipeline loop + executor loop. Optionally starts live reconciler loop (recommended for live).")

    st.write(proc_status(["pipeline","executor","reconciler"]))

    colA, colB, colC = st.columns(3)
    with colA:
        start_reconcile = st.checkbox("Start live reconciler too", value=False)
        if st.button("START BOT"):
            cmd = [sys.executable, "scripts/start_bot.py"] + (["--with_reconcile"] if start_reconcile else [])
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            st.code(out)
    with colB:
        if st.button("STOP BOT (all)"):
            out = subprocess.check_output([sys.executable, "scripts/stop_bot.py", "--all"], stderr=subprocess.STDOUT, text=True)
            st.code(out)
    with colC:
        if st.button("STATUS"):
            out = subprocess.check_output([sys.executable, "scripts/bot_status.py"], stderr=subprocess.STDOUT, text=True)
            st.code(out)

except Exception as e:
    st.error(f"Setup Wizard error: {type(e).__name__}: {e}")

st.markdown("### Computed gate inputs (Phase 83)")
try:
    from services.risk.journal_introspection_phase83 import JournalSignals
    js = JournalSignals(exec_db=exec_db)
    st.json({
        "realized_pnl_today_usd": js.realized_pnl_today_usd(),
        "trades_today_computed": js.trades_today(),
        "note": "Trade counter should be incremented only after confirmed LIVE submit success (Phase 83 helper exists).",
    })
except Exception as e:
    st.error(f"Phase 83 compute error: {type(e).__name__}: {e}")

st.divider()
st.header("LIVE Safety Gates (Phase 82)")
try:
    import yaml
    from services.risk.killswitch_phase82 import KillSwitch
    from services.risk.live_risk_gates_phase82 import LiveRiskLimits, LiveGateDB

    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    ex_cfg = cfg.get("execution") or {}
    exec_db = str(ex_cfg.get("db_path") or "data/execution.sqlite")

    ks = KillSwitch(exec_db=exec_db)
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Kill switch", "ON" if ks.is_on() else "OFF")
    with colB:
        if st.button("Turn ON", key="ks_on"):
            ks.set(True); st.success("Kill switch ON")
    with colC:
        if st.button("Turn OFF", key="ks_off"):
            ks.set(False); st.warning("Kill switch OFF")

    limits = LiveRiskLimits.from_trading_yaml("config/trading.yaml")
    st.write("Limits:", None if not limits else limits.__dict__)

    db = LiveGateDB(exec_db=exec_db)
    st.write("Today:", db.day_row())
except Exception as e:
    st.error(f"Phase 82 panel error: {type(e).__name__}: {e}")

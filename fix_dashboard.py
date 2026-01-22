# fix_dashboard_placeholder.py - Removes placeholder and adds real panel
from pathlib import Path

def fix_dashboard():
    file_path = Path("dashboard/app.py")
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    content = file_path.read_text(encoding="utf-8")

    # Placeholder patterns to remove
    placeholders = [
        "<PASTE ENTIRE DASHBOARD PANEL BLOCK HERE>",
        "# ... rest of your dashboard panel code ...",
        "# ... (keep your full dashboard panel code here unchanged) ..."
    ]

    modified = content
    for ph in placeholders:
        if ph in modified:
            modified = modified.replace(ph, "")

    # The real panel to insert (Tick Publisher from Phase 102)
    panel_code = r'''
st.divider()
st.header("System Status Tick Publisher")
st.caption("Keeps runtime/snapshots/system_status.latest.json fresh so the Market Data Staleness Guard can verify tick freshness. Public market data only.")
try:
    from services.admin.config_editor import load_user_yaml, save_user_yaml
    from pathlib import Path as _Path
    import json as _json
    import os as _os
    import subprocess as _subprocess
    import sys as _sys
    import platform as _platform
    cfg = load_user_yaml()
    mdp = cfg.get("market_data_publisher") if isinstance(cfg.get("market_data_publisher"), dict) else {}
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues_default = mdp.get("venues") if isinstance(mdp.get("venues"), list) else (pf.get("venues") if isinstance(pf.get("venues"), list) else ["binance","coinbase","gateio"])
    symbols_default = mdp.get("symbols") if isinstance(mdp.get("symbols"), list) else (pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USDT"])
    st.subheader("Controls")
    c1, c2, c3 = st.columns(3)
    stop_file = _Path("runtime") / "flags" / "tick_publisher.stop"
    lock_file = _Path("runtime") / "locks" / "tick_publisher.lock"
    status_file = _Path("runtime") / "flags" / "tick_publisher.status.json"
    with c1:
        if st.button("Start publisher (background)"):
            cmd = [_sys.executable, "scripts/run_tick_publisher.py", "run"]
            try:
                if _platform.system().lower().startswith("win"):
                    DETACHED_PROCESS = 0x00000008
                    _subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                else:
                    _subprocess.Popen(cmd, start_new_session=True, stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                st.success({"ok": True, "started": cmd})
            except Exception as e:
                st.error(f"Start failed: {type(e).__name__}: {e}")
            st.caption("If it refuses, delete the lock file only if you are sure it is not running.")
    with c2:
        if st.button("Request stop"):
            stop_file.parent.mkdir(parents=True, exist_ok=True)
            stop_file.write_text("stop\n", encoding="utf-8")
            st.success({"ok": True, "stop_file": str(stop_file)})
    with c3:
        if st.button("Show run command"):
            st.code("python3 scripts/run_tick_publisher.py run", language="bash")
            st.code("python3 scripts/run_tick_publisher.py stop", language="bash")
    st.subheader("Status")
    st.caption(f"Lock: {lock_file} | Stop file: {stop_file}")
    if status_file.exists():
        st.json(_json.loads(status_file.read_text(encoding="utf-8")))
    else:
        st.warning("No status file yet. Start the publisher or run it in a terminal.")
    st.subheader("Latest snapshot preview")
    snap = _Path("runtime") / "snapshots" / "system_status.latest.json"
    if snap.exists():
        st.caption(str(snap))
        with st.expander("Preview (first ~16k chars)"):
            st.code(snap.read_text(encoding="utf-8")[:16000], language="json")
    else:
        st.warning("system_status.latest.json not found yet.")
    st.subheader("Config (safe write)")
    cur_enabled = bool(mdp.get("enabled", True))
    cur_interval = int(mdp.get("interval_sec", 2) or 2)
    cur_latest = bool(mdp.get("write_latest_only", True))
    cur_maxsym = int(mdp.get("max_symbols_per_venue", 50) or 50)
    enabled = st.checkbox("market_data_publisher.enabled", value=cur_enabled)
    interval = st.number_input("market_data_publisher.interval_sec", min_value=1, max_value=60, value=cur_interval, step=1)
    latest_only = st.checkbox("market_data_publisher.write_latest_only", value=cur_latest)
    maxsym = st.number_input("market_data_publisher.max_symbols_per_venue", min_value=1, max_value=500, value=cur_maxsym, step=1)
    venues_txt = st.text_area("market_data_publisher.venues (one per line)", value="\n".join([str(x) for x in venues_default]))
    symbols_txt = st.text_area("market_data_publisher.symbols (one per line)", value="\n".join([str(x) for x in symbols_default]))
    new_cfg = dict(cfg)
    new_mdp = dict(mdp)
    new_mdp["enabled"] = bool(enabled)
    new_mdp["interval_sec"] = int(interval)
    new_mdp["write_latest_only"] = bool(latest_only)
    new_mdp["max_symbols_per_venue"] = int(maxsym)
    new_mdp["venues"] = [x.strip().lower() for x in venues_txt.splitlines() if x.strip()]
    new_mdp["symbols"] = [x.strip() for x in symbols_txt.splitlines() if x.strip()]
    new_cfg["market_data_publisher"] = new_mdp
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Dry-run (diff only) — tick publisher config"):
            out = save_user_yaml(new_cfg, create_backup=False, dry_run=True)
            st.code(out.get("diff",""), language="diff")
            if not out.get("ok"):
                st.error(out.get("validation"))
    with c2:
        if st.button("Save — tick publisher config (backup + atomic)"):
            out = save_user_yaml(new_cfg, create_backup=True, dry_run=False)
            if out.get("ok"):
                st.success({"written": out.get("written"), "backup": out.get("backup")})
            else:
                st.error(out.get("validation"))
            st.code(out.get("diff",""), language="diff")
except Exception as e:
    st.error(f"Tick publisher panel failed: {type(e).__name__}: {e}")
'''

    # Find a safe insertion point (e.g. after the last st.divider() or before a known header)
    # Here we append at the end if no better marker
    if "st.divider()" in modified:
        # Insert after the last divider
        lines = modified.splitlines()
        last_divider_idx = max(i for i, line in enumerate(lines) if "st.divider()" in line)
        lines.insert(last_divider_idx + 1, panel_code.strip())
        modified = "\n".join(lines)
    else:
        modified += "\n" + panel_code.strip()

    file_path.write_text(modified, encoding="utf-8")
    print(f"Fixed dashboard/app.py - placeholder removed and panel added.")
    print("You can now run: streamlit run dashboard/app.py")

if __name__ == "__main__":
    fix_dashboard()
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


# CBP_BOOTSTRAP: ensure repo root on sys.path so `import services` works when running scripts directly
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from pathlib import Path
import datetime
import re

ROOT = Path(".").resolve()
ATTIC = ROOT / "attic" / ("phase82_" + datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
ATTIC.mkdir(parents=True, exist_ok=True)

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s.lstrip("\n"), encoding="utf-8")

def backup(p: Path) -> None:
    if p.exists():
        (ATTIC / p.name).write_text(read(p), encoding="utf-8")

def safe_patch(p: Path, fn) -> bool:
    if not p.exists():
        print(f"[skip] missing: {p}")
        return False
    before = read(p)
    after = fn(before)
    if after == before:
        print(f"[noop] {p}")
        return False
    backup(p)
    write(p, after)
    print(f"[patch] {p}")
    return True

def append_once(p: Path, marker: str, block: str) -> bool:
    if not p.exists():
        print(f"[skip] missing: {p}")
        return False
    t = read(p)
    if marker in t:
        print(f"[noop] {p} (marker exists)")
        return False
    backup(p)
    write(p, t.rstrip() + "\n\n" + block.lstrip("\n") + "\n")
    print(f"[append] {p} (+{marker})")
    return True

# -----------------------------------------------------------------------------
# A) Repair root install.py (remove YAML tail starting at watchdog:/alerts:)
# -----------------------------------------------------------------------------
install_py = ROOT / "install.py"
def fix_install_py(txt: str) -> str:
    if not txt.strip():
        return txt
    # If watchdog YAML exists, truncate before it
    m = re.search(r"(?m)^(watchdog|alerts)\s*:\s*$", txt)
    if m:
        return txt[: m.start()].rstrip() + "\n"

    # If it ends properly, leave it
    if re.search(r"(?ms)^if __name__ == ['\"]__main__['\"]:\s*\n\s*raise SystemExit\(main\(\)\)\s*$", txt.strip()):
        return txt.strip() + "\n"

    # Otherwise, best-effort truncate after main guard
    m2 = re.search(r"(?ms)^if __name__ == ['\"]__main__['\"]:\s*\n\s*raise SystemExit\(main\(\)\)\s*$", txt)
    if m2:
        return txt[: m2.end()].rstrip() + "\n"
    return txt

if install_py.exists():
    safe_patch(install_py, fix_install_py)
else:
    print("[warn] install.py missing")

# -----------------------------------------------------------------------------
# B) Ensure risk.live defaults exist in config/trading.yaml
# -----------------------------------------------------------------------------
trading_yaml = ROOT / "config" / "trading.yaml"
RISK_BLOCK = """
risk:
  live:
    # HARD gates enforced before any live submit
    max_daily_loss_usd: 25
    max_notional_per_trade_usd: 25
    max_trades_per_day: 5
    max_position_notional_usd: 50
paths:
  kill_switch_file: ".cbp_state/data/KILL_SWITCH.flag"
"""
def ensure_risk_block(txt: str) -> str:
    if "risk:" in txt and "risk:\n" in txt:
        # if keys are missing, append block at end (safe / non-destructive)
        missing = []
        for k in ["max_daily_loss_usd", "max_notional_per_trade_usd", "max_trades_per_day", "max_position_notional_usd"]:
            if k not in txt:
                missing.append(k)
        if missing:
            return txt.rstrip() + "\n\n" + RISK_BLOCK.lstrip("\n")
        # also ensure kill_switch_file path exists somewhere
        if "kill_switch_file" not in txt:
            return txt.rstrip() + "\n\n" + 'paths:\n  kill_switch_file: ".cbp_state/data/KILL_SWITCH.flag"\n'
        return txt
    return txt.rstrip() + "\n\n" + RISK_BLOCK.lstrip("\n")

if trading_yaml.exists():
    safe_patch(trading_yaml, ensure_risk_block)
else:
    print("[warn] config/trading.yaml missing (skipping defaults)")

# -----------------------------------------------------------------------------
# C) Upgrade services/risk/live_risk_gates_phase82.py (add kill-switch FILE support)
# -----------------------------------------------------------------------------
g82 = ROOT / "services" / "risk" / "live_risk_gates_phase82.py"

def patch_gates82(txt: str) -> str:
    if "KILL_SWITCH_FILE_SUPPORT" in txt:
        return txt

    # add Path import if missing
    if "from pathlib import Path" not in txt:
        txt = txt.replace("import sqlite3", "import sqlite3\nfrom pathlib import Path")

    # add kill_switch_file to LiveRiskLimits
    if "kill_switch_file" not in txt and "max_position_notional_usd" in txt:
        txt = txt.replace(
            "    max_position_notional_usd: float\n",
            "    max_position_notional_usd: float\n    kill_switch_file: str = \".cbp_state/data/KILL_SWITCH.flag\"\n"
        )

    # wire kill_switch_file from yaml (paths.kill_switch_file)
    if "paths = cfg.get(\"paths\")" not in txt:
        txt = txt.replace(
            "        risk = (cfg.get(\"risk\") or {}).get(\"live\") or {}",
            "        risk = (cfg.get(\"risk\") or {}).get(\"live\") or {}\n        paths = cfg.get(\"paths\") or {}"
        )
    if "kill_switch_file" not in txt.split("return LiveRiskLimits", 1)[0]:
        txt = txt.replace(
            "        return LiveRiskLimits(mdl, mnt, mtd, mpn)",
            "        ksf = str(paths.get(\"kill_switch_file\") or \".cbp_state/data/KILL_SWITCH.flag\")\n        return LiveRiskLimits(mdl, mnt, mtd, mpn, ksf)"
        )

    # add file check helper + apply in check_live
    inject = """
def _killswitch_file_on(path: str) -> bool:
    try:
        return Path(path).exists()
    except Exception:
        return False
"""
    if "_killswitch_file_on" not in txt:
        txt = txt.replace("class LiveGateDB:", inject + "\nclass LiveGateDB:")

    # modify check_live kill switch logic
    txt = txt.replace(
        "        if self.db.killswitch_on():",
        "        # KILL_SWITCH_FILE_SUPPORT\n        if self.db.killswitch_on() or _killswitch_file_on(self.limits.kill_switch_file):"
    )

    return txt

if g82.exists():
    safe_patch(g82, patch_gates82)
else:
    print("[warn] services/risk/live_risk_gates_phase82.py missing (skipping)")

# -----------------------------------------------------------------------------
# D) Patch services/execution/live_executor.py to use PnLStoreSQLite + incr trades/day
# -----------------------------------------------------------------------------
live_exec = ROOT / "services" / "execution" / "live_executor.py"

def patch_live_executor(txt: str) -> str:
    if "PHASE82_CANONICAL_RISK_PATCH" in txt:
        return txt

    # import PnLStoreSQLite
    if "from storage.pnl_store_sqlite import PnLStoreSQLite" not in txt:
        txt = txt.replace(
            "from storage.order_dedupe_store_sqlite import OrderDedupeStore",
            "from storage.order_dedupe_store_sqlite import OrderDedupeStore\nfrom storage.pnl_store_sqlite import PnLStoreSQLite"
        )

    # replace rpnl source (day_row realized_pnl_usd -> pnl.sqlite realized_day)
    txt = re.sub(
        r"row\s*=\s*gate_db\.day_row\(\)\s*\n\s*rpnl\s*=\s*float\(row\.get\(['\"]realized_pnl_usd['\"]\)\s*or\s*0\.0\)",
        "pnl = PnLStoreSQLite()\n            rpnl = float((pnl.get_today_realized() or {}).get('realized_pnl') or 0.0)  # PHASE82_CANONICAL_RISK_PATCH",
        txt
    )

    # ensure lp estimation for market orders using fetch_ticker when limit_price is None
    if "fetch_ticker" not in txt:
        txt = txt.replace(
            "lp = (float(it['limit_price']) if it.get('limit_price') is not None else None)",
            "lp = (float(it['limit_price']) if it.get('limit_price') is not None else None)\n            if lp is None:\n                try:\n                    ex = client.build()\n                    t = ex.fetch_ticker(str(it['symbol']))\n                    side0 = str(it.get('side') or '').lower()\n                    if side0 == 'buy':\n                        lp = float(t.get('ask') or t.get('last') or t.get('close') or 0.0) or None\n                    else:\n                        lp = float(t.get('bid') or t.get('last') or t.get('close') or 0.0) or None\n                except Exception:\n                    lp = None"
        )

    # pass symbol into gates.check_live (helps future extensions)
    txt = txt.replace(
        "ok2, reason2, meta2 = gates.check_live(it={'qty': float(it.get('qty') or 0.0), 'price': lp}, realized_pnl_usd=rpnl)",
        "ok2, reason2, meta2 = gates.check_live(it={'qty': float(it.get('qty') or 0.0), 'price': lp, 'symbol': str(it.get('symbol') or '')}, realized_pnl_usd=rpnl)"
    )

    # increment trades/day after submit
    if "gate_db.incr_trades" not in txt:
        txt = txt.replace(
            "store.set_intent_status(intent_id=intent_id, status=\"submitted\", reason=f\"remote_id={rid2} client_id={cid2}\")",
            "store.set_intent_status(intent_id=intent_id, status=\"submitted\", reason=f\"remote_id={rid2} client_id={cid2}\")\n\n            try:\n                gate_db.incr_trades(1)\n            except Exception:\n                pass"
        )

    return txt

if live_exec.exists():
    safe_patch(live_exec, patch_live_executor)
else:
    print("[warn] services/execution/live_executor.py missing (skipping)")

# -----------------------------------------------------------------------------
# E) Add Streamlit LIVE Risk panel
# -----------------------------------------------------------------------------
dash = ROOT / "dashboard" / "app.py"
PANEL = r"""
st.divider()
st.header("LIVE Risk Gates — HARD BLOCKS")

st.caption("Enforced before any LIVE submit: kill-switch, max daily loss, max notional/trade, max trades/day (live submits), and (best-effort) position notional.")

try:
    import yaml
    from pathlib import Path
    from services.risk.live_risk_gates_phase82 import LiveRiskLimits, LiveGateDB
    from storage.pnl_store_sqlite import PnLStoreSQLite

    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    ex_cfg = cfg.get("execution") or {}
    exec_db = str(ex_cfg.get("db_path") or ".cbp_state/data/execution.sqlite")

    limits = LiveRiskLimits.from_trading_yaml("config/trading.yaml")
    if limits is None:
        st.error("LIVE risk limits missing/invalid. Fix config/trading.yaml (risk.live.*).")
    else:
        st.subheader("Configured limits")
        st.json({
            "max_daily_loss_usd": limits.max_daily_loss_usd,
            "max_notional_per_trade_usd": limits.max_notional_per_trade_usd,
            "max_trades_per_day": limits.max_trades_per_day,
            "max_position_notional_usd": limits.max_position_notional_usd,
            "kill_switch_file": getattr(limits, "kill_switch_file", ".cbp_state/data/KILL_SWITCH.flag"),
        })

        gate_db = LiveGateDB(exec_db=exec_db)
        day = gate_db.day_row()
        pnl = PnLStoreSQLite().get_today_realized()

        ks_file = Path(getattr(limits, "kill_switch_file", ".cbp_state/data/KILL_SWITCH.flag"))
        st.subheader("Today status")
        st.json({
            "utc_day": day.get("day"),
            "live_submits_today": day.get("trades"),
            "realized_pnl_today": pnl.get("realized_pnl"),
            "killswitch_db": gate_db.killswitch_on(),
            "killswitch_file_exists": ks_file.exists(),
        })

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("KILL SWITCH: ON (block LIVE)"):
                gate_db.set_killswitch(True)
                st.success("Kill switch DB = ON")
        with c2:
            if st.button("KILL SWITCH: OFF"):
                gate_db.set_killswitch(False)
                st.success("Kill switch DB = OFF")
        with c3:
            if st.button("Toggle kill-switch FILE"):
                ks_file.parent.mkdir(parents=True, exist_ok=True)
                if ks_file.exists():
                    ks_file.unlink()
                    st.warning(f"Removed: {ks_file}")
                else:
                    ks_file.write_text("KILL_SWITCH=ON\n", encoding="utf-8")
                    st.success(f"Created: {ks_file}")

except Exception as e:
    st.error(f"LIVE Risk panel error: {type(e).__name__}: {e}")
"""
if dash.exists():
    append_once(dash, "LIVE Risk Gates — HARD BLOCKS", PANEL)
else:
    print("[warn] dashboard/app.py missing (skipping)")

# -----------------------------------------------------------------------------
# F) Docs + CHECKPOINTS update (best-effort)
# -----------------------------------------------------------------------------
write(ROOT / "docs" / "PHASE82_LIVE_RISK_GATES.md", """
# Phase 82 — Mandatory LIVE Risk Gates (hard blocks)

Enforced before any LIVE submit:
- Kill switch (DB flag + optional kill-switch file)
- Max daily loss (uses pnl.sqlite realized_day)
- Max notional per trade
- Max trades per day (counts live submits)
- (Best-effort) position notional guard (future)

Config:
- config/trading.yaml -> risk.live.*
- config/trading.yaml -> paths.kill_switch_file
""")

ck = ROOT / "CHECKPOINTS.md"
if ck.exists():
    marker = "## Phase 82) Mandatory LIVE risk gates (killswitch + max loss/day + max notional/trade + max trades/day) ✅"
    if marker not in read(ck):
        backup(ck)
        write(ck, read(ck).rstrip() + "\n\n" + marker + "\n" + "\n".join([
            "- ✅ Repair root install.py (remove YAML tail)",
            "- ✅ Ensure risk.live defaults exist in config/trading.yaml",
            "- ✅ Add kill-switch FILE support to live risk gates",
            "- ✅ Patch live_executor to use pnl.sqlite realized_day + enforce trade counter",
            "- ✅ Add Streamlit LIVE Risk panel",
            "- ✅ Add docs/PHASE82_LIVE_RISK_GATES.md",
            "",
            "Next: Phase 83 market/symbol validation + min amount/precision enforcement before submit.",
        ]) + "\n")
        print("[ok] CHECKPOINTS.md updated (Phase 82)")
else:
    print("[warn] CHECKPOINTS.md not found (skipping)")

print("\nOK ✅ Phase 82 applied.")
print(f"Backups saved in: {ATTIC}")

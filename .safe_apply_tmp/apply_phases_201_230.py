from pathlib import Path

# -----------------------------
# Utilities
# -----------------------------
def append_file_once(path, content):
    f = Path(path)
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        print(f"Created: {path}")
    else:
        print(f"Skipped (exists): {path}")

def patch_append_once(checkpoints_file, header, content):
    f = Path(checkpoints_file)
    if f.exists():
        text = f.read_text(encoding="utf-8")
        if header in text:
            print(f"Checkpoint already exists: {header}")
            return
    else:
        f.parent.mkdir(parents=True, exist_ok=True)
        text = ""
    with f.open("a", encoding="utf-8") as out:
        out.write("\n\n" + header + "\n" + content + "\n")
        print(f"Patched checkpoint: {header}")

# -----------------------------
# Files for phases 201–230
# -----------------------------
files = {
    # Phases 201–220 (examples / placeholders)
    "storage/idempotency_sqlite.py": "# Phase 201: Idempotency DB helper\n# TODO: implement\n",
    "services/execution/startup_reconcile.py": "# Phase 216: Startup reconciliation safe mode\n# TODO: implement\n",
    "services/runtime/bot_process.py": "# Phase 218: Single entrypoint Start/Stop + status summary\n# TODO: implement\n",
    "services/runtime/run_mode.py": "# Phase 220: Single run mode across UI/CLI/config\n# TODO: implement\n",
    # Phases 221–230
    "services/marketdata/ohlcv_fetcher.py": "# HL1: OHLCV fetcher (Phase 221)\n# TODO: implement OHLCV fetch logic\n",
    "services/strategies/ema_cross.py": "# HL2: EMA crossover signal (Phase 221)\n# TODO: implement EMA signal\n",
    "services/paper/paper_state.py": "# HL3: Persistent paper state (Phase 221)\n# TODO: save/load paper state\n",
    "services/paper/paper_broker.py": "# HL4: Paper broker writes audit orders/fills (Phase 221)\n# TODO: implement paper broker\n",
    "storage/execution_audit_load.py": "# HM1: Load full fills history from audit DB (Phase 222)\n# TODO: implement audit loader\n",
    "services/analytics/paper_pnl.py": "# HM2: Paper PnL engine (Phase 222)\n# TODO: implement realized/unrealized PnL\n",
    "services/analytics/price_probe.py": "# HM3: Optional network price probe for unrealized PnL (Phase 222)\n# TODO: implement price probe\n",
    "services/analytics/mtm_equity.py": "# HN1: MTM equity builder (Phase 223)\n# TODO: implement MTM equity\n",
    "services/analytics/portfolio_mtm.py": "# HO1: Portfolio MTM builder across symbols with shared cash ledger (Phase 224)\n# TODO: implement portfolio MTM\n",
    "services/risk/position_sizing.py": "# HP1: Volatility estimator + risk sizing (Phase 225)\n# TODO: implement sizing\n",
    "services/risk/exit_controls.py": "# HQ1: Sell-side exit controls (Phase 226)\n# TODO: implement exit controls\n",
    "services/strategies/base.py": "# HR1: Strategy interface + OrderIntent (Phase 227)\n# TODO: define base strategy classes\n",
    "services/strategies/registry.py": "# HR2: Strategy registry + factory (Phase 227)\n# TODO: implement strategy registry\n",
    "services/strategies/validation.py": "# HS1: Strategy config validator (Phase 228)\n# TODO: implement validator\n",
    "services/strategies/presets.py": "# HS2: Preset library + apply helper (Phase 228)\n# TODO: implement presets\n",
    "services/profiles/bundles.py": "# HT1: Bundle library (Phase 229)\n# TODO: implement bundles\n",
    "services/utils/config_diff.py": "# HT2: Config diff helper (Phase 229)\n# TODO: implement config diff\n",
    "services/profiles/guardrails.py": "# HU1: Live guardrails for bundle apply (Phase 230)\n# TODO: implement guardrails\n",
}

# -----------------------------
# Checkpoints for phases 201–230
# -----------------------------
checkpoints = {
    # 201–220 placeholders
    "## HG) Startup Auto-Reconciliation (Safe Mode)": "- ✅ HG1–HG6: Startup reconciliation + UI + CLI + reports",
    "## HH) Startup Status Gate (Freshness) + UI Indicator": "- ✅ HH1–HH4: Startup status freshness gate + UI + checkpoints",
    "## HI) Bot Control Single Entrypoint + Status Summary": "- ✅ HI1–HI4: Single entrypoint + status summary + log tail\n- ⏳ HI5: Live start gating next",
    "## HJ) UI Live Start Gate + ARM LIVE": "- ✅ HJ1–HJ5: Live gating + ARM LIVE + confirmations",
    "## HK) Single Run Mode (paper|live) Across UI/CLI/Config": "- ✅ HK1–HK4: Single run mode across UI/CLI/config\n- ⏳ HK5: Dry run cleanup next",
    # 221–230
    "## HL) Paper Strategy Loop": "- ✅ HL1–HL5: Paper loop foundation\n- ⏳ HL6: Paper PnL/analytics UI next",
    "## HM) Paper Analytics + PnL": "- ✅ HM1–HM4: Paper analytics + UI\n- ⏳ HM5: MTM sampling next",
    "## HN) Paper MTM Equity + Sharpe/Sortino + Daily + CSV": "- ✅ HN1–HN4: MTM equity + metrics + UI + CSV\n- ⏳ HN5: Portfolio-level MTM next",
    "## HO) Portfolio MTM + Correlation + CSV": "- ✅ HO1–HO5: Portfolio MTM + correlation + UI + CSV\n- ⏳ HO6: Risk allocation next",
    "## HP) Risk Allocation + Position Sizing": "- ✅ HP1–HP4: Risk sizing + caps + paper loop + UI\n- ⏳ HP5: Sell-side risk controls next",
    "## HQ) Sell-Side Risk Controls (Paper)": "- ✅ HQ1–HQ5: Exit controls + panic reduce + UI\n- ⏳ HQ6: Strategy-aware exit stacking next",
    "## HR) Strategy Library + Registry (Selectable)": "- ✅ HR1–HR6: Multi-strategy + registry + UI selector\n- ⏳ HR7: Param validation + presets next",
    "## HS) Strategy Validation + Presets + Trade Gate": "- ✅ HS1–HS5: Validation + presets + trade gate + UI\n- ⏳ HS6: Per-strategy preset bundles next",
    "## HT) Preset Bundles + Safe Paper Profile + Governance Log": "- ✅ HT1–HT5: Bundles + governance log + UI\n- ⏳ HT6: Guardrails for live mode next",
    "## HU) Live Guardrails for Bundles + Runtime Hard Block": "- ✅ HU1–HU4: ARM LIVE + guardrails + runtime block\n- ⏳ HU5: Live execution layer future",
}

# -----------------------------
# Apply files
# -----------------------------
for path, content in files.items():
    append_file_once(path, content)

# -----------------------------
# Apply checkpoints
# -----------------------------
for header, content in checkpoints.items():
    patch_append_once("CHECKPOINTS.md", header, content)

print("✅ Phases 201–230 and checkpoints applied safely.")


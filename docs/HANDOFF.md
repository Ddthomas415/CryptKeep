# Handoff (copy into a new chat if needed)

## Objective (standing orders)
- Build an installable **Mac + Windows** desktop app for an **advanced crypto trading bot**.
- Start **read-only first** (collect/normalize/store market data) before any live trading.
- Safe/reliable coding path, no fluff, minimal manual steps, always update checkpoints.

## Current status
- Phase 1 scaffold: complete (single “gold” repo, one-command install, Streamlit dashboard).
- Phase 2 read-only data plane: implemented (Binance + Coinbase + Gate.io WS; SQLite event store; dashboard shows latest events).

## How to run
macOS:
```bash
python3 scripts/install.py
./run_collector.sh
./run_dashboard.sh
```

Windows (PowerShell):
```powershell
py scripts\install.py
.\run_collector.ps1
.\run_dashboard.ps1
```

## Next steps
1) Data quality: symbol normalization + dedupe + backfill (REST snapshots for books where needed).
2) Add “sources that affect the market” (news + on-chain + macro) as separate collectors.
3) Execution engine (paper trading first) with strict risk guardrails.
4) Package as an installer (Tauri/Electron or Python-native), with auto-updater.

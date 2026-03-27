# Install (Mac + Windows)

This project installs locally and runs on localhost (Streamlit).
The supported baseline here is the root repo Python platform only.
For that baseline, `requirements.txt` is the dependency source of truth used by the installer when present.
Sidecar workspaces such as `crypto-trading-ai/`, `src-tauri/`, and packaging/release helpers are not part of the required root install/run/test path.

## macOS
1) From repo root:
   - `python3 scripts/bootstrap.py`
2) Double-click the Desktop launcher:
   - `launchers/CryptoBotPro.command`

## Windows
1) From repo root (PowerShell):
   - `py scripts\bootstrap.py`
2) Double-click the Desktop launcher:
   - `launchers\CryptoBotPro.bat`

## Notes
- Install git hooks for this repo with `bash crypto-trading-ai/scripts/install_git_hooks.sh`.
- Desktop launcher prefers http://localhost:8502 and automatically moves to the next free local port when 8502 is busy.
- CLI helpers:
  - `./run_dashboard.sh`
  - `.\run_dashboard.ps1`
- Docker helper:
  - `make docker-up-auto-ports`
- Live trading requires credentials via environment variables (never in code).
- Supported venues (via CCXT): binance, coinbase, gateio.

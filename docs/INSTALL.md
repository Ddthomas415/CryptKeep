# Install (Mac + Windows)

This project installs locally and runs on localhost (Streamlit).

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
- Desktop launcher prefers http://localhost:8502 and automatically moves to the next free local port when 8502 is busy.
- CLI helpers:
  - `./run_dashboard.sh`
  - `.\run_dashboard.ps1`
- Docker helper:
  - `make docker-up-auto-ports`
- Live trading requires credentials via environment variables (never in code).
- Supported venues (via CCXT): binance, coinbase, gateio.

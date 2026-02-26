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
- Desktop launcher opens the app at: http://localhost:8502
- Live trading requires credentials via environment variables (never in code).
- Supported venues (via CCXT): binance, coinbase, gateio.

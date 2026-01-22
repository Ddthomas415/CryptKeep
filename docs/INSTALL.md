# Install (Mac + Windows)

This project installs locally and runs on localhost (Streamlit).

## macOS
1) From repo root:
   - `bash installers/install.sh`
2) Double-click the Desktop launcher:
   - `CryptoBotPro.command`

## Windows
1) From repo root (PowerShell):
   - `powershell -ExecutionPolicy Bypass -File installers\install.ps1`
2) Double-click the Desktop shortcut:
   - `CryptoBotPro.lnk`

## Notes
- The app runs at: http://localhost:8501
- Live trading requires credentials via environment variables (never in code).
- Supported venues (via CCXT): binance, coinbase, gateio.

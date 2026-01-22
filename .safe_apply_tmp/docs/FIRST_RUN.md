# First Run (Phase 345)

In the app:
- Open **First-Run Wizard**
- Click **Run Preflight**
  - Confirms imports (streamlit, ccxt)
  - Confirms port availability (8501)
  - Confirms DB paths are writable
  - Shows presence of env vars (never prints values)

If config is missing/corrupted:
- Click **Restore Missing Configs**
  - Creates `config/trading.yaml` from `config/templates/trading.yaml.default` (never overwrites)
  - Creates `.env.template` in repo root (never overwrites)

Diagnostics export:
- Use **Download Diagnostics JSON** or **Copy Diagnostics**.

# Phase 64 — Setup Wizard + Preflight + Start Bot button

Adds:
- services/setup/config_manager.py
  - generates/loads/saves config/trading.yaml with safe defaults
  - risk presets (safe_paper / paper_relaxed / live_locked)

- services/preflight/preflight.py
  - validates config exists, exchange supported, symbols configured, db writable, live gating, basic env key hints

- services/runtime/process_supervisor.py
  - pidfile-based process control for:
    - pipeline loop
    - executor loop
    - live reconciler loop (optional)

- scripts/start_bot.py / scripts/stop_bot.py / scripts/bot_status.py

UI:
- Adds a “Setup Wizard (First Run)” section to dashboard/app.py:
  - configure exchange, symbol, strategy, sizing, mode
  - apply risk presets
  - save/generate config
  - run preflight
  - START/STOP/STATUS buttons

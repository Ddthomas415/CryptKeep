# Phase 335 — Services Supervisor (WS collector + bot runner)

What it does:
- Runs background services defined in `config/services.yaml`
- Auto-restarts crashed services
- Writes status to `data/supervisor/status.json`
- Writes logs to `data/supervisor/logs/<service>.log`
- Stops cleanly when `data/supervisor/STOP` exists

Commands:
- Start: `python scripts/start_supervisor.py`
- Stop:  `python scripts/stop_supervisor.py`
- Status: `python scripts/supervisor_status.py`

Dashboard:
- “Services Manager” panel can start/stop supervisor and show status.

Launcher:
- Desktop launcher will attempt to auto-start supervisor idempotently.

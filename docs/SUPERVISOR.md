# Supervisor (Phase 201)

## What it does
Starts 2 managed sibling processes:
- Streamlit cockpit
- Watchdog loop

Writes:
- data/supervisor_process.json
- data/logs/cockpit.log
- data/logs/watchdog.log

## Launch (double click)
- macOS: launchers/CryptoBotPro_Supervisor.command
- Windows: launchers/CryptoBotPro_Supervisor.bat

## CLI
Start:
  python scripts/supervisor_ctl.py start

Status:
  python scripts/supervisor_ctl.py status

Stop (hard):
  python scripts/supervisor_ctl.py stop --hard

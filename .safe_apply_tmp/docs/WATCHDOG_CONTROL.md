# Watchdog Control (Phase 202)

If you are not using Supervisor mode, you can run the watchdog loop as a managed PID-tracked process.

## Files
- data/watchdog_process.json
- data/logs/watchdog_loop.log

## CLI
Status:
  python scripts/watchdog_ctl.py status

Start:
  python scripts/watchdog_ctl.py start --interval 15

Stop soft:
  python scripts/watchdog_ctl.py stop

Stop hard:
  python scripts/watchdog_ctl.py stop --hard

Clear stale:
  python scripts/watchdog_ctl.py clear_stale

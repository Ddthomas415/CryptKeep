# Watchdog (Phase 200)

## Purpose
Detect “alive but stuck” bot:
- PID running
- heartbeat not updated for stale_after_sec

## Actions (on stale heartbeat)
- Write crash snapshot (data/crash_snapshot.json)
- Turn kill switch ON
- Optional: stop bot (OFF by default)

## CLI
Run once:
  python scripts/watchdog.py --once

Loop (manual watchdog process):
  python scripts/watchdog.py --loop --interval 15

Show last:
  python scripts/watchdog.py --show_last

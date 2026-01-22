# Crash Snapshot (Phase 199)

## File
- data/crash_snapshot.json

## When it is written
- When the controller hard-kills the bot
- When stop fails and the process remains running (controller writes forensics)

## Contents
- last heartbeat
- bot.log tail
- app.log tail
- pid + controller proc_state

## CLI
Show:
  python scripts/crash_snapshot.py --show

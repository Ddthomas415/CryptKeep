# Crash Snapshot (Phase 199)

## File
- default dev path: `.cbp_state/data/crash_snapshot.json`
- if `CBP_STATE_DIR` is set: `$CBP_STATE_DIR/data/crash_snapshot.json`

## When it is written
- When the controller hard-kills the bot
- When stop fails and the process remains running (controller writes forensics)

## Contents
- last canonical heartbeat payload
- canonical managed-service log tails:
  - `.cbp_state/runtime/logs/market_ws.log`
  - `.cbp_state/runtime/logs/intent_consumer.log`
  - `.cbp_state/runtime/logs/reconciler.log`
- legacy compatibility log tail: `.cbp_state/data/logs/bot.log`
- app logger tail: `.cbp_state/runtime/logs/app.log`
- pid + controller proc_state

## CLI
Show:
  python scripts/crash_snapshot.py --show

# Process Control (Phase 196)

## Files
- data/bot_process.json  (PID + command)
- data/bot_heartbeat.json (last tick / last error)
- data/logs/bot.log (bot stdout/stderr)

## CLI
Status:
  python scripts/bot_ctl.py status

Start:
  python scripts/bot_ctl.py start --venue binance --symbols BTC/USDT

Stop (hard):
  python scripts/bot_ctl.py stop --hard

Stop all:
  python scripts/bot_ctl.py stop_all --hard

## UI
Dashboard → Process Control
- Start Bot
- Stop Bot (hard)
- STOP ALL (hard)
- Heartbeat view
- bot.log tail + download

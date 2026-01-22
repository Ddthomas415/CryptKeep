# Bot Control (Single Source) — Phase 6

The dashboard has a single authoritative control panel:
- Start PAPER Bot (always allowed)
- Start LIVE Bot (blocked unless gates + risk + confirmations pass)
- Stop Bot

LIVE confirmations (only required when live.sandbox=false):
- ENABLE_LIVE_TRADING=YES
- CONFIRM_LIVE=YES

Process state:
- data/bot_process.json (pid, mode, log path)
Logs:
- data/logs/live_bot.log
- data/logs/paper_bot.log

Note:
- If your repo does not yet implement services.bot.paper_runner or live_runner entrypoints,
  the subprocess will exit and logs will show the missing entrypoint. This phase only
  consolidates control and safety checks.

# Hidden Defaults Note

Status: OPEN

## Objective
Record the currently visible hidden defaults on runtime-capable root-runtime paths without changing runtime behavior.

## Updated status
The canonical operator/config path now requires explicit venue and symbol inputs in:
- `scripts/run_bot_safe.py`
- `scripts/bot_ctl.py`
- `services/execution/live_executor.py`

This reduces the launch-path risk from silent defaults on the actively used operator path.
Hidden defaults may still remain in non-canonical or not-yet-classified paths.

## Updated status
Recent landed cleanup:
- `services/pipeline/ema_strategy.py` no longer silently defaults:
  - `exchange_id` to `coinbase`
  - `symbol` to a venue-derived fallback
  - `mode` to `paper`
- commit landed:
  - `dbbf53d` — `config: remove silent runtime defaults from ema strategy cfg`

## Confirmed defaults
The repo currently includes runtime-capable defaults such as:

- default venue: `coinbase`
- default symbol: `BTC/USD`

These appear on runtime-relevant paths including:
- operator/runtime wrappers
- setup/config helpers
- paper/live-capable execution helpers

## Why this is still a blocker
Launch-path venue, symbol, mode, and account selection are not yet consistently explicit.
A developer or operator can inherit production-relevant assumptions from defaults instead of deliberate launch-scope choices.

## Close condition
All launch-path selections are explicit for the chosen supported runtime, including:

1. venue
2. symbol(s)
3. mode
4. account / credentials source

If defaults are retained for local/dev convenience, they must be clearly fenced from the supported launch path.

## Risk
High if runtime behavior changes

## Review lane
READY_FOR_INDEPENDENT_REVIEW if behavior changes

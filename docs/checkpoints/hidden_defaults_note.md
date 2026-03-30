# Hidden Defaults Note

Status: OPEN

## Objective
Record the currently visible hidden defaults on runtime-capable root-runtime paths without changing runtime behavior.

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

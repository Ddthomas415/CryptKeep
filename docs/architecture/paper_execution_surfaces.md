# Paper Execution Surface Classification

Date: 2026-07-03

## Finding

The current tracked source tree no longer contains `services/paper/`, but it
does still contain `services/paper_trader/` and the canonical
`services/execution/paper_engine.py`.

## Classification

| Surface | Classification | Evidence |
|---|---|---|
| `services/execution/paper_engine.py` | `core` | Imported by execution adapters, paper runner, and paper-engine tests |
| `services/paper_trader/` | `compatibility` | Used by `services/trading_runner/run_trader.py` and compatibility tests |
| `services/paper/` | `retired` | Listed as retired in `docs/ARCHITECTURE.md`; not tracked in current source |

## Policy

- New paper execution behavior goes through `services/execution/paper_engine.py`.
- `services/paper_trader/` should not gain new behavior unless a current caller
  requires a compatibility bridge.
- Do not reintroduce `services/paper/` without a new accepted architecture
  decision.

## Open Follow-Up

If `services/trading_runner/run_trader.py` remains supported, write a separate
compatibility plan for whether it should delegate to the canonical paper engine
or be retired.

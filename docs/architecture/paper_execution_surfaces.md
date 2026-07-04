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
| `services/trading_runner/run_trader.py` | `legacy_compatibility_runner` | Paper-only EMA runner using `services/paper_trader/`, journal store, and market-data store |
| `services/paper/` | `retired` | Listed as retired in `docs/ARCHITECTURE.md`; not tracked in current source |

## Policy

- New paper execution behavior goes through `services/execution/paper_engine.py`.
- `services/paper_trader/` should not gain new behavior unless a current caller
  requires a compatibility bridge.
- Do not reintroduce `services/paper/` without a new accepted architecture
  decision.

## Open Follow-Up

Closed 2026-07-04.

`services/trading_runner/run_trader.py` remains a legacy compatibility runner
for local paper-only EMA smoke coverage. It is not a canonical evidence
campaign runner, not a promotion-gate evidence source, and not a place for new
paper execution features.

Compatibility policy:

- keep existing import/integration tests until the runner is retired;
- do not add new strategy families, evidence semantics, or promotion behavior
  to this runner;
- if a future task needs this runner to produce promotion-quality evidence,
  first migrate it to delegate to `services/execution/paper_engine.py` or
  retire it in favor of the canonical supervised paper campaign path.

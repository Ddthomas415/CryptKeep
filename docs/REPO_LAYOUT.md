# Repo layout (Gold)

Canonical top-level dirs:
- adapters/
- core/
- dashboard/
- docker/
- docs/
- scripts/
- services/
- storage/
- backtest/
- tests/

Operational config:
- config/ (runtime YAMLs)

Companion trees currently referenced by the main repo:
- phase1_research_copilot/
  - actively referenced from the main README, Makefile, dashboard research fallback, and tests
  - current repo evidence shows it is a companion subsystem, not dead archive material

Sidecar workspace present in the tree:
- crypto-trading-ai/
  - present with its own backend/frontend/docs/scripts
  - current repo evidence shows test coverage and utility scripts, but not the same level of integration into the main operator/runtime path as `phase1_research_copilot/`
  - treat as sidecar workspace unless a stronger product-scope decision is documented elsewhere

Desktop/build roots:
- `desktop/`
  - currently contains only `desktop/README.md`
  - treat the top-level `desktop/` root as a reserved/documentation placeholder, not as an active code root
  - current desktop-related implementation surfaces visible in the repo live elsewhere, including `src-tauri/`, `packaging/`, and `services/desktop/`
- `build/`
  - current tree contains no checked-in source files under this root
  - treat `build/` as an output-shaped root, not a canonical source location
  - do not place new source modules under `build/`

Local-only state (gitignored):
- data/, runtime/, logs/, .venv/

Validation entrypoint:
- root `/.pre-commit-config.yaml` is intentionally minimal
- active git hooks are currently installed via `core.hooksPath` and point at `crypto-trading-ai/.githooks/pre-commit`
- repo-level validation commands live at the main repo root (`make validate-quick`, `python3 scripts/validate.py --quick`)

Overlapping service families:
- the current tree contains overlapping top-level service families that should be treated as unresolved ownership boundaries until an explicit canonical-owner decision is documented
- examples currently visible in `services/`:
  - `market_data/` and `marketdata/`
  - `paper/` and `paper_trader/`
  - `strategy/` and `strategies/`
  - `trading/` and `trading_runner/`
  - `signals/` and `trader_signals/`
  - `data/` and `data_collector/`
  - `live_router/`, `live_trader_fleet/`, and `live_trader_multi/`
- safe rule: do not consolidate or move these families based on naming similarity alone; document canonical ownership first

Archive:
- attic/ (old/duplicate code moved here; reversible)

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

Non-source workspace material:
- `/.cbp_state/`
  - runtime state, snapshots, journals, logs, and generated evidence artifacts
  - operationally important, but not a canonical source tree
- `/data/`
  - local SQLite stores and runtime-adjacent outputs
  - operationally important, but not a canonical source tree
- `/.venv_x86_backup_20260224_133111/`
  - backup virtualenv content
  - do not treat as source, dependency metadata, or a supported runtime root

Validation entrypoint:
- root `/.pre-commit-config.yaml` is intentionally minimal
- active git hooks are currently installed via `core.hooksPath` and point at `crypto-trading-ai/.githooks/pre-commit`
- repo-level validation commands live at the main repo root (`make validate-quick`, `python3 scripts/validate.py --quick`)

Managed evidence symbol scope:
- the managed paper evidence collector is currently CLI/env driven, not driven by `/.cbp_state/runtime/config/user.yaml` symbol lists alone
- runtime collection symbol comes from `scripts/run_paper_strategy_evidence_collector.py --symbol` and flows into `PaperStrategyEvidenceServiceCfg.symbol`
- the synthetic evidence cycle uses `PaperStrategyEvidenceServiceCfg.evidence_symbol` when set, otherwise it reuses the managed runtime symbol
- `load_user_yaml()` is still passed into the evidence cycle as base configuration, but it does not override the managed evidence symbol by itself
- older docs, journals, and evidence artifacts may still mention historical campaign symbols such as `APR/USD` and `2Z/USD`; treat those as historical evidence inputs, not as the current default managed evidence universe

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
- `attic/`
  - tracked archive content retained inside the repo
  - treat as non-canonical source and do not route new integration work through it

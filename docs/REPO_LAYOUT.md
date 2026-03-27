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

Local-only state (gitignored):
- data/, runtime/, logs/, .venv/

Validation entrypoint:
- root `/.pre-commit-config.yaml` is intentionally minimal
- active git hooks are currently installed via `core.hooksPath` and point at `crypto-trading-ai/.githooks/pre-commit`
- repo-level validation commands live at the main repo root (`make validate-quick`, `python3 scripts/validate.py --quick`)

Archive:
- attic/ (old/duplicate code moved here; reversible)

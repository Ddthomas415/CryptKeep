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

Local-only state (gitignored):
- data/, runtime/, logs/, .venv/

Archive:
- attic/ (old/duplicate code moved here; reversible)

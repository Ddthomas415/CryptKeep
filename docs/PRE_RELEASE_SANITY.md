# Phase 316 — Pre-release sanity suite

Goal:
- A single command that fail-closes on quality issues before you tag and publish.

Local:
- macOS/Linux: `bash scripts/run_sanity.sh`
- Windows: `powershell -ExecutionPolicy Bypass -File scripts\run_sanity.ps1`

What it runs:
- alignment gate (`python scripts/check_repo_alignment.py`)
- ruff (lint)
- mypy (type check) with ignore-missing-imports
- YAML config validation (config/**/*.y*ml)
- import smoke (PyYAML + requests required; ccxt/pandas/numpy optional)
- pytest if tests/ exists

Useful flags:
- `--skip-ruff` for constrained local environments where ruff is not installed
- `--json` for machine-readable status output (works with skip flags; includes `schema_version`, `mode`, `started_at`, `finished_at`, `duration_seconds`)
  - `mode` values: `quick` (all skip flags), `full` (no skip flags), `custom` (mixed skip flags)
  - `CBP_PRE_RELEASE_SKIP_PYTEST=1` can be combined with skip flags (for example `--skip-ruff --skip-mypy`) and marks `pytest` as skipped in JSON output

CI:
- `.github/workflows/ci-sanity.yml` runs on PR + main.

# Phase 316 — Pre-release sanity suite

Goal:
- A single command that fail-closes on quality issues before you tag and publish.

Local:
- macOS/Linux: `bash scripts/run_sanity.sh`
- Windows: `powershell -ExecutionPolicy Bypass -File scripts\run_sanity.ps1`

What it runs:
- ruff (lint)
- mypy (type check) with ignore-missing-imports
- YAML config validation (config/**/*.y*ml)
- import smoke (PyYAML + requests required; ccxt/pandas/numpy optional)
- pytest if tests/ exists

CI:
- `.github/workflows/ci-sanity.yml` runs on PR + main.

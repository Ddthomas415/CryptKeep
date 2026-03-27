# Crypto Bot Pro (Gold Repo)

Crypto Bot Pro is a crypto-first operator platform for market-data collection, paper trading, guarded live execution, reconciliation, and dashboard-based operations. The current repo includes both research/evaluation workflows and execution surfaces, so it should be treated as a safety-aware trading system under active hardening, not as a read-only market-data bundle.

Supported production surface for current hardening:
- root repo Python platform only
- supported baseline commands in this README cover the root install/run/test path
- root dependency source of truth for that baseline is `requirements.txt`
- sidecar workspaces such as `crypto-trading-ai/`, `src-tauri/`, and packaging/release helpers are not part of the required local production baseline for this root path

## Install (no bouncing)
### macOS
```bash
python3 scripts/install.py
./.venv/bin/python -m services.data_collector.main
./run_dashboard.sh
```

### Windows (PowerShell)
```powershell
py scripts\install.py
.\.venv\Scripts\python.exe -m services.data_collector.main
.\run_dashboard.ps1
```

## Notes
- Status + scope: see `DECISIONS.md` and `CHECKPOINTS.md`.
- Ops-risk integration contract: see `docs/OPS_RISK_GATE_INTEGRATION.md`.
- AI engine scaffold: see `docs/AI_ENGINE.md`.
- Root install/bootstrap currently supports the root Python platform only.
- Git hooks are installed via `core.hooksPath` and currently point at `crypto-trading-ai/.githooks/pre-commit`; the root `.pre-commit-config.yaml` is intentionally minimal rather than a second active hook system.
- Install the current git-hook path with `bash crypto-trading-ai/scripts/install_git_hooks.sh`.
- Dashboard API defaults to `CK_API_BASE_URL=http://localhost:8000`.
- Dashboard research explain fallback can target the Phase 1 copilot with `CK_PHASE1_ORCHESTRATOR_URL=http://localhost:8002`.
- Phase 1 copilot smoke check: `make phase1-smoke`
- `./run_dashboard.sh` and `.\run_dashboard.ps1` auto-switch to the next free local dashboard port if the requested one is already in use.
- `make docker-up-auto-ports` starts the Docker stack with the next free host ports for backend and dashboard when the defaults are busy.
- `crypto-trading-ai/`, `src-tauri/`, and packaging/release helpers remain companion or release-engineering surfaces, not part of the required root install/run/test baseline.

## Repo Alignment Commands
```bash
make check-alignment
make check-alignment-list
make check-alignment-list-json
make check-alignment-json
make check-alignment-json-fast
make validate-quick
make validate-json-quick
make validate-json-fast
make validate-json
make validate
make pre-release-sanity
make pre-release-sanity-quick
make pre-release-sanity-json-quick
make pre-release-sanity-json-fast
make test-runtime
make test-checkpoints
```

Validation lanes:
- `make validate-quick` and `make validate` remain the main repo-level gates
- `make test-runtime` runs top-level tests excluding `test_checkpoints*`
- `make test-checkpoints` runs the checkpoint-formatting / repo-hygiene lane separately
- `make test` still runs the full top-level pytest suite

Fast full JSON (skip inner pytest):
```bash
CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json
```

Fast alignment JSON (skip guard tests):
```bash
CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json
```

Fast pre-release full JSON (skip inner pytest):
```bash
CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy
```

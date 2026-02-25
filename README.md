# Crypto Bot Pro (Gold Repo)

## Install (no bouncing)
### macOS
```bash
python3 scripts/install.py
./run_collector.sh
./run_dashboard.sh
```

### Windows (PowerShell)
```powershell
py scripts\install.py
.\run_collector.ps1
.\run_dashboard.ps1
```

## Notes
- Phase 2 is **read-only** market data collection (no trading).
- Status + scope: see `DECISIONS.md` and `CHECKPOINTS.md`.
- Ops-risk integration contract: see `docs/OPS_RISK_GATE_INTEGRATION.md`.
- AI engine scaffold: see `docs/AI_ENGINE.md`.

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
```

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

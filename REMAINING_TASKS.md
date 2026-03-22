# Remaining Tasks

Source: `CHECKPOINTS.md`

## Summary
- Total non-✅ items: 4
- 🔄 In progress: 0
- 🟡 Partial: 0
- ⏳ Not started: 0
- ⚠️ Constraint/note: 4

## 🔄 In Progress (0)


## 🟡 Partial (0)


## ⏳ Not Started (1)




- Implement governance smoke target in `Makefile`
  - Add `.PHONY: governance-smoke`
  - Target commands:
    - `python3 tools/repo_doctor.py --strict`
    - `./scripts/manual_repo_audit.sh quick`
    - `./.venv/bin/python -m pytest -q tests/test_manual_repo_audit_paths.py`
  - Validation:
    - `make governance-smoke` exits 0

## ⚠️ Constraint / Note (4)

- UX Safety rule: terminal must remain a controlled product console only; no unrestricted shell access from UI
  Source: `CHECKPOINTS.md:1997`
- API Safety rule: terminal endpoints must route only approved product commands; never expose raw shell execution
  Source: `CHECKPOINTS.md:2012`
- DB Safety rule: encrypted credential material must never be logged or returned in API responses
  Source: `CHECKPOINTS.md:2025`
- SM Safety rule: no service may bypass state-machine guards for execution-affecting transitions
  Source: `CHECKPOINTS.md:2037`

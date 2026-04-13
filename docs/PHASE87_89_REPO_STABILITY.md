# Phase 87–89 — Repo Stability / Gold Alignment

## Phase 87 — Script bootstrap everywhere
- Injects repo-root sys.path bootstrap into scripts/*.py to fix:
  - ModuleNotFoundError: No module named 'services'

## Phase 88 — Preflight + Repo Doctor
- scripts/preflight_check.py
- tools/repo_doctor.py

## Phase 89 — Gold-layout alignment tool (dry-run by default)
- tools/align_gold_layout.py
  - dry-run prints plan
  - --apply moves non-canonical top-level dirs into attic/legacy_*

Backups saved in: <your-repo-path>/attic/phase87_89_20260218_044830

# Commit/PR packaging plan for the uncommitted work (2026-10-09) - PLAN ONLY, nothing committed

Author: Claude (cloud session). Read-only inventory of branch codex/research-bundle-proof (HEAD 620bc8dbe):
2,575 status entries = 35 modified tracked files + 2,540 untracked files. Sizes: research/research_corrections_20261009
24 MB (1,404 files are calibration checkpoints cmc_confirmation_v1/v2), cmc_trending_log/snapshots 7.7 MB,
docs/research/raw_archives_20261009 68 MB.

## Blockers before any commit
1. Git cannot run safely from the laptop VM until deletion is allowed in crypto-bot-pro (git deletes its own
   .lock files; without that, commit/stash leave stale locks). Needs Damian's approval of folder delete permission,
   or commits made from the Mac terminal.
2. Push/merge only with Damian's explicit OK (standing rule). PRs go to master per repo workflow.
3. Large data (68 MB raw archives, 24 MB corrections, snapshots) should not go into normal commits without a
   decision: options are git LFS, a release asset, or keeping hashes in-repo and data outside.

## Proposed scoped PRs (each only reviewed/accepted content; unfinished items stay uncommitted)
| # | Scope | Files | Review state |
|---|---|---|---|
| 1 | ES execution-identity chain | services/strategies/{execution_identity,runtime_execution_identity,market_context_capture}.py; services/execution/{paper_engine,intent_reconciler,_executor_reconcile,strategy_runner}.py; services/journal/fill_sink.py; storage/{paper_trading,trade_journal,execution_store}_sqlite.py; matching tests; docs/checkpoints/es_* | identity capture + journal slices ACCEPTED_WITH_RISK; durable storage slice: CLOUD review recommends ACCEPT WITH RISK, human acceptance pending. Hold until accepted. |
| 2 | Corrected historical reruns | scripts/research/rerun_frozen_*.py, corrected_research_math.py, tests/test_rerun_*.py, docs/research/*_corrected_rerun_20261009.md, small result JSONs | reviewed/accepted with risk per R08 |
| 3 | CMC logger v3 + identity map + evaluator/report/statistics/book evidence | docs/research/cmc_trending_log/*.py,*.md (not snapshots), scripts/research/cmc_*.py, run_cmc_diagnostic_report.py, tests/test_cmc_*.py | mostly ACCEPTED_WITH_RISK; quote qualification (cmc_quote_qualification.py, run_cmc_qualified_report.py) READY_FOR_INDEPENDENT_REVIEW - exclude until reviewed |
| 4 | Calibration study (negative result) | scripts/research/*calibration*.py, tests, contracts/result docs; checkpoint data via LFS/hash manifest | ACCEPTED_WITH_RISK (NO_CERTIFIED_SAMPLE) |
| 5 | Governance/docs edits | AGENTS.md, REMAINING_TASKS.md, runtime_prompt.md, docs/*.md, tools/repo_doctor.py, governance tests | owner: integrating session - confirm before packaging |
| 6 | strategy_feedback / strategy runner changes | services/analytics/strategy_feedback.py + tests | status unknown to CLOUD - ask owner |
| 7 | Older review artifacts | docs/review_artifacts/* (108 files) | historical; decide keep vs archive |
Each PR: own branch from current master, targeted test command in the PR body, no unrelated files.

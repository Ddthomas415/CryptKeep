# Paper Quote and Recovery Correction Handoff

Active role: ENGINEER. HIGH risk, isolated candidate only. Independent reviewer
Fermat disposition: INCOMPLETE. Do not deploy this candidate.

Candidate: /private/tmp/cryptkeep-paper-correction-20261004, based on the prior
isolated assembled bundle. correction.patch contains only this bounded delta;
it does not contain or authorize earlier live-order changes in that candidate.

SHOWN: supplied quote validation now checks the same quote used to price the
paper fill. Existing live guard API/defaults and venue-fetch handling remain.
Recovery uses persistent ascending rowid pagination, avoiding the latest-500
window. Added restart-persistence and 505-row pagination tests. Gate-mocked
fixtures now also stub the new exact-quote evaluator; the independent freshness
probe still uses the real evaluator.

Verification, Python 3.12.10, temporary state, bytecode/cache writes disabled:
`env PYTHONDONTWRITEBYTECODE=1 /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_codex_0040_0044_probe.py tests/test_paper_engine_cost_config_validation.py tests/test_paper_ledger_fill_validation.py tests/test_paper_fill_quote_freshness.py tests/test_paper_collector_dead_man.py tests/test_paper_fill_evidence_backfill.py tests/test_market_quality_guard.py tests/test_market_quality_strict_template.py tests/test_paper_engine_integration.py tests/test_paper_engine_limit_and_status.py tests/test_paper_engine_currency.py --tb=short`
Result: 150 passed in 5.57s. Both original failure probes pass.

Independent static review confirms the exact-quote fix and pagination, but finds
a blocker: a persistently failing evidence row prevents cursor advancement and
aborts the sweep, starving later fills, including unrelated strategies. Preserve
the failed repair obligation while allowing bounded progress past it. Required
next proof: failed-row isolation, retry after recovery, restart persistence, and
independent re-review. Do not merely discard the failed record.

Review did not run tests. Engine recreation is not a process-kill test. Concurrent
sweeps, logger durability, database replacement and runtime operation remain
unverified. No full suite, CI, host or real exchange proof. Main source/config,
accounts and collectors untouched; no push, merge or deployment.

Acceptance state: INCOMPLETE after independent review. Implementation checkpoint
preserved at docs/review_artifacts/paper_quote_recovery_correction_20261004/.

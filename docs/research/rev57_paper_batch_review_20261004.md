# Patches 0040-0044 Bounded Review

Active role: AUDITOR. Overall batch: INCOMPLETE. No runtime changes applied.

## Findings

P2, SHOWN, 0042: paper_engine.py:624-641 reads a quote into q, then the
market-quality guard independently reads the current snapshot. A publisher
refresh between those reads lets the guard approve fresh data while the fill
uses the earlier stale price. Independent deterministic probe captures a
three-hour-old 40000 quote, refreshes the snapshot to 61000, and observes a buy
fill at 40020 including configured slippage. Expected no fill; probe fails.
Validate freshness and spread on the exact quote used for execution, or return
the validated quote from one coherent read. Keep the order pending on refusal.

P2, SHOWN, 0044: paper_engine.py:571 reads only the newest limit fills, without
a cursor or unresolved-fill query. Once missing evidence falls outside that
page, repeated sweeps cannot reach it. Probe creates two missing records and
sweeps twice with limit=1; only the newer record is recovered. The same boundary
exists at the default 500. Recovery must advance through eligible ledger fills
or query unresolved records; preserve the historical cutoff and idempotency.

## Dispositions

- 0040: ACCEPTED_WITH_RISK for bounded numeric validation and entry refusal.
  Invalid costs are replaced by defaults for exits, so resulting paper PnL is
  not validated account-cost evidence. No actual fee schedule was checked.
- 0041: ACCEPTED_WITH_RISK for invalid-fill refusal and float-rounding closure.
  Negative fees/rebates are intentionally unsupported; venue-separated account
  ownership and arbitrary corrupted ledger inputs remain outside this review.
- 0042: INCOMPLETE pending exact-quote validation and regression.
- 0043: ACCEPTED_WITH_RISK for paper heartbeat emission and future-skew checks.
  Scheduling, external alert delivery and host operation remain unverified.
- 0044: INCOMPLETE pending complete bounded recovery traversal and regression.
  Backfilled PnL remains unknown; a recovered row is not profit validation.

## Verification

VERIFIED_ENV: isolated /private/tmp/cryptkeep-rev56.3fTGQR, local venv Python
3.12.10. Numbered 0040-0044 are the supplied versions in the existing assembled
candidate; no independent full-series acceptance is inferred.

`env PYTHONDONTWRITEBYTECODE=1 /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_paper_engine_cost_config_validation.py tests/test_paper_ledger_fill_validation.py tests/test_paper_fill_quote_freshness.py tests/test_paper_collector_dead_man.py tests/test_paper_fill_evidence_backfill.py`

Result: 72 passed in 1.66s.

Independent probe, copied into the isolated tree as
tests/test_codex_0040_0044_probe.py: 2 failed in 0.24s. Preserved unchanged at
docs/review_artifacts/shared_submission_review_20261004/rev57_paper_batch_probe.py.
These are simulated races/recovery windows, not demonstrated live incidents.
No full suite, CI, real exchange or Hetzner test performed. No account/config,
collector, merge or deployment change. Correct 0042 and 0044 in isolation and
request re-review; do not stack unrelated trading work.

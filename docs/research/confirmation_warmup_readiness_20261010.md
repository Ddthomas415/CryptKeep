# coinbase_confirmation_usd_v1 - warm-up readiness record (PREPARE ONLY), 2026-10-10

Claude (cloud session), approved check-in R10. NOT an activation: no scoring, no simulate run, no date change, no
account/campaign/scheduler created. Work log checked first: no other session had completed this step.

Steps (laptop VM, Python 3.12 venv outside the repo; registered runner unchanged, sha256 4aaac1a6...):
1. Backfilled the 24 completed hourly bars 2026-10-09 00:00-23:00 UTC per product with the existing
   scripts/research/run_ohlcv_archive_backfill.py (public Coinbase data, archive only). Receipts:
   {BTC,ETH,SOL,ADA,XRP}_warmup_completion_backfill_20261010.json - each ok, rows_written 24.
2. Coverage (runner --mode coverage --phase warmup): warmup_coverage_complete_20261010.json -
   full_phase_completed true; all five ARCHIVE_VERIFIED with exactly 300 bars (2026-09-27 12:00 -> 2026-10-10 00:00).
3. Prefix integrity: the first 276 bars of each product still hash to the 2026-10-09 preflight rows_sha256 (all 5 True).
4. Freeze (runner --mode freeze --phase warmup --registration registration_20261009.json):
   warmup_freeze_manifest_20261010.json (sha256 3a2ba0a2...), kind CONTENT_FREEZE_NOT_AUTHENTICITY_PROOF,
   registration_sha256 b979c626..., plan sha256 11fd2a75... (unchanged).
   warmup rows_sha256: BTC c69e7c83..., ETH 7633cd1b..., SOL 395412c7..., ADA 8509608f..., XRP 361fe71e...

Status: WARMUP_VERIFIED_AND_FROZEN. Activation/evaluation remains a separate decision under the accepted contract;
evaluation window 2026-10-10 -> 2027-04-08, descriptive checkpoint 2027-01-08. Registration predates the start.
Limit: the freeze proves the archived content is unchanged from now on, not that Coinbase's data is authentic.

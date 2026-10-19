# Independent review: optional level-1 book capture in logger v3

Reviewer: Claude (cloud session), ~11:05 UTC 2026-10-09. No code, schedule or snapshot edited.
Reviewed: cmc_trending_logger_v3.py sha256 e97f93fa... (mtime 10:54); level1_capture_amendment_20261009.md (10:55);
probes research_corrections_20261009/cmc_level1_probe_*.json; daily scheduled task trig_012ybaBYn3NNN3cqx38BTRjV.
Tests: test_cmc_trending_logger_v3.py + test_cmc_snapshot_evidence.py + test_run_cmc_diagnostic_report.py: 20 passed.

## Verdict: code ACCEPTABLE WITH RISK; process findings need the operator

Code: the flag is off by default; books are stored in a separate key (coinbase_level1_books) and never replace
ticker quotes; base.request never raises (errors are recorded per product); BTC-USD and ETH-USD always added;
product IDs URL-encoded; each entry labeled NOT_FILL_PROOF. 28 tracked products + 2 = 30 sequential public GETs
after the ticker pass; a manual default-TLS GET of /products/BTC-USD/book?level=1 from this laptop returned 200.

## Findings
1. HIGH (process) - the unattended daily task now runs the unreviewed option. The task's prompt contains
   `--capture-level1` and its updated_at is 10:58:59 UTC, three minutes after the amendment stating "The schedule has
   not been edited" and "no live API or unattended run has verified this option". Time and permissions are
   unchanged. The amendment is now inaccurate and the option goes live at 13:52 before independent acceptance.
2. MEDIUM (preservation) - the accepted v3 collector (collector_sha256 108d9da4..., recorded in the 05:03/05:09
   snapshots) was edited in place; no copy of that source remains (both .pyc caches are of the new 4417-byte file).
   The ticker path looks unchanged by reading, but byte-level equivalence with the accepted version cannot be shown.
   From 13:52 snapshots carry collector_sha256 e97f93fa...; any scorer must accept both hashes explicitly.
3. LOW - book quotes are fetched seconds after the tickers, so they are not simultaneous with the ticker quotes
   used for entries; no pacing between the 30 requests (expected well under Coinbase's public limit, unverified).
4. LOW - the first probe (10:59:26) failed TLS verification; the second used an installed certifi bundle. The
   scheduled task forbids changing TLS, and default TLS worked for me at ~11:04, so this looks transient. R07 should
   check the 13:52 snapshot for book errors.

Not in scope: R03 thresholds (none inferred, correctly). Nothing here qualifies quotes as executable.

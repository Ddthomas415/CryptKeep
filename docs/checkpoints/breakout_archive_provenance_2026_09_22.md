# Breakout Archive Provenance Review

Active role: AUDITOR. Read-only inspection, not a new backtest or campaign decision.
Inspected against master adde462ff. Historical local artifact:
`.cbp_state/data/research/archive_walk_forward/breakout_default_btcusdt_5m_research_enabled_walk_forward.latest.json`.
Artifact SHA256: ea7adea203e2d6681f649c935c2661ecd888ae9e7bdd0bf95331ddcb04ab30a7.

## Findings

- SHOWN: current referenced YAML reproduces the stored canonical config hash
  8eb61fc59bdebceb87364db985f7abedd77816d56ccb15b504d442eb6b17c070.
  It enables Donchian 20 for research only, with campaign_enabled and
  promotion_candidate false. This verifies config content, not historical execution.
- SHOWN: the artifact reports four negative evaluation windows, 13 closed
  trades, mean return -2.847715%, and average drawdown 3.715460%.
  These are stored results, not independently recomputed performance.
- UNVERIFIED: actual historical fees, slippage, initial cash and code revision.
  They are not recorded in this artifact. The current CLI passes separately
  configurable fee/slippage arguments (defaults 10/5 bps) to the engine;
  neither those defaults nor the YAML hash proves the historical argument values.
- SHOWN: 1500 rows are reported between 2026-06-01 00:00 UTC and
  2026-06-06 06:35 UTC inclusive. That span contains 1520 five-minute slots.
  Thus the summary does not establish contiguous coverage despite complete=true.
  Exact missing/duplicate/off-grid timestamps require inspecting the source rows;
  this review does not assert exactly 20 missing bars or attribute losses to gaps.
- UNVERIFIED: the stored dataset hash against today's archive. No archive read,
  fetch, repair or simulation was performed. The short historical window is not
  a matched-period comparison with the all-history paper journal.

## Disposition

### Completed Source-Row Inspection

Subsequent read-only SQLite inspection supersedes the unverified dataset-hash
and exact-gap questions above. Opened the artifact's archive URI with mode=ro
and PRAGMA query_only=ON, selected ts_ms,o,h,l,cl,v from market_ohlcv for
coinbase / BTC/USDT / 5m, ts_ms >= 1780272000000, ordered ascending, limit 1500.
The existing ohlcv_dataset_hash function reproduced
6415c95900ddc6a72d0a653adcee186e7207ed039464610ee7d1896c1b6ab523 exactly.
Both endpoints also match. All 1500 timestamps are unique and on the 5m grid.
Exactly 20 expected timestamps are absent within the recorded endpoint span:

| UTC date | Missing UTC times |
| --- | --- |
| 2026-06-01 | 05:40, 05:55, 09:10, 09:15, 09:40, 09:45, 09:55, 11:40, 19:10, 20:55 |
| 2026-06-02 | 00:25, 04:30, 11:15, 11:40 |
| 2026-06-03 | 18:05, 18:25 |
| 2026-06-05 | 05:15 |
| 2026-06-06 | 00:35, 01:00, 01:40 |

The inspected loader sets complete from row count >= requested limit, not
timestamp continuity. No cause is established for the absent candles: upstream
absence and collection loss remain distinct possibilities. No data was fetched,
fabricated, inserted or changed. Gap impact on the reported losses is unverified.
Historical cost arguments remain unknown. Do not repeat this completed census.

### Historical Invocation Search Closed

Searched tracked docs and local research JSON/text/log artifacts for the config
name, artifact name, generation timestamp and dataset hash. No invocation tying
fee/slippage arguments to the early single-config artifact was found in that
scope. This is not proof that no external record exists; its costs remain unknown.

An existing work-log entry dated 2026-08-01T21:10:15Z records the later sweep
command explicitly with --fee-bps 10 --slippage-bps 5. The corresponding local
archive_parameter_sweep/breakout_default_btcusdt_5m_sweep.latest.json reports
12 successful variants; its best mean test return is -0.603437%, with 1/4
non-negative windows. The associated triage has zero review candidates and
reason=insufficient_review_candidates. These are inspected historical reports,
not independently rerun economic results.

Crucially, the sweep dataset hash is
a773808b2690cc2106ac4dca5cab91943732cf512da9a7bcc183749638475983, not the
single-config artifact's 6415c959... hash. Its documented cost arguments cannot
be transferred to the earlier run. Sweep source continuity was not checked here.

Do not use the early artifact alone to retire, tune, promote or expand breakout.
Preserve both results unchanged. The source census and bounded invocation search
are complete; do not repeat them or the already-completed sweep merely to fill
the historical cost gap. No supported replacement parameter set emerged from
that sweep. Any future comparison needs a distinct predeclared question and
explicit data/cost provenance, not retroactive relabeling of these results.
No extra campaign, ES retrospective sweep or campaign change is warranted by
this review. Close this audit without claiming profitability or universal failure.

Verification: parsed existing JSON/YAML, recomputed canonical config SHA256,
hashed artifact bytes, and calculated endpoint slot count. Inspected CLI and
walk-forward parameter forwarding. No runtime code changed; tests not run for
this documentation-only review. Acceptance: ACCEPTED for bounded audit facts,
not economic efficacy or source-data completeness.

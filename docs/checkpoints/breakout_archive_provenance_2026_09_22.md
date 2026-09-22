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

Do not use this artifact alone to retire, tune, promote or expand breakout.
Preserve it unchanged as a historical research result with limited provenance.
Before any new simulation, inspect the identified archive rows read-only to
verify the hash and timestamp census. Recover a contemporaneous invocation if
available; otherwise label historical costs unknown rather than infer defaults.
Any later explicit-cost comparison is a separate research artifact, not a repair
of this historical result. No extra campaign or ES retrospective sweep is needed.

Verification: parsed existing JSON/YAML, recomputed canonical config SHA256,
hashed artifact bytes, and calculated endpoint slot count. Inspected CLI and
walk-forward parameter forwarding. No runtime code changed; tests not run for
this documentation-only review. Acceptance: ACCEPTED for bounded audit facts,
not economic efficacy or source-data completeness.

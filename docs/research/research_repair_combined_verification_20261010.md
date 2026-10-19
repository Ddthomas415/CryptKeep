# Research repairs: combined verification

Role: AUDITOR. Scope: October 9 approved research repair, local environment only.
Status: ACCEPTED_WITH_RISK for this combined evidence report.
Separate Hooke review found no blockers: independently reran all261 selected
tests (3.51 seconds, cache/bytecode writes disabled), verified seven archive and
seven economic hashes, and checked saved diagnostic status/counts. This does
not accept overall research completion or broaden underlying implementation
acceptance.
Not a full repository audit, deployment approval or profitability certification.

## Shown verification

| Check | Current result | Limit |
|---|---|---|
| Combined repair regression | 261 passed in 4.54 seconds | Selected research tests, not full repo suite |
| Seven frozen archive checksums | All seven match | Compressed archives; no new extraction or historical reruns |
| Seven economic-report source hashes | All seven match | Saved-artifact integrity, not execution realism |
| Coinbase forward archive | 311 contiguous hourly bars in each of five USD markets | 300 warmup plus eleven evaluation hours; no early scoring |
| Frozen warmup and contract identities | All five warmup hashes and source identities match | Content preservation, not independent exchange authenticity |
| Integrated CMC qualified report | 101 HISTORY_UNCERTAIN; zero qualified seven-day outcomes | Both views NOT_READY_90_DAYS; primary gate blocked |
| Scheduling | One natural daily run previously verified; weekly first run pending | No current scheduler reconfiguration or sustained-health claim |

Regression command:

```sh
./.venv/bin/python -m pytest -q $(rg --files tests | rg 'test_(cmc_|calibrate_cmc|report_cmc|run_cmc|rerun_frozen|frozen_altcoin|frozen_breakout|frozen_majors|corrected_research|coinbase_confirmation)')
```

Archive check: `shasum -a 256 -c SHA256SUMS_archives.txt` in the frozen archive
directory. Report sources verified against the seven SHA256 values in
`consolidated_economic_summary_20261010.md`.

Integrated output is preserved separately at
`research/research_corrections_20261009/cmc_combined_verification_20261010T112042Z.json`.
Its fixed as-of is 11:20:42 UTC, not an assertion of later capture health.

## Corrections made during this verification

Separate reviewer identified stale ledger progress counts, completed local
summaries still described as open, stale diagnostic-review wording, and an
economic summary sentence failing to distinguish V4 from V2/V3. Reconciled
those statements without changing figures, strategies, thresholds or acceptance
scope. No reproducible behavior defect appeared in the combined test selection.

## Completion boundary

Software and historical reporting have bounded verification. Overall research
completion remains INCOMPLETE: market-applicable CMC inference is not established,
natural weekly scheduling is not yet observed, and mature forward evidence does
not exist. V4's finite-family pass is not a replacement for the registered primary
target. Positive historical gains remain visible without becoming live claims.

No original artifacts overwritten, strategy reruns, background jobs, external-app
interaction, account mutation, campaign changes, live orders or deployment.

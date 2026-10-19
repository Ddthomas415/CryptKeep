# R06 integration verification (independent, reviewer-written probes) - 2026-10-09

Claude (cloud session); synthetic snapshots in temp dirs; run_cmc_diagnostic_report.py sha256 312da745...,
cmc_statistics.py as of 11:02. No repo code edited. Reproduce from repo root:
`python3 -B docs/research/cmc_trending_log/integration_verification_20261009/probe_e2e.py` and
`python3 -B .../probe_stats.py docs/research/cmc_trending_log/integration_verification_20261009`.

| Case (owner list item 6) | Input | Result | OK |
|---|---|---|---|
| End-to-end scored path | 40 clean days, coin enters day 40, daily tracked quotes, BTC paired | 1/7/30-day DIAGNOSTIC; 7d excess 0.1933237 = hand value 0.193324 (1.2%/side) | yes |
| Collection gap | one missing day inside the prior 30 | HISTORY_UNCERTAIN, not scored | yes |
| Identity collision at entry | entry row identity_eligible false | EXCLUDED_IDENTITY | yes |
| Identity excluded at endpoints | tracked rows identity_eligible false | MISSING at 1/7/30 (not invented) | yes |
| Duplicate capture same day | second capture 30 min later | one event; first observation kept | yes |
| Missing benchmark at entry | no BTC quote at entry capture | INVALID_ENTRY_QUOTE all horizons | yes |
| Missing benchmark at endpoint | no BTC at the +7d capture | 7d MISSING (no other capture within +/-12h); 1d/30d scored | yes |
| Malformed snapshot | invalid JSON file | listed in rejected_envelopes; run continues | yes |
| Immature cohort | covered by existing test_candidate_without_mature_endpoint_not_scored | not scored | yes |
| Statistics wiring | 60 coins, 60 entry days, bids 103/104/105 | events 60, entry_days 60, mean 0.0386647 = hand 0.038665; all intervals DESCRIPTIVE | yes |

Not verified here (open elsewhere): quote freshness/provenance/size (R03); the operator's all-ranges-above-zero
gate and 7-day missing-outcome counts (R05 implementation in progress); real unattended snapshot (R07).
Status: integration behaviour VERIFIED for the listed cases; final independent review of the frozen version
still waits for R03 and R05 to be finished.

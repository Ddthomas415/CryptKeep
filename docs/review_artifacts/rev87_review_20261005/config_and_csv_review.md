# Config and CSV full-content review - 2026-10-07

Active role: AUDITOR. Documentary/data inspection, not deployment acceptance.

## Findings and limits

- SHOWN: item-29 strict proposal targets the runtime config, requires bid/ask,
  blocks unknown quotes, caps age at 120 seconds and BTC/USDT spread at 20 bps.
  This supersedes the historical wrong-path proposal. No applied configuration
  or observed order-time cycle follows from the proposal file.
- SHOWN: isolated-account proposal declares USDT, 10,000 starting cash, 7.5 bps
  fees and 5 bps slippage. These are proposed research settings, not account
  provenance, the user's actual capital, measured commission or realised costs.
- SHOWN: archived ES preset still declares ATR stops and risk-based sizing while
  runner exit percentages are zero. Prior accepted exit scope excluded ATR and
  exact next-open behavior. Preserve that distinction; do not infer a new
  approval or silently implement declared fields from this review.
- SHOWN: 24 fee-attribution rows have gross minus scenario fee equal to scenario
  net within 0.0001 rounding, and notional times 50 bps equals scenario fee within
  0.00005 rounding. This verifies table arithmetic only; whether the notional
  incorporates both legs and correct fee assets requires fill-level provenance.
- Candidate recorded net sums to 31.4369, scenario net to 25.4458; both include
  the already-labelled May price outlier (37.3287 recorded net). Do not reopen
  that known contamination as new or interpret the aggregate as positive edge.
  Challenger scenario sums are -4.0954 and -1.0033, also descriptive only.
- SHOWN: supplied dry-run CSV has eight scripted sessions per version and shows
  the intended cooldown contrast. It is supplied simulation output, not an
  independently rerun harness, live behavior or profitability evidence.
- Web README declares relayed candle retrieval and unsaved external references.
  No independent fee endpoint, current PR status or web verification performed.

## Full-read artifact hashes

| SHA256 | Bundle-relative artifact |
| --- | --- |
| `1367f239599864dd7037777c9c283ed9191045a4ad87a2c965f12861cbe24a8e` | `17_item29_proposed_config_NOT_APPLIED/runtime_user_yaml_market_quality_strict.diff` |
| `48e55b8ce3a13fcd99579cb1799b07b7444a97194b75d5a9ba88fa90dc2e888c` | `17_item29_proposed_config_NOT_APPLIED/market_quality_guard_block.yaml` |
| `81accfe4d0acf86d7bcc11c771899c977c3c04893f9093500b073a535e92a1f8` | `19_isolated_laptop_account_PROPOSAL_NOT_APPLIED/user.yaml` |
| `1d10082cc5758a783affe77230637360227b1df872b2e7b0c7ea7e2fe00bdf88` | `4_evidence_sources/web/README_web_sources.txt` |
| `d9cb4fe54e52463f586b7e004e6d5bf037c3a07faaa26bb1dc83b053916db658` | `4_evidence_sources/master_97c24c8e4/configs/strategies/es_daily_trend_v1.yaml` |
| `cc0c46e236f036088ac9a54200d432ac4c1b2f21a751076c78252f0654274c11` | `7_dry_run_on_real_state/dry_run_results.csv` |
| `397f6ecd89b52e1e99263e6a4b9ea41b8b862513127b5dd639c11803ac9c4dc4` | `2_e01_audit/paper_fee_attribution_2026-10-02.csv` |

No executable artifact run, source/config/account/runtime changes, external
calls, publishing or deployment. Arithmetic was recomputed read-only from CSV.

## Additional small-data inspection

Full read of the following four JSON contents, not independent regeneration:

| SHA256 | Bundle-relative artifact |
| --- | --- |
| `53c9f49772d1aba39aa806b4da5d99d5da2ab591ceff5f17a7df1bb82a497321` | `4_evidence_sources/web/coinbase_btc_usdt_daily_2026-05-14_to_05-28.json` |
| `700b0e8ed2b9119afb2922a7ea71887351a6338f8ab074a06a6f2a05e445e82c` | `4_evidence_sources/local_checkout/cbp_state/data/cost_assumptions/cost_assumptions.latest.json` |
| `2c7d9ef0a5689fdf4ca4d9c346fdbe311332e152023202203abf0b28a221f812` | `19_isolated_laptop_account_PROPOSAL_NOT_APPLIED/paper_evidence_campaigns.laptop.isolated_es.json` |
| `5ff87ef6d15d710d56e1629b8505c9544819eb6a5eea5922bc7fb41bbc16b825` | `57_sweep_holdout_and_effect/review_probe_sweep_selection_bias.result.json` |

The 15 relayed daily candles show the declared OHLCV ordering and range; no
external provenance check follows. The isolated campaign is disabled in its
proposal and has its own state path; no launch is authorized. September 2 cost
report explicitly distinguishes paper 7.5 bps, scoring/backtest 10 bps and
dormant lookup 7 bps, warning on mismatches. Its "ok" fields certify configured
numbers, not measured executable costs. The sweep probe supplies selected-data
versus fresh-data contrast, but its execution and statistical validity are not
reproduced by reading the result JSON.

Attempts to print the large SQLite state copy and economic-result arrays were
truncated. Their coverage remains limited to structural checks and separately
documented selected-field arithmetic; they are not upgraded to full reads.

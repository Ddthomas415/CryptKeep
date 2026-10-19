# Corrected research decision - 2026-10-09

## Decision

Continue the existing prospective research. Do not promote these historical
results into capital allocation or a profitability claim. Preserve the frozen
rules and originals; no threshold tuning is justified by this correction run.
This recommendation does not disable or remove any agreed capability.

## What the corrected evidence says

- SHOWN: seven supplied raw archives and 2,377 extracted input files matched
  their supplied checksums. The unarchived CMC per-coin live-history deep-dive
  remains non-reproducible; its computed outputs are not raw input evidence.
- SHOWN: the corrected pump/dip diagnostic retained the original signals.
  All 18 aggregate means are negative after modeled execution costs. Missing
  paths were excluded explicitly, so results describe retained samples only.
- SHOWN: the frozen breakout trade means were positive in the historical later
  sample, but every dependence-aware block interval included zero. They were
  not portfolio returns or independent confirmation.
- SHOWN: the strict continuous-account run stopped on missing May 8 candles.
  Approved public retrieval returned no candles for the five missing hours.
  The separate outage-policy run retained positions and null valuations rather
  than inventing data; it is a different execution assumption, not data repair.
- SHOWN: at 50 bps per side and 0.1% slippage per side, the separate outage
  scenario ended at 1,419.46 (3x) or 1,251.43 (2x), from 1,000 quote dollars.
  Matching BTC ended at 787.85. Dates: November 8, 2025 01:00 UTC to October 8,
  2026 23:00 UTC. These are historical simulated balances, not actual fills.
- SHOWN: later returns on carried equity were +7.83% (3x), -0.42% (2x), and
  +29.00% (BTC). Their starting capital differs. Overall terminal advantage
  must not be described as later-segment outperformance.
- SHOWN: 121 aligned complete UTC days yielded 12 descriptive uncertainty
  bands (six scenarios, 14/28-day blocks); all cross zero. Separate reviewer
  Ohm reproduced all 726 paired daily returns and all bands exactly and returned
  ACCEPTED_WITH_RISK for descriptive uncertainty only.

## What remains unverified

- No fresh holdout, selection-adjusted confidence, or live execution proof.
- No full-period drawdown: each outage curve contains five unknown-NAV hours.
- The daily-return bands omit partial boundary days and final-open liquidation;
  they are not confidence intervals for terminal dollars or compounded return.
- Current saved 50-bps taker fee observation is not proof of historical or
  product-specific fee applicability. The 60/120-bps scenarios remain stress
  tests, not alternative claims about the account's fee tier.
- Fees and slippage are modeled; OHLC bars cannot establish executable depth,
  stop liquidity, intrabar ordering, queue position, or actual fill quality.
- Infrastructure-adjusted economics are not closed by the BTC comparison.
  Operational costs must be charged once to the actual shared research/trading
  setup, not once per overlapping candidate or ignored because trading won.
- Manual scheduled-task collection succeeded; future unattended runs remain
  unverified. The weekly state-rewriting task was not run by this correction.

## Next evidence, without a new strategy search

1. Inspect the next naturally scheduled CMC snapshot and execution record.
   Do not create a duplicate task or treat a manual run as unattended proof.
2. Continue collecting first-appearance membership and retained endpoint quotes
   under the existing frozen logger contract; missing endpoints stay missing.
3. Keep prospective confirmation separate from reused historical diagnostics.
   Review its frozen manifest before any new run or state change.
4. Compare eventual outcomes after the registered sample/end condition, using
   matched costs and benchmarks. Report insufficient power if that is the result.

## Evidence artifacts

- `research/research_corrections_20261009/events_corrected_50bps_v1.json`
- `research/research_corrections_20261009/breakout_corrected_v1.json`
- `research/research_corrections_20261009/breakout_portfolio_v1.json`
- `research/research_corrections_20261009/breakout_portfolio_outage_v1.json`
- `research/research_corrections_20261009/breakout_btc_comparison_v1.json`
- `research/research_corrections_20261009/breakout_segments_v1.json`
- `research/research_corrections_20261009/breakout_uncertainty_v1.json`

Scope: research decision summary only. No production, campaign, scheduler,
account, credentials, capital sizing or frozen strategy changes authorized here.

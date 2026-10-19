# Pre-registration: CryptKeep Composite v1, a trend ensemble with rebalance bands (E8)

Written 2026-10-13, BEFORE running. Research only. It is built from the ranked ingredients in `../crypto_trading_edges_survey_20261013.md`:
- #1 slow trend, using a lookback ensemble;
- #2 volatility scaling;
- cost control through rebalance bands.

The crash brake (E7) was rejected and is not used.

## Rule (PRIMARY, one setting)
- **Assets:** BTC and ETH. Each asset's sleeve is at most 50% of the account. The rest is cash. No leverage, no shorting.
- **Trend score per asset** at a decision close: the average of 4 votes, one per lookback L in {20, 50, 100, 200} days. A vote is 1 if close > close L days earlier, else 0. The score is 0, 0.25, 0.5, 0.75 or 1.
- **Target weight per asset** = 0.5 × score × min(1, 0.50 / annualised 30-day volatility). This is the candidate's own volatility scaling, unchanged.
- **Decisions:** Sunday closes, executed at the next day's open (same timing as the reviewed harness).
- **Rebalance band:** an asset is traded only if |target − current weight| ≥ 0.10 (10 percentage points of the account). It then trades fully to target. Assets inside the band are left untouched.
- **Costs:** fee + 0.05% slippage per side on traded value, via the shared `rebalance()` helper.

## Incumbent and benchmarks (identical execution and costs)
- **Incumbent:** the BTC+ETH 28-day vol-scaled trend candidate, with no band.
- **Benchmarks:** hold BTC; 25% BTC / 25% ETH / 50% cash, weekly; cash.

## Simulator check (required before any result is read)
With the candidate's target and band = 0, the new simulator must reproduce the reviewed harness's daily curve to within 1e-6 USD. Otherwise the run is aborted.

## Data and periods
- **Data:** the hash-checked majors daily files (BTC from 2015-07, ETH from 2016-05). ETH's 200-day lookback is available from Dec 2016.
- **D (development):** first Sunday on or after 2017-01-01 to 2023-12-31.
- **H (holdout):** first Sunday on or after 2024-01-01 to 2026-10-08. Run once in the same execution; nothing is changed after seeing it.

## PASS (all required, at BOTH fee 0.50% and fee 0.90% per side)
1. **D:** Composite Sharpe ≥ incumbent Sharpe, AND composite turnover ≤ 0.75 × incumbent turnover.
2. **H:** Composite Sharpe ≥ incumbent Sharpe − 0.05, AND composite max drawdown ≤ incumbent max drawdown + 2 percentage points.

- **PASS:** Composite v1 replaces the candidate as the strategy to paper-track, after review. No profitability claim.
- **FAIL:** the candidate stays.
- **Always reported:** the result vs BTC and the mixes.

## Sensitivity (reported only; cannot rescue a FAIL)
- Band 0 (ensemble only).
- Band 0.20.
- No vol scaling (weight = 0.5 × score).

## Trial accounting
- One primary and 3 sensitivities, added to the project count.
- A DSR on the composite's D+H daily returns at the 0.50% fee is reported at N = 15 and 120.

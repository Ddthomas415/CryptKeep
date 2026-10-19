# Pre-registration: rebalance band alone on the unchanged trend candidate (E9)

Written 2026-10-13, BEFORE running. Research only.
- **Motivation:** E8 suggested that halving turnover is valuable, and that the failure came from the ensemble signal, not the band.
- **What this tests:** cost reduction only. The signal is unchanged.

## Rule (PRIMARY, one setting)
- **Signal:** the frozen candidate target, exactly. BTC+ETH; per asset, if the 28-day return > 0, weight = 0.5 × min(1, 0.50 / annualised 30-day vol), else 0. Decided at Sunday closes, executed at the next open.
- **Band:** at each decision, an asset is traded only if |target − current weight| ≥ 0.10. It then trades fully to target. Otherwise it is untouched.
  - Exits to 0 and entries from 0 are subject to the same band. A target of 0 is always ≥ 0.10 away from any holding of 0.10 or more.
- **Costs:** fee + 0.05% slippage per side via the shared `rebalance()` helper. Fees 0.50% and 0.90%.
- **Simulator:** `../composite_v1_20261013/composite.py` logic, copied unchanged into `band.py`. It has been verified to reproduce the reviewed harness within 1e-6 USD at band 0, and that check is repeated here.

## Incumbent and benchmarks
- **Incumbent:** the candidate with no band.
- **Benchmarks:** hold BTC; 25/25/50 mix; cash. Same execution and costs.

## Periods
- **D:** first Sunday on or after 2017-01-01 to 2023-12-31.
- **H:** first Sunday on or after 2024-01-01 to 2026-10-08. One run.
- **Caveat:** H is not a true holdout for the candidate signal itself, which was selected on windows that include 2024-26. It is the first look at the band in H.

## PASS (all required, at BOTH 0.50% and 0.90%)
1. **D:** banded Sharpe ≥ incumbent Sharpe, AND banded turnover ≤ 0.75 × incumbent turnover.
2. **H:** banded Sharpe ≥ incumbent Sharpe − 0.05, AND banded max drawdown ≤ incumbent max drawdown + 2 percentage points.

- **PASS:** the band is adopted into the candidate for forward paper tracking, after review.
- **FAIL:** no band.

## Sensitivity (reported only)
- Band 0.05.
- Band 0.20.

## Trial accounting
One primary and 2 sensitivities, added to the project count.

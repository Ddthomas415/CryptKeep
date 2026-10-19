# Pre-registration: funding-rate crash brake on the BTC+ETH trend candidate (E7)

Written 2026-10-13, after a data-quality check of the funding file and BEFORE any funding-vs-price analysis. Research only: no orders, keys, campaigns or tracker changes.

## Data
- **Funding:** Binance USDT-M perpetual funding prints, BTCUSDT from 2019-09-10 and ETHUSDT from 2019-11-27, to 2026-10-13. Every 8 hours, with no gaps, duplicates or errors.
  - Fetched once, read-only, via the operator's Hetzner host.
  - File: `research/crash_brake_20261013/binance_funding_raw.jsonl` (sha256 15edda37d3119f1cdadcbfa8ec10ed938fe359c9dd89e920384471bd167db3a9).
- **Prices:** the hash-checked majors daily files and the reviewed corrected harness (`scripts/research/rerun_frozen_stress.py`).
  - Decide at the Sunday close, trade at the next open, mark at closes.
  - Missing data refused.

## Hypothesis
BIS WP 1087 reports that high crypto carry predicts crashes. Cutting the trend candidate's exposure when perpetual funding is extreme should therefore improve its risk-adjusted return and reduce its drawdown, net of costs.

## Signal (PRIMARY, one setting)
- **Funding level:** for each asset, the 7-day average funding = mean of the last 21 prints with fundingTime strictly before the decision close, annualised (x 3 x 365).
- **Extreme:** this level is at or above the 90th percentile of the same asset's own history, using only prints before the decision (expanding window). At least 365 days of history are required. Before that, no brake applies.
- **Action:** when an asset is "extreme", its candidate target weight is multiplied by 0.5. Otherwise it is unchanged. The brake can only reduce exposure. Everything else is the frozen candidate (28-day trend, 50% vol target, Sunday decisions).

## Comparison and costs
- **Primary comparison:** braked rule vs the unbraked candidate, identical execution.
- **Also reported:** hold BTC; 25% BTC / 25% ETH / 50% cash (weekly); cash.
- **Costs:** fee 0.50% + slippage 0.05% per side (observed taker tier). Repeated at fee 0.90% (reported higher US tier, UNVERIFIED).

## Periods
- **D (development):** first Sunday on or after 2020-12-01 (the BTC brake becomes available) to 2023-12-31.
- **H (holdout):** 2024-01-01 to 2026-10-08. It is run once in the same execution, and nothing is changed after seeing it.
- The ETH brake becomes available about 2020-11-27. Before that, ETH is unbraked.

## PASS (all required, at the 0.50% fee)
1. **D:** the braked rule's Sharpe is higher AND its max drawdown is lower than the candidate's.
2. **H:** the braked rule's Sharpe is not lower than the candidate's by more than 0.05, AND its max drawdown is not higher.
3. **At 0.90%:** conditions 1 and 2 still hold.

- **PASS:** a candidate overlay for forward paper tracking only. No profitability claim.
- **FAIL:** the overlay is rejected.
- **Brake usage:** the number of weeks with the brake on is reported. If the brake is active in fewer than 4 weeks of D, the result is INCONCLUSIVE whatever the numbers.

## Sensitivity (reported only, cannot rescue a FAIL)
- Thresholds at the 80th and 95th percentile.
- Brake to 0 (instead of 0.5).
- BTC funding used for both assets.

## Trial accounting
- One primary setting plus 4 sensitivities. They are added to the project count (about 576 configurations, about 10-15 effective trials so far).
- A DSR on the braked rule's daily returns over D+H is reported at N = 15 and 120, using the broad cross-trial variance from the DSR report.

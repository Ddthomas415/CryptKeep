# Pre-registration: weekly cross-sectional momentum on liquid Coinbase USD coins

Written 2026-10-12, BEFORE any data for this study was downloaded or any result seen. Research only: no orders, no keys, no campaign changes.
Operator instruction: "find me a working edge". Registered under the 90-day plan as E6 (operator-requested).

## Why this hypothesis
The leader-pullback tests (2026-10-12) showed that 1-day top gainers tend to keep falling (short-horizon reversal). The published crypto literature finds the opposite at 1-4 week horizons: momentum. This test checks that pattern on Coinbase, long-only and spot-only.

## Data
Coinbase Exchange public daily candles for every currently listed */USD product, from 2017-01-01 to the last completed UTC day.
- Stablecoins and wrapped or pegged assets are excluded: USDC, USDT, DAI, PYUSD, EURC, GUSD, PAX, USDS, WBTC, CBETH and any product whose base asset name contains "USD".
- **Known bias:** delisted coins are missing. This survivorship bias favours ALL long strategies, including the benchmarks.

## Universe (dynamic, using only past information)
At each weekly decision, the universe is products with:
- at least 90 days of candles;
- rank in the top 20 by median daily USD volume (close × volume) over the trailing 30 days.

## Rule (PRIMARY, one setting)
- **Decision:** at each Sunday 00:00 UTC daily close.
- **Ranking:** rank the universe by 28-day return.
- **Holdings:** hold the top 5, equal weight, considering only coins whose 28-day return is > 0. Unfilled slots are cash.
- **Execution:** trade at the next daily open. Costs are 0.50% fee plus 0.25% slippage per side, on traded value. No leverage, no shorting.

## Benchmarks (same costs)
- (a) Hold BTC.
- (b) Equal-weight universe: all 20, rebalanced weekly.
- (c) The existing BTC+ETH 28-day trend rule (majors primary).

## Periods
- **A:** 2018-01-01 to 2021-12-31.
- **B:** 2022-01-01 to the end.
- **FULL:** both.

## PASS (all required, net of costs)
1. Positive CAGR in both A and B.
2. Higher Sharpe than BTC hold in both A and B.
3. Higher Sharpe than the equal-weight universe in both A and B.
4. FULL-period DSR ≥ 0.90 at N = 15 effective trials, using the broad cross-trial variance from the DSR report. Values at N = 4, 120 and 576 are also reported.

Then:
- **PASS:** a candidate for a frozen forward paper test. It is not proof of profit.
- **FAIL:** reported as evidence against this rule.

## Sensitivity (reported only, cannot rescue a FAIL)
- Lookback 14 and 56 days.
- Top 3 and top 10.
- Universe top 10 and top 40.
- Costs 0.5% and 1.0% per side.

## Outputs
- `xs_momentum_result.json` and `README.md` beside this file.
- Every period, benchmark and sensitivity row is reported, losers included.

## Amendment 1 (2026-10-12, after download, BEFORE any backtest run)
- **Delisted coins:** the download includes 89 delisted USD products that Coinbase still lists, alongside the 403 online ones. This reduces the survivorship bias noted above, but does not remove it.
- **Stopped trading:** a held coin with no later candles stays valued at its last traded close and is sold at that price at the next rebalance. The original text did not specify this.

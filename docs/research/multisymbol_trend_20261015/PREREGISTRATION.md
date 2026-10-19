# Pre-registration E10: slow-trend portfolio across the Coinbase core pairs

Written 2026-10-15, BEFORE running. This is the first experiment under `../MULTI_SYMBOL_MANDATE.md`. Research only.

**Question:** does applying the frozen candidate trend rule to the 10 Coinbase core pairs improve on the BTC+ETH candidate, net of costs, as a portfolio? And how does the rule do on each symbol alone?

## Universe and data
- **Symbols:** the `coinbase_pairs` in `config/candidate_universe.yaml` (fixed in commit 9b241e0d5, long before this study): BTC, ETH, SOL, DOGE, LTC, LINK, AVAX, ADA, XRP, DOT.
- **Data:** Coinbase Exchange public daily candles (downloaded 2026-10-12), copied with SHA-256 sums to `research/multisymbol_trend_20261015/data/`.
- **Known data facts:** XRP has a 904-day gap (the US trading suspension, 2021-01 to 2023-07); the other nine have no gaps. Listing dates differ: SOL, DOGE, ADA, AVAX and DOT list in 2021.

## Rule (frozen candidate, generalized; no new parameters)
- **Decisions:** at each Sunday daily close.
- **Eligible:** a symbol with candles on every one of the last 61 days. N = the number of eligible symbols.
- **Target per eligible symbol:** if the 28-day close return > 0, weight = (1/N) × min(1, 0.50 / annualised 30-day vol), else 0. With N = 2 (BTC, ETH) this is exactly the candidate.
- **Execution:** at the next day's open.
- **Missing candles:**
  - Only symbols with a candle that day are traded.
  - A held symbol with no candle is frozen: not traded, marked at its last close, and held until candles resume. This mirrors the real XRP suspension; no price is filled in for trading.
- **Accounting:** the shared `rebalance()` helper over the tradable sub-account.
- **Costs:** fee 0.50% and 0.90% per side. Slippage is 0.10% per side for EVERY strategy here, including the BTC+ETH incumbent and benchmarks. That is conservative for BTC and ETH; alt spreads are wider.

## Comparisons (same simulator, costs and periods)
- **Incumbent:** the same rule with universe {BTC, ETH}.
- **Benchmarks:**
  - hold BTC;
  - equal-weight hold of the eligible core symbols (1/N each, weekly);
  - cash.

## Periods
- **D:** first Sunday on or after 2019-01-01 to 2023-12-31.
- **H:** first Sunday on or after 2024-01-01 to 2026-10-11. One run; nothing changed after seeing it.

## PRIMARY PASS (portfolio vs incumbent; all required at BOTH fees)
1. **D:** portfolio Sharpe ≥ incumbent Sharpe AND portfolio max drawdown ≤ incumbent max drawdown + 2 points.
2. **H:** portfolio Sharpe ≥ incumbent Sharpe − 0.05 AND portfolio max drawdown ≤ incumbent max drawdown + 2 points.

- **PASS:** a multi-symbol trend portfolio becomes a candidate for forward paper tracking, after review.
- **FAIL:** the BTC+ETH incumbent stays. The result is scoped to this rule, these 10 symbols, these periods and these costs.

## SECONDARY: per-symbol standalone classification (rules fixed now; written to the coverage registry)
- **Standalone rule:** each symbol alone, weight = min(1, 0.50 / vol30) when its 28-day return > 0, otherwise cash. Fee 0.50%, slippage 0.10%.
- **Comparison:** against holding that symbol, from its first eligible Sunday in each period.
- **Classification:**
  - **CANDIDATE** (for further portfolio research only): Sharpe ≥ hold Sharpe AND max drawdown < hold max drawdown, in BOTH D and H.
  - **REJECTED_UNDER_TESTED_CONDITIONS:** Sharpe < hold Sharpe in BOTH D and H.
  - **INCONCLUSIVE:** otherwise, or fewer than 365 days of data in D.
- **Trading:** none of these statuses authorizes trading.

## Sensitivity (reported only; cannot rescue a FAIL)
- Portfolio with a 0.05 rebalance band.
- Portfolio without vol scaling.

## Trial accounting
- 1 portfolio, 10 standalone and 2 sensitivities: 13 trials added to the project count.
- DSR on the portfolio's D+H daily returns (0.50% fee), reported at N = 26 and N = 120 with the broad cross-trial variance.

## Simulator check (required before any result is read)
On the hash-checked majors BTC/ETH files, with fee 0.50% and slippage 0.05%, from Sunday 2020-01-05, the new simulator must reproduce the reviewed harness candidate curve within 1e-6 USD. Otherwise the run aborts.

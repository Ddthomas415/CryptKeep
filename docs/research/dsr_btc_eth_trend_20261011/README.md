# Selection-bias check (Deflated Sharpe Ratio): BTC+ETH 28d trend, 2026-10-11

Scope: only existing saved results. No new backtests, no strategy, config or campaign changes.
Reproduce with `python3 dsr.py` (stdlib only). Output: `dsr_result.json`, which also records the SHA-256 of every input file.

Inputs: `majors_trend_20261009/majors_next_open_v2.json` (daily returns per window, 50 bps fee),
`stress_corrected_v1.json` (105-setting neighbourhood + 13 variants), `hybrid.json` (11 Binance strategies' test Sharpes),
`strategy_search_20261009/search.json` (program-wide configuration count).

## 1. Trial count: total vs effective

| Source (Oct 8-9 program) | Configurations |
|---|---|
| strategy_search altcoin events | 448 |
| Binance hybrid, non-control | 11 |
| majors rules, non-benchmark (primary pre-registered) | 4 |
| top-10 trend rules | 4 |
| recovery / recovery_regime | 16 / 32 |
| CMC proxy | 20 |
| dynamic Coinbase | 8 |
| short_hold | 14 |
| three ideas | 9 |
| **Raw total, approx.** | **~576** |
| Post-selection robustness: 105-setting neighbourhood + 13 one-at-a-time variants | 118 (not selection, but counted in the N=120 case) |

Most of these configurations are highly correlated variants inside a family, so the raw count overstates independent trials.
Cases evaluated, from least to most conservative:

- **N=1**: no selection (this is the plain PSR).
- **N=4**: the rules in the pre-registered majors study.
- **N=10**: one effective trial per strategy family searched.
- **N=15**: the actual selection chain (11 Binance strategies led to this rule family; 4 majors rules).
- **N=120**: chain + the whole neighbourhood grid.
- **N=576**: every configuration treated as independent (an upper bound, not a realistic count).

The best-supported effective count is **10–15**.

## 2. Assumptions

- Formula: Bailey & López de Prado (2014). The return series is daily; Sharpe is annualised x sqrt(365) for display. Kurtosis is raw (normal = 3).
- Return series: the primary pre-registered rule at a 0.50% fee per side (Coinbase taker observed). Windows are concatenated.
- Cross-trial Sharpe variance V (this sets the expected-max hurdle SR0):
  - **narrow** is the Sharpe SD across the 105-setting neighbourhood (0.12/yr).
  - **broad** is the SD across the 11 Binance strategies' test Sharpes (0.411/yr).
  - Both are reported; neither is chosen as "the" answer.
- Window A (2016-07 to 2019) was declared unseen before the majors run, so it is the cleanest out-of-sample slice.
- **Two questions are tested separately:**
  - **absolute:** is the Sharpe above zero?
  - **active vs BTC:** daily strategy return minus BTC buy-and-hold return. Is there an edge over just holding BTC?

## 3. Results (DSR; SR0 is the deflated hurdle)

| Series | Ann. SR | T days | N=1 | N=4 | N=10 | N=15 | N=120 | N=576 |
|---|---|---|---|---|---|---|---|---|
| Full, absolute, narrow V | 1.40 | 3,749 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Full, absolute, broad V | 1.40 | 3,749 | 1.00 | 0.999 | 0.992 | 0.984 | 0.855 | 0.653 |
| Window A (unseen), absolute, narrow | 1.44 | 1,278 | 0.997 | 0.993 | 0.991 | 0.990 | 0.983 | 0.978 |
| Window A (unseen), absolute, broad | 1.44 | 1,278 | 0.997 | 0.971 | 0.932 | 0.910 | 0.758 | 0.621 |
| Window C 2024-26, absolute, narrow | 0.82 | 1,011 | 0.918 | 0.880 | 0.858 | 0.849 | 0.806 | 0.777 |
| Window C 2024-26, absolute, broad | 0.82 | 1,011 | 0.918 | 0.744 | 0.615 | 0.562 | 0.338 | 0.222 |
| **Full, active vs BTC**, narrow / broad | **-0.35** | 3,749 | 0.132 | 0.064 / 0.006 | 0.043 / 0.001 | 0.036 / 0.000 | ~0 | ~0 |
| **Window A, active vs BTC** | **-0.70** | 1,278 | 0.093 | 0.059 / 0.016 | 0.047 / 0.006 | 0.043 / 0.004 | ~0 | ~0 |
| **Window C, active vs BTC** | **-0.21** | 1,011 | 0.364 | 0.288 / 0.143 | 0.254 / 0.077 | 0.241 / 0.059 | 0.19 / 0.02 | 0.17 / 0.01 |

## 4. Interpretation

- **Absolute Sharpe survives selection deflation.** It holds over the full sample and the unseen window A at the realistic N=10-15 under both V assumptions (DSR >= 0.91). It only weakens under the broadest assumption, where every one of ~576 configurations is treated as independent with wide dispersion.
  - But a positive absolute Sharpe largely reflects crypto exposure, which BTC buy-and-hold also has. It is not evidence of skill.
- **There is no evidence of an edge over BTC.** The active Sharpe is negative in every window. Even without any deflation, the probability that the true active Sharpe is above zero is 0.13 (full), 0.09 (window A) and 0.36 (recent).
  - The supported value of the rule is lower drawdown (e.g. 32% vs 53% in 2024-26), not higher return.
- **The recent window (2024-26) is inconclusive.** Its absolute DSR is 0.56-0.85 at N=10-15, and three years is too short to separate a 0.8 Sharpe from luck after selection.
- **Sensitivity:** the conclusions above do not change across N=4...120 or narrow/broad V. Only the strength of the absolute result moves.
- **What the DSR is not:**
  - It is not the probability of making money in future.
  - It corrects the Sharpe estimate for selection only.
  - It does not model execution beyond the 0.50% fee, slippage beyond the backtest, regime change, or the ~$20/month infrastructure cost. At $1,000 capital, that infrastructure cost already turns the rule net-negative (see `strategy_decision_report_20261011.md`).

## 5. Decision

- **Continue the frozen paper test.** The absolute risk-adjusted result is not explained by selection bias, so stopping it is not justified.
- **Edge over BTC: unsupported and rejected as a claim.** The evidence points the other way.
- **Profitability after costs and infrastructure: inconclusive / not claimed.**
- **What the paper test is judged on:** whether it beats a fixed exposure-matched BTC/ETH-plus-cash mix and holds a lower drawdown than BTC. It is not judged on "making money", and it gets no capital increase on the strength of this check.

Proposed next step (needs operator go-ahead): pre-register a maker-vs-taker paper test on the existing weekly BTC+ETH rebalance. That tests whether the 0.25% maker fee is reachable without missed fills, which is the main cost lever.

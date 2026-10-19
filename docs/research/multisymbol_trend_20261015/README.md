# Result: E10 slow-trend portfolio across the 10 Coinbase core pairs (2026-10-15)

**Primary: FAIL.** The incumbent BTC+ETH candidate stays.

- **Pre-registration:** `PREREGISTRATION.md` (83191d18...), written before running.
- **Script:** `ms_trend.py` (550dc2ea...), run once; result `ms_trend_result.json` (a6a4aa09...).
- **Data:** 10 Coinbase daily candle files with SHA-256 sums in `research/multisymbol_trend_20261015/data/`.
- **Simulator check passed:** the reviewed harness was reproduced to 7.3e-12 USD (BTC+ETH, from Sunday 2020-01-05).
- **Costs:** slippage 0.10% per side on every strategy here.

| Fee/side | Period | 10-symbol trend portfolio | BTC+ETH incumbent | Hold BTC | Equal-weight core (hold) |
|---|---|---|---|---|---|
| 0.50% | D 2019-01..2023 | $5,742 (Sharpe 1.20, DD 42.4%, turnover 8.4x) | $11,603 (1.46, 44.8%, 9.2x) | $10,402 (1.04, 76.7%) | $12,798 (1.04, 76.3%) |
| 0.50% | H 2024-01..2026-10 | $1,331 (0.51, 38.9%) | $1,858 (0.88, 32.3%) | $1,892 (0.72, 53.1%) | $1,058 (0.37, 75.4%) |
| 0.90% | D | $4,853 (1.10, 45.1%) | $9,659 (1.37, 46.1%) | $10,361 (1.03, 76.7%) | $12,165 (1.03, 76.3%) |
| 0.90% | H | $1,177 (0.35, 41.5%) | $1,615 (0.71, 34.1%) | $1,885 (0.72, 53.1%) | $1,030 (0.35, 75.6%) |

- **Why it fails:** the portfolio has a lower Sharpe than the incumbent in D and H at both fees, and a deeper drawdown in H.
- **Sensitivity (reported only):** band 0.05 gives Sharpe 1.27 in D and 0.42 in H; no vol scaling gives 1.05 and 0.39. Neither rescues it.
- **DSR (portfolio, D+H, 0.50%):** 0.67 at N=26 and 0.41 at N=120.
- **Frozen holdings:** none occurred. The rule was out of XRP when its suspension began.

## Secondary: per-symbol standalone trend vs holding the same symbol (fee 0.50%, rules fixed in advance)
| Symbol | Classification | D: trend Sharpe vs hold (max DD) | H: trend Sharpe vs hold (max DD) |
|---|---|---|---|
| ETH | CANDIDATE | 1.21 vs 1.06 (50% vs 79%) | 1.00 vs 0.40 (37% vs 68%) |
| AVAX | CANDIDATE | 0.68 vs 0.11 (45% vs 93%), from 2021-12 | 0.30 vs -0.03 (59% vs 90%) |
| DOT | CANDIDATE | 0.10 vs -0.06 (59% vs 93%), from 2021-08 | -0.32 vs -0.33 (67% vs 94%) |
| BTC | INCONCLUSIVE | 1.50 vs 1.04 (40% vs 77%) | 0.51 vs 0.72 (33% vs 53%) |
| SOL | INCONCLUSIVE | 1.08 vs 0.69, from 2021-08 | 0.44 vs 0.49 |
| DOGE | INCONCLUSIVE | -0.03 vs -0.02, from 2021-08 | 0.66 vs 0.49 |
| ADA | INCONCLUSIVE | 0.60 vs 0.07, from 2021-05 | -0.17 vs 0.17 |
| LTC | REJECTED_UNDER_TESTED_CONDITIONS | 0.37 vs 0.61 | 0.15 vs 0.36 |
| LINK | REJECTED_UNDER_TESTED_CONDITIONS | 0.89 vs 1.01, from 2019-09 | 0.33 vs 0.42 |
| XRP | REJECTED_UNDER_TESTED_CONDITIONS | 0.31 vs 0.52, from 2019-04 | 0.62 vs 0.81 |

**"CANDIDATE" here means only that trend beat holding that symbol on both Sharpe and drawdown.** It does not mean profitable: DOT's trend Sharpe in H is -0.32, and AVAX's is 0.30. None of these statuses authorizes trading.

## Reading (scoped to this rule, these 10 symbols, these periods and costs)
- **Spreading the frozen rule evenly across the 10 core pairs diluted the BTC+ETH result.** Weaker symbols took weight from BTC and ETH, and crash correlation limited the diversification. This does NOT show that other symbols or other strategy families cannot add value.
- **Standalone, the trend rule cut drawdowns on every symbol** (by 10-50 percentage points) but rarely improved risk-adjusted return. That is the same pattern as BTC/ETH.
- **Trial count:** 13 trials (1 portfolio, 10 standalone, 2 sensitivities) are added to the project count.
- **Justified next questions:**
  - portfolio weighting other than equal 1/N (e.g. adding a symbol only after its standalone status is CANDIDATE, judged on later data);
  - other families on the untested tier-2 and watchlist symbols;
  - forward tracking of the ETH/AVAX/DOT standalone results.
  Each would need its own pre-registration.

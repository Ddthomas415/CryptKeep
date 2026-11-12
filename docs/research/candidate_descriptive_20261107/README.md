# The BTC+ETH trend candidate, described: regimes, ETH alone, trades, win rate, profit factor

Bot relation: SIGNAL_ONLY (the research harness's weekly target weights, not the bot's runner, which trades differently:
`exit_parity_audit_20261031/`); runtime configuration not applicable.

Research item 7. Claude (Cowork), 2026-11-07. **Descriptive, not a test.**
- No parameter was changed and no variant was run; nothing is promoted or rejected.
- All of this history was examined before, so it is not holdout evidence (`RESEARCH_BRIEF.md` rule 5.8).
- Self-checked; Codex to verify.

**Files:**
- `PLAN.md`: the definitions, written before computing (sha256 `209b4e5e...`).
- `describe.py`: the computation (sha256 `9d64839d...`).
- `results.json`: every number below (sha256 `2665c189...`).

**Reproduce from the repository root:** `mkdir -p D/maj && cp docs/research/majors_trend_20261009/{BTC,ETH}-USD_d1.json D/maj/`,
then `python3 -B docs/research/candidate_descriptive_20261107/describe.py D`. The script refuses to write if
`results.json` already exists.

**Checks, both passed in every period and at both cost levels (SHOWN):**
- The instrumented loop reproduces the reviewed harness's equity curve exactly (maximum difference $0.000000).
- Round-trip P&L plus open positions reconciles to the equity change exactly (residual $0.000000).

The harness's own figures (A $5,555, B $9,920, C $1,780 at 0.50%) match `btc_eth_corrected_comparison_20261012/`.

## 1. The rule against holding BTC or ETH ($1,000 start; 0.50% fee + 0.05% slippage per side, both on every traded dollar)

| Period | Rule: end / worst drop / Sharpe | Hold BTC | Hold ETH alone |
|---|---|---|---|
| A 2016-08 to 2019-12 | $5,555 / 51.9% / 1.49 | $11,782 / 83.8% / 1.30 | $11,728 / 94.0% / 1.19 |
| B 2020 to 2023 | $9,920 / 32.8% / 1.70 | $5,862 / 76.7% / 1.00 | $17,432 / 79.4% / 1.26 |
| C 2024 to 2026-10 | $1,780 / 32.0% / 0.82 | $1,837 / 53.1% / 0.70 | $1,045 / 67.6% / 0.36 |
| FULL 2016-08 to 2026-10 | $102,426 / 51.9% / 1.42 | $134,319 / 83.8% / 1.05 | $225,629 / 94.0% / 1.04 |

At the 1.20% stress cost the rule ends at $4,522, $7,671, $1,383 and $50,448 (A, B, C, FULL). The holds barely change,
because they trade only once.

**Holding ETH alone (SHOWN):**
- It had the highest end value over FULL, but the deepest drop (94%), and it is not consistent: it was the worst of the
  three in 2024-2026 ($1,045).
- At 0.50%, the rule had the highest Sharpe and the smallest drop in every period. It ended above holding BTC only in
  B. At 1.20% its Sharpe falls below holding BTC's in C (0.53 against 0.69).

## 2. Trades and costs (0.50%)

| Period | Days with trades (per year) | Entries / exits / resizes | Turnover (traded $ / average equity, per year) |
|---|---|---|---|
| A | 136 (39.8) | 35 / 35 / 165 | 8.8x |
| B | 152 (38.0) | 40 / 38 / 202 | 9.2x |
| C | 106 (38.3) | 37 / 35 / 117 | 12.8x |
| FULL | 394 (38.7) | 110 / 108 / 486 | 11.3x |

- The rule trades on most Sundays. Most trades are resizes from the weekly volatility sizing, not entries or exits.
- At 0.55% per side (fee plus slippage), FULL turnover of about 11x a year costs roughly 6% of capital a year. That is
  my arithmetic from the table, not a separate measurement.

## 3. Round trips, after costs (BA-39: net, not gross)

A round trip is one asset's holding spell, from entry to exit. Its net P&L includes every fee and slippage paid on that
asset during the spell, resizes included.

| Period | Round trips (BTC / ETH) | Win rate, net | Profit factor, net | Average win / loss | Median spell |
|---|---|---|---|---|---|
| A | 35 (19 / 16) | 34.3% | 1.70 | $922 / -$283 | 28 days |
| B | 38 (19 / 19) | 47.4% | 2.61 | $524 / -$181 | 35 days |
| C | 35 (20 / 15) | 31.4% | 1.49 | $135 / -$42 | 21 days |
| FULL | 108 (58 / 50) | 39.8% | 2.05 | $3,833 / -$1,235 | 28 days |

- At 1.20% the win rates are 34.3%, 42.1%, 28.6% and 37.0%, and the profit factors 1.56, 2.16, 1.15 and 1.69.
- Typical of trend following: most round trips lose, and the winners are about three times the size of the losers.
- Positions still open at a period's end are excluded and listed in `results.json`.
- Dollar sizes grow with the account, so FULL averages are dominated by later, larger trips.

## 4. Market regimes (BTC against its 200-day average, labelled at each Sunday decision; 0.50%; FULL)

| Regime | Weeks | Rule, compounded | Hold BTC | Hold ETH |
|---|---|---|---|---|
| Bull (above a rising average) | 270 | +4,643% | +3,006% | +76,325% |
| Bear (below a falling average) | 144 | +14% | -37% | -72% |
| Mixed | 95 | +59% | +342% | +54% |
| Too little history (2016) | 21 | +29% | +67% | -26% |

**What it shows (SHOWN, descriptive):**
- In bear weeks the rule mostly sat in cash and gained slightly, while both holds lost (over FULL). Its record rests
  mainly on avoiding falls.
- In bull weeks it beat holding BTC over FULL, because it held ETH as well, but trailed holding ETH alone.
- In mixed weeks it trailed holding BTC by a wide margin. That is where whipsaws and trading costs bite.
- By period (`results.json`), mixed weeks favour holding BTC in A, B and C alike. The other two regimes vary:
  - In A, the rule only matched BTC in bear weeks (-16% each) and trailed it in bull weeks (+384% against +496%).
  - In B and C, the rule gained in bear weeks while both holds lost.
  - In C, the rule's bull-week gain (+93%) also beat holding ETH's (+55%).

## 5. Calendar years (0.50%)

| Year | Rule | Hold BTC | Hold ETH |
|---|---|---|---|
| 2016 (from Aug) | +27.7% | +60.0% | -25.5% |
| 2017 | +495.7% | +1,324.2% | +8,984.2% |
| 2018 | -41.0% | -73.4% | -82.4% |
| 2019 | +23.7% | +94.1% | -1.5% |
| 2020 | +233.8% | +304.6% | +473.9% |
| 2021 | +127.7% | +59.4% | +398.3% |
| 2022 | -23.0% | -64.2% | -67.5% |
| 2023 | +69.6% | +155.8% | +90.8% |
| 2024 | +48.9% | +120.8% | +46.0% |
| 2025 | +21.8% | -6.3% | -10.9% |
| 2026 (to Oct 8) | +2.5% | -6.6% | -16.6% |

The rule did better than both holds in every year BTC fell (2018, 2022, 2025, 2026 to date). It gained less than holding
BTC in 6 of the 7 years BTC rose; 2021 is the exception.

## Limits
- Same-history description: it says nothing about future returns, and none of it is a pass or fail against a criterion.
- The current Coinbase fee tier is unverified. Lower fees would raise every rule figure, and higher fees would lower them.
- The regime labels are my own description, chosen in `PLAN.md` before computing. They are not a tested filter, and
  using them to time the rule would be a new, post-hoc idea.
- This is the research harness, not the bot. The bot's runner, on hourly candles with stops and take-profits, trades
  differently.
- At $1,000 of capital, about $240 a year of infrastructure cancels most of the rule's 2024-2026 return
  (`strategy_decision_report_20261011.md`); that is not modelled here.

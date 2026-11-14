# What fee does the BTC+ETH rule need to beat holding BTC? (2026-11-13, Claude)

Research only, exploratory, historical (in-sample). Bot relation: STANDALONE (research harness); runtime trading
configuration not checked. Owner request: real work that advances the project; execution cost is the active focus
(owner direction 2026-11-12, option C).

## How
- `fee_breakeven.py` (written before running): the reviewed corrected harness `scripts/research/rerun_frozen_stress.py`
  on the hash-checked daily inputs used by `btc_eth_corrected_comparison_20261012/compare.py`. The frozen rule is
  unchanged. Only the fee per side varies (0% to 1.20%), with 0.05% slippage per side; every account pays the same costs.
- **Check passed:** at 0.50% the rule, the 25/25/50 mix and hold-BTC end values equal the stored
  `comparison_result.json` in all five periods.
- `maker_scenario.py` was added **after** seeing `result.json`. A maker (limit) order fills at its own price, so this
  scenario uses 0.25% fee with no slippage. 0.25% is the account's observed maker fee
  (`research/coinbase_fee_observation_20261008.json`: maker 0.25%, taker 0.50%, observed 2026-10-08).
- Fee scenarios are not a new strategy setting. No verdict, frozen criterion or tracker is changed.

## Result: $1,000 start, end values

| Period | Rule, taker (0.50% + 0.05%) | Rule, maker (0.25%, every order fills) | Hold BTC | 25/25/50 mix (taker) |
|---|---|---|---|---|
| FULL 2016-08 to 2026-10 | $102,426 | **$138,723** | $134,319 | $34,135 |
| C 2024-01 to 2026-10 | $1,780 | **$1,983** | $1,837 | $1,320 |
| From 2018-01 | $13,434 | $17,664 | $6,027 | $4,023 |
| B 2020 to 2023 | $9,920 | $11,074 | $5,862 | $4,268 |
| A 2016-08 to 2019 | $5,555 | $6,067 | $11,782 | $5,894 |

Worst drawdown, rule maker / taker / hold BTC: FULL 50.2% / 51.9% / 83.8%; C 30.6% / 32.0% / 53.1%.

**Break-even fee per side (with 0.05% slippage) for the rule to match holding BTC's end value:**
- FULL: 0.23%, which is 0.28% all-in.
- C: 0.41%, which is 0.46% all-in.
- A: the rule is behind BTC even at 0%.
- B and from-2018: the rule is ahead at every fee up to 1.20%.

Against the 25/25/50 mix (the frozen Q1 comparator), the rule is ahead at every fee in FULL, B, C and from-2018. In A
it is behind at 0.50%; its break-even there is 0.246%.

## What it means
- **Cost decides the comparison with BTC.** Paying taker fees, the rule ends 24% below holding BTC over ten years. If
  every order filled as maker at the account's 0.25% tier, it would end 3% above BTC over ten years and 8% above in
  2024-26, with 23 to 34 points less worst drawdown than holding BTC.
- **Needed maker fill rate (approximation, linear between the sweep's fee levels).** If a share q of orders fills as
  maker (0.25% all-in) and the rest pays taker (0.55% all-in), the average all-in cost is 0.55% - 0.30% x q.
  - Matching BTC over FULL needs q of about 90%.
  - Matching BTC over C needs q of about 30%.
- **This ignores price movement while a limit order waits,** and any fallback cost above 0.55%. Both lower the real
  benefit. Those are exactly what the E1 maker-versus-taker measurement has to establish. No fill rate is known yet.
- Historical in-sample results across 1,267 or more tried configurations. This is not an edge claim under AGENTS.md
  POP; the deflated Sharpe at the current trial count is unresolved.

## Files
- `fee_breakeven.py`, `result.json`
- `maker_scenario.py`, `maker_scenario_result.json`
- Inputs copied to a scratch folder outside the repo for the harness's `maj/` layout; hashes are checked by the script.

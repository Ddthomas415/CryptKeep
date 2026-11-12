# Descriptive report on the BTC+ETH trend candidate: plan, written before any computation

Bot relation: SIGNAL_ONLY (the research harness's weekly target weights, not the bot's runner); runtime configuration not
applicable.
Research item 7 in `docs/PROJECT_STATE.md`. Started 2026-11-07 on the owner's direction ("find something within your
capacity"), which this plan treats as the approval the item needs.

This is a **descriptive report, not a test.** No parameter is changed, no variant is run and nothing is promoted or
rejected. Every number describes history that has already been examined (`RESEARCH_BRIEF.md` rule 5.8), so none of it
is holdout evidence.

## Inputs (all already in the repository, hash-checked as in `btc_eth_corrected_comparison_20261012/compare.py`)
- `docs/research/majors_trend_20261009/BTC-USD_d1.json` and `ETH-USD_d1.json` (Coinbase daily candles to 2026-10-08).
- The reviewed corrected harness `scripts/research/rerun_frozen_stress.py` (sha256 `1f98513a...`) and its shared
  `rebalance()` from `scripts/research/corrected_research_math.py`.
- The frozen rule: a 28-day trend, sized by 30-day volatility to a 50% target, decided at the Sunday close and traded
  at the next day's open, BTC and ETH, each capped at half the account. Marked at closes.

## Costs
- 0.50% fee plus 0.05% slippage per side (the account's last recorded taker rate; the current tier is unverified).
- 1.20% plus 0.05% (the registered stress level).
- Fees and slippage are charged on every traded dollar, entry included, exactly as in the harness.

## Periods
The registered A (2016-08-01 to 2019-12-31), B (2020-01-01 to 2023-12-31), C (2024-01-01 to 2026-10-08) and FULL
(2016-08-01 to 2026-10-08). Each starts with $1,000.

## Measures, defined now
1. **Reproduction check.** My instrumented loop must reproduce the harness's `run(ns, "rule", ...)` equity curve to
   within $0.01 on every day. If it does not, stop and report; nothing else is computed.
2. **Trades.**
   - A rebalance is a weekly decision that changes holdings.
   - An entry is an asset's weight moving from 0 to above 0; an exit is the reverse; a resize changes a non-zero weight.
   - Report counts per period and per year, plus turnover (traded dollars divided by average equity, per year).
3. **Round trips.**
   - A round trip is one asset's continuous holding spell, from the entry day to the exit day.
   - Its net P&L is that asset's mark-to-market gain over the spell minus every fee and slippage paid on that asset
     during the spell (entry, resizes and exit).
   - Its return is net P&L divided by the dollar value bought at entry.
   - A spell still open at the period's end is reported separately and not counted.
4. **Win rate:** the share of round trips with net P&L above 0, after costs.
   **Profit factor:** the sum of positive net P&L divided by the absolute sum of negative net P&L.
   Also the average win, the average loss and the median spell length in days.
5. **Holding ETH alone.** Buy ETH at the period's first open with the same costs and mark at closes. Reported beside
   holding BTC and the rule, using the harness's statistics function (end value, CAGR, worst drawdown, Sharpe).
6. **Market regimes.**
   - Each week, from one Sunday decision to the next, is labelled by BTC at the decision close, using only data up to
     that day:
     - **bull:** BTC's close is above its 200-day simple average and that average is higher than 20 days earlier;
     - **bear:** the close is below the average and the average is lower than 20 days earlier;
     - **mixed:** otherwise.
   - Weeks before 200 days of history are "insufficient".
   - For each label, report the number of weeks, plus the mean and compounded weekly return of the rule, hold BTC and
     hold ETH.
   - Calendar-year returns are also reported.
7. **Reconciliation:** the sum of the round trips' net P&L, plus the open spells' P&L and the cash effects, must equal
   the rule's total equity change in each period, to within $0.05.

## Not done
- No new parameters, lookbacks, weekdays, assets or costs beyond the two above.
- No statistical significance claims.
- No comparison with runner exits: the bot's runner trades differently (`exit_parity_audit_20261031/`).
- The regime labels are a description chosen now; they are not a tested filter.

# Daily trend: exploratory economic comparison

Date: 2026-09-23. HIGH-risk research arithmetic; no campaign or live changes.
Objective: seek a cost-resilient candidate without retuning toward a positive
answer. Not an untouched holdout, full runner replay or promotion proof.

## Frozen scope and data

Existing `es_daily_trend.compute_signal`, period 200, long/flat only. No regime,
ATR stop, runner exit stack or risk overlay. One hypothesis, no parameter grid.
Compare cash and buy-and-hold on exactly the same evaluation dates.
Read-only `.cbp_state/data/market_raw.sqlite`, Coinbase BTC/USD daily: 3,134
contiguous rows, 2018-01-01 through 2026-07-31. Check finite positive OHLC,
OHLC ordering and exactly one-day spacing. Original collection provenance has
not been independently verified; this is archived-price research.
Evaluation starts 2018-07-20 after 200 prior bars. Prior-close signals execute
at the next bar's open with adverse slippage. No same-close execution.

1,000 USD initial cash, 100 USD notional per entry plus fees, one long at a
time, no leverage/top-ups. Buy-and-hold invests 100 once and holds. Both allow
positions to appreciate: this does NOT enforce a continuous 500 USD market-value
ceiling and is not the proposed pooled multi-campaign account simulation.
Remaining cash earns zero interest. No exchange rounding/minimums modeled.
Fee/slippage scenarios per side fixed before execution: 10/5, 20/10, 60/10 bps.
These are declared sensitivity assumptions, NOT verified account fee tiers.

## Results (USD, entire evaluation period)

| Fee/slippage bps | SMA200 net | Buy-and-hold net | Cash net |
| --- | ---: | ---: | ---: |
| 10/5 | +453.38 | +739.04 | 0.00 |
| 20/10 | +443.17 | +737.26 | 0.00 |
| 60/10 | +416.55 | +733.51 | 0.00 |

Net includes modeled terminal liquidation for any remaining position. At 10/5,
SMA200 closes 31 trades, seven net winners; daily-close account drawdown 21.21%,
versus buy-and-hold 38.42%. Average daily-close account exposure: 7.33% versus
33.08%. These unequal exposures prevent interpreting the return difference as
an exposure-matched alpha estimate. Drawdown excludes intraday extremes and
does not include terminal liquidation as a separate sampled equity point.

SMA200 calendar-year marked-equity changes at 10/5: partial 2018 0.00;
2019 +58.34; 2020 +210.88; 2021 +40.55; 2022 0.00; 2023 +79.53;
2024 +87.18; 2025 -23.09; partial 2026 0.00. These are not independent folds.
Most gains are historical, and this does not establish current profitability.

## Interpretation

Positive under the declared cost stresses, but underperforms buy-and-hold in
absolute dollars while reducing exposure and sampled drawdown. This supports
further investigation of a trend-filter hypothesis, not a live allocation or
claim that the current ES campaign produced these returns. No tested parameter
was changed after seeing the result. No promising period is called untouched.

Reproduce:

```sh
./.venv/bin/python scripts/research/compare_daily_trend_cash.py --archive-db .cbp_state/data/market_raw.sqlite --output /tmp/daily-trend-comparison.json
./.venv/bin/python -m pytest -q tests/test_daily_trend_cash_comparison.py
```

Local artifact: `.cbp_state/data/research/daily_trend_comparison_20260923.json`,
including dataset SHA256, dated trades and daily equity for every arm/scenario.
Ignored artifact is not committed backup. Tests: 3 passed (cost arithmetic,
next-open/no-current-close decision, gap and invalid-cost refusal).
Outstanding: independently review arithmetic, verify original archive lineage,
then evaluate the unchanged hypothesis on a genuinely reserved later dataset
with runner semantics and account constraints explicitly resolved. No automatic
promotion, retirement, restart, routing or risk configuration change.
Acceptance state: READY_FOR_INDEPENDENT_REVIEW.

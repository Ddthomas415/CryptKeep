# SMA200 declared exits vs buy and hold: risk on the same archive - 2026-10-08

Reviewer: Claude (AUDITOR). Research only. Closes the gap named in
`shared_rev88_review_20261007.md` finding 3: the matrix gave buy and hold's return but not
its drawdown. Not promotion evidence; no campaign, state, config or code change.

Same frozen archive (SHA256 `c0d64661...28eb`), costs (7.5 bps fee, 5 bps slippage per
side), warm-up (210 bars) and 1,000 start as `es_exit_policy_matrix_20261007.md`. Both
equity curves are marked at the daily close. Buy and hold buys at the first tradable bar
and pays exit costs at the end. Both runs reproduce the matrix: 9,543.47 and 7,746.36.

| Measure | SMA200, declared exits | Buy and hold |
|---|---:|---:|
| Net return | +854.4% | +674.6% |
| Compound annual return (7.85 years) | 33.3% | 29.8% |
| Maximum drawdown of equity | 64.3% (2021-04-13 to 2023-01-13) | 76.7% (2021-11-08 to 2022-11-21) |
| Longest time below a previous equity peak | 1,050 days | 846 days |
| Annual return / maximum drawdown | 0.52 | 0.39 |
| Annualised daily volatility | 44.5% | 63.0% |
| Mean / standard deviation of daily return, annualised, no risk-free rate | 0.87 | 0.73 |

## Reading

- On this one path the trend rule had a higher return and a lower drawdown than holding,
  with lower volatility, because it was out of the market for about 45% of days.
- It also spent longer under water: almost three years from the April 2021 peak.
- The differences are modest and come from one in-sample path. They do not establish
  risk-matched superiority or an edge. No significance test is claimed.
- "Drawdown" here is the drawdown of the equity curve. It is not the performance policy's
  measure, which is a running sum of per-trade percentage results.

## Files

`es_exit_policy_matrix_20261007/es_buy_and_hold_risk_20261008.py` and `.json`.

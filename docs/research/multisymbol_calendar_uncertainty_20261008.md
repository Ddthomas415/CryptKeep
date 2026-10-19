# Calendar outcomes and exploratory uncertainty

MODELLED, post-result descriptive diagnostics, not live profit or promotion
evidence. All75 outcomes retained:5markets,3strategies and2benchmarks,3fee
scenarios.273 UTC days January1-September30,2026. No tuning or strategy rerun.

## Four positive cumulative arms, base costs

100-notional entries, independent1,000-cash arms,25bpsfee+5bpsslippage per side.
Bands below are pointwise95percentile circular-block diagnostics with14day
blocks,2,000replicates. They are not a forecast interval or post-selection test.

| Arm | Net USDT | Positive months / 9 | Net-profit band | Profit gap vs buy-hold band |
|---|---:|---:|---:|---:|
| ETH breakout | 4.50 | 4 | -53.30 to 67.99 | -44.72 to 83.65 |
| ETH EMA | 33.64 | 4 | -30.57 to 110.18 | -19.22 to 120.11 |
| SOL breakout | 23.06 | 5 | -51.33 to 107.53 | -48.90 to 120.07 |
| SOL EMA | 1.87 | 3 | -77.84 to 85.34 | -67.31 to 89.84 |

None of15strategy arms has a positive net-profit lower bound across all7/14/28
day blocks at base costs. Every base-cost14day paired profit-gap and drawdown-
gap band includes zero. This does not prove absence of edge; it means these
diagnostics do not resolve a positive-profit or benchmark advantage claim.
SOLmean-reversion's net-profit bands lie wholly negative at7and28days but
include zero at14days; do not claim all bands universally include zero.
Its28day paired profit-gap band is also negative (-107.88 to -3.26USDT).
These remain conditional exploratory findings, not multiplicity-adjusted tests.

## Monthly quote changes, base costs

Equity changes, including unrealized position movement until final liquidation.
Terminal fees/slippage belong to September, not an invented October period.
Daily and weekly paths for every arm/scenario are in the raw report.

| Arm | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC breakout | -2.72 | 0.29 | 0.13 | -5.72 | -7.78 | -1.35 | -5.43 | 13.57 | -5.33 |
| BTC EMA | -3.58 | -4.50 | -7.83 | 1.46 | -3.48 | -20.72 | 2.24 | 3.00 | 3.47 |
| BTC mean reversion | -15.48 | -10.80 | -0.61 | 14.18 | -7.15 | -10.42 | 6.43 | 1.64 | -1.11 |
| ETH breakout | 1.59 | -2.43 | 7.10 | -3.73 | -15.77 | -2.01 | 14.54 | 13.00 | -7.79 |
| ETH EMA | 2.29 | -2.87 | -3.30 | -0.05 | -11.22 | -0.62 | 12.31 | 29.20 | 7.91 |
| ETH mean reversion | -21.78 | -15.61 | 7.21 | 13.27 | -5.67 | -20.85 | 7.38 | 0.00 | 0.32 |
| SOL breakout | 5.85 | 8.85 | -18.85 | -9.00 | -1.93 | 6.67 | -4.47 | 29.90 | 6.05 |
| SOL EMA | -7.64 | -12.78 | -11.30 | -5.97 | -6.77 | 8.60 | -2.05 | 32.77 | 7.00 |
| SOL mean reversion | -21.44 | -14.77 | -5.18 | 4.98 | -5.12 | -13.31 | -7.23 | 2.99 | 0.00 |
| ADA breakout | 6.46 | 0.00 | -18.92 | -8.44 | -27.01 | -14.10 | 18.13 | 8.21 | 7.09 |
| ADA EMA | -2.67 | -3.34 | -4.63 | -13.28 | -8.35 | -0.31 | 28.20 | 6.61 | -6.52 |
| ADA mean reversion | -6.70 | -3.79 | -4.28 | 8.11 | -1.47 | -38.30 | 6.24 | 13.44 | 25.90 |
| XRP breakout | 6.45 | -10.03 | -7.80 | -11.98 | -2.76 | -5.48 | -4.07 | 32.83 | 1.93 |
| XRP EMA | 17.28 | -13.38 | 2.33 | -10.07 | 0.41 | -8.30 | 1.96 | -16.70 | 5.71 |
| XRP mean reversion | -13.17 | -9.89 | -2.65 | -0.46 | -0.41 | -11.36 | -4.87 | -0.04 | 0.00 |

Rounded cells may not sum exactly to unrounded totals. Calendar observations
show temporal variation, not its cause: no regulatory/news event attribution
is established by these prices. Most of ETH EMA's positive cumulative result
comes from July-August; it is not evidence of consistent monthly earnings.

## Method and limitations

Daily endpoints use completed-hour closes with final terminal costs replacing
the September30 endpoint. Weekly ISO periods retain partial-week day counts;
monthly totals telescope to the full-period liquidated equity change.
Bootstrap samples paired circular blocks of additive daily equity changes,
same indices for each strategy and same-market/fee fixed100-notional buy-hold.
Seed20261008,reps2000,blocks7/14/28; all sensitivities retained.

This is not reexecution: resampled increments do not enforce the original
trade ordering or reconstruct a feasible strategy path. Stationarity and
regime persistence are unverified. Terminal cost is resampled with its day;
finite-sample percentile bands are uncorrected for the15arms/45costoutcomes and
previous research. Daily-close drawdown is not hourly or intrabar drawdown.
These restrictions prevent promotion, causal or future-profit claims.

Fixed circular blocks with wrapping are described in the primary
[arch documentation](https://arch.readthedocs.io/en/stable/bootstrap/timeseries-bootstraps.html).
The implementation uses NumPy; the reference does not validate our economic
inference assumptions. Actual account fees, L2 execution and shared-capital
scaling remain UNVERIFIED. USD20/month infrastructure remains a shared operator
estimate, not a verified invoice or automatic USDT/USD conversion.

## Proof and next recommendation

SHOWN: isolated targeted tests10passed; separate GATE independently10passed
and ACCEPTED_WITH_RISK for narrow reporting logic. Reporter exited0,5markets,
273days,all75outcomes. Raw report:
research/multisymbol_baseline_v1/calendar_uncertainty_20261008.json.
It records input/source SHA256,seed,NumPyversion and assumptions. Separate
AUDITOR verified all75outcomes,273dailyperiods,39terminal adjustments and225
bootstrap diagnostics; calendar totals reconcile and diagnostics reproduce
exactly. It confirmed the zero-band exceptions stated above. Fullsuite/CI
and live integration not run or claimed. Descriptive ACCEPTED_WITH_RISK only.

Recommendation: do not increase capital or select a live winner from this
study. Next highest-leverage research question is whether a separately frozen
rule has stable net gains beyond a favorable short regime at measured account
costs. Before new selection, resolve the30cycle-window ambiguity and specify
a new prospective confirmation contract, without rewriting this experiment.
Existing broader-universe/5minute/event-aware/funding research remains preserved.

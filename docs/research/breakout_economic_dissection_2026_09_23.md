# Breakout economic dissection and bounded treatment

Closeout addendum (2026-09-23): the isolated comparison implementation was
subsequently independently reviewed with no remaining scoped issues (61
independent tests, 84 broader local tests). Code is preserved on
`codex/breakout-exit-treatment`, implementation commit `909239e48`, closeout
`bc0156090`. The economic experiment is explicitly SHELVED, not validated.
The runner's separate exit stack and signal-transition behavior are not modeled
by this diagnostic; filtered signal exits do not prove equivalent delays in
paper campaigns. This document remains the historical diagnosis, not evidence
of treatment profitability. MCB-1 scope is on `codex/mcb1-scope-contract`.

Active role: AUDITOR. Date: 2026-09-23. Status: INCOMPLETE for profitable-treatment validation.

## Evidence, not a new performance experiment

Read-only analysis of the preserved June 1-August 31 Coinbase BTC/USDT 5m
diagnostic under `.cbp_state/data/research/breakout_economic_20260922/`.
Result SHA256: `9c61d07d02fb05a70284501058f7a4259f64fd80813011beeaa90aab51575407`.
No new parameter search, campaign change, promotion decision, or deployment.
These results describe an ineligible, retrospective, gapped-data diagnostic;
they are neither current account returns nor proof that every breakout fails.

## SHOWN findings

| Per-side fee/slippage (bps) | Terminal return | Closed-trade profit factor |
| --- | ---: | ---: |
| 0 / 0 | -0.1040% | 0.9937 |
| 10 / 5 | -12.1940% | 0.6458 |
| 20 / 10 | -22.8209% | 0.4323 |

Across identical 42 closed-trade timestamps, the arithmetic mean mid-price
entry-to-exit return is 0.013309% (1.3309 bps); median is -0.409072%.
This average is descriptive, not expected future edge or a portfolio return.
Median hold is 11.2083 hours; maximum is 241.3333 hours. At 10/5, recorded
fees total $750.5033 on initial $10,000 and two-sided notional turnover is
75.0503 times initial capital. Approximate round-trip friction is 30 bps.
The final open position is separately marked/liquidated in the original report;
it is not included among the 42 strategy closes. Profit factor uses summed
positive realized PnL divided by absolute summed negative realized PnL.
Buy-and-hold terminal return at 10/5 is +6.3430%, but is not exposure/risk matched.

Entry filters also suppress downside exits in
`services/strategies/breakout_donchian.py`: raw buy/sell is selected first,
then volatility, volume, efficiency and width filters apply to both directions.
Read-only replay of the original signal function, using the stored resolved
parameters and last 300 rows, aligned against the original zero-cost trade
timestamps, found 357 low-volatility and 12 low-volume blocked downside-break
bars while long. Of 42 closed positions, 28 had at least one such bar.
Median elapsed time from first blocked downside break to actual exit among
those 28 is 16.125 hours; maximum is 227.5833 hours. The final open position
also has a blocked downside break. These are repeated bars, not 369 trades.
This proves suppression, NOT incremental losses caused by suppression:
some earlier exits could remove profitable recoveries or add turnover.

The archive has 22,704 of 26,496 expected timestamps: 3,792 absent (14.31%).
Bar-count indicators therefore need not represent fixed elapsed-time windows.
The calculation also uses same-close fills and all-cash sizing, not proven
paper-runner execution/sizing parity. Cost inputs are assumptions, not measured
account fee tiers or realized market impact.

## Research and limits

- Coinbase explicitly warns historical candles may be incomplete and omits
  intervals with no ticks. This establishes a possible legitimate omission,
  not the cause of every gap here. Repeated backfill is not a guaranteed cure.
  https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
- Bailey et al., *The Probability of Backtest Overfitting*, describes the risk
  in selecting the best of many historical trials. It supports recording all
  trials and separating selection from evaluation, not searching this quarter
  repeatedly until profitable. It does not prescribe our proposed exit rule.
  https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf
- Moskowitz, Ooi and Pedersen, *Time Series Momentum* (2012), studies momentum
  in other markets/horizons. It is not validation of this five-minute crypto
  Donchian implementation or evidence that a longer timeframe will cure it.
  https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum

## Treatment recommendation (engineering judgment)

1. Do not expand or promote this configuration on these results. Preserve
   existing governed trials; this review does not authorize stopping them.
2. Qualify the exact intended source and interval before any new economic run.
   Distinguish unavailable data from verified no-trade intervals. No silent
   forward filling or venue/symbol substitution. If exact-source coverage cannot
   be established, stop that experiment, not another retry-until-success loop.
3. Freeze ONE exit-policy comparison: current symmetric filters versus keeping
   entries identical while allowing the existing buffered downside Donchian
   exit without entry-quality filters. No optimized stop, timeframe, channel,
   or volume threshold. This is a hypothesis test, not an approved runtime fix.
4. First pin entry equivalence and intended sell behavior with fixtures; use
   next-available execution timing and consistent sizing/cost assumptions in
   both arms. Keep this quarter diagnostic/training-only. Freeze a disjoint
   evaluation window before inspecting its strategy returns; record prior
   exposure to data and do not call an inspected period untouched.
5. Report paired net return, drawdown, exposure, turnover, per-trade distribution
   and sensitivity to declared costs. Positive aggregate PnL alone is not a
   pass. Require independently reviewed execution parity, eligible inputs,
   positive net evaluation expectancy with uncertainty disclosed, and an
   explicit risk-budget check before considering a separate prospective trial.
   An inconclusive result stays inconclusive; 42 trades do not establish edge.
6. If exit separation fails, retire this variant from the advancement shortlist
   rather than add filters until it looks good. Lower-turnover research would
   be a separately registered hypothesis, not a promised cure. Maker execution,
   more symbols, AI selection, or gate relaxation cannot supply missing gross
   edge by assertion.

Verification: JSON trade-pair arithmetic and read-only signal replay completed
locally with repo Python. No production code changed; no full suite run.
Economic causality, profitable treatment, source completeness and independent
review of this dissection remain UNVERIFIED.

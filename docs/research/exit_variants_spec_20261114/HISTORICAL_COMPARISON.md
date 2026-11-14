# Exit-unblocked variants: historical comparison

Bot relation: BOT_RULES; runtime configuration not checked. Final checked 2026-11-14T17:13:20Z.
Result status: ACCEPTED_WITH_RISK, separate Nash review 2026-11-14T17:12:59Z, historical comparison/reporting only.
Source variants retain their earlier separate acceptance. See `HISTORICAL_REVIEW.md` for review scope and limits.

## Answer

**SHOWN in the saved replay: unblocking SELL filters did not rescue these strategies after costs.** All 60
exit-unblocked symbol/model/cost cases lost quote currency over this period. With signal-only exits, all three
five-symbol totals worsened. With the modeled runner stack, totals improved by only 1.06-2.75 USDT at the primary
fee, and all three remained negative. No variant is recommended for promotion from this evidence.

Figures below are **arithmetic sums of five independent 1,000-USDT sleeves**, each with fixed 100-USDT entries,
not results for one 1,000-dollar account, shared-capital portfolio returns or realized income. Period:
2026-01-01 through 2026-09-30; OKX hourly BTC, ETH, SOL, ADA and XRP; 5/25 project symbols, no change to wider scope.
Primary fee 0.50% per side; stress 0.90%; both add 0.05% adverse-price adjustment per side. These are hypothetical
comparison costs, not measured OKX execution or verified dollar FX. USDT is the actual quote unit.

| Strategy | Arm | Default net, 0.50% | Unblocked net, 0.50% | Change | Default net, 0.90% | Unblocked net, 0.90% |
|---|---|---:|---:|---:|---:|---:|
| Breakout | S: signal only | -171.61 | -190.81 | -19.19 | -420.17 | -445.72 |
| EMA cross | S: signal only | -84.09 | -142.42 | -58.32 | -187.48 | -307.47 |
| Mean reversion | S: signal only | -175.97 | -195.16 | -19.20 | -198.58 | -236.99 |
| Breakout | R: modeled stack | -403.38 | -402.32 | +1.06 | -838.34 | -837.28 |
| EMA cross | R: modeled stack | -166.15 | -163.40 | +2.75 | -329.50 | -328.38 |
| Mean reversion | R: modeled stack | -122.61 | -120.64 | +1.97 | -192.07 | -190.10 |

## Why, and what this corrects

- **Execution costs and changed entry/exit timing:** in S, breakout trades rose 310 to 318, EMA 129 to 206, and
  mean reversion 29 to 53. EMA's before-fee/after-slippage sum improved about 18.77, but fees rose about 77.09,
  making net results 58.32 worse. Mean reversion's before-fee sum improved about 4.83, but fees rose about 24.02.
  Breakout worsened before fees as well. Unchanged BUY signals do not imply unchanged executed entries: earlier
  exits change when the account is flat and can re-enter. This is the full variant contrast, not a same-entry
  counterfactual or a causal attribution to individual exits.
- **Exit implementation:** R already closes many positions via the modeled stop/trailing/TP/time stack. Its trade
  counts are 543 to 543 (breakout), 204 to 206 (EMA), and 87 to 87 (mean reversion). The incremental exit change
  is small under this model; that does not show current live/paper runner equivalence.
- **Per-symbol exceptions matter:** default EMA on ETH in S was positive at both costs; its unblocked S version lost
  0.75 USDT at the primary fee. Unblocking EMA improved BTC from -41.40 to -26.39 in S while worsening ADA from
  -17.82 to -48.99. Do not turn aggregate losses into a universal claim about every symbol or strategy family.
  Full per-symbol results at both costs are in `historical_20261114T1706Z/per_symbol_metrics.csv` (120 rows),
  including fees, trade counts, drawdown, blocked signals, exposure bounds and ending cash.
- **Data/backtest limits and insufficient evidence:** this is reused, exploratory history, not a holdout, registered
  forward result, DSR-qualified edge, regime-general conclusion or profitability proof. No regime or parameter was
  selected after seeing these outcomes. The exact proposed exit-separation hypothesis was tested; alternative
  protective exits, entry rules and all other 20 project symbols were not tested here.
- **Dated correction to the original proposal:** its -15/+28/+65 estimates were already withdrawn for quantity
  accounting error. They are not validated by this replay. The original expectation that EMA/mean reversion would
  improve before fees is not an expectation of net profit: the measured after-cost S contrast is worse. All original
  results and the earlier correction remain intact; no criteria were changed to obtain a pass.

The narrow diagnosis is changed exit/entry timing plus costs, with model/data limits and insufficient forward
evidence. There is no basis to blame one universal cause, reject all entry signals or infer that more safety code
will create an edge. Small R improvements are not meaningful promotion evidence. Future investigations remain
queue proposals, not automatic new backtests.

## What was verified

- One historical process, session54075, finished successfully at 2026-11-14T17:07:49.569813Z; no retry or tuning.
- All five frozen 6,852-row final prefixes matched `dataset.freeze.json`; hourly grid/OHLC/finite values passed.
  The evaluation uses 6,552 bars per symbol after 300 warmup bars.
- Fifteen strategy/symbol cases compared 98,280 execution-relevant historical prefixes. Preserved-before and current
  defaults matched full outputs and raw observer events. BUY signals matched variants. Every raw SELL was returned
  as SELL by variants; zero blocked SELL bars in every unblocked case.
- S default trades reproduced saved timestamps, sides, prices, quantities, individual fees and net PnL at the
  original 0.25% replay-check fee. This check is not the new primary performance fee. No saved trade was rewritten.
- All 120 account/model/cost cases reconciled net PnL to before-fee PnL minus fees using original position quantity.
  Fixed entries remained affordable; the minimum modeled cash across cases was 647.61 USDT. Cash/positions carry
  through the period, with liquidation only at the evaluation end, not intermediate split resets.
- Every recorded input/source pin matched before and after the run; the original SQLite file is opened immutable
  and read-only. Defaults, runner, accepted source artifact and all earlier research files remain unchanged.
- Author synthetic/source run:95 passed in1.05s. Independent pre-run review reused9 synthetic passes and passed
  six ledger-field corruption regressions in0.21s. The reviewer withheld initial acceptance until O168 was fixed.
  Separate final historical review accepted reporting with risks at17:12:59Z:28 pins, five frozen prefixes,
  15 saved S ledgers, all120 cases/5,430 trade-cost CSV rows, metrics export and four selected R price traces checked.
  No strategy-signal replay was repeated by the reviewer; full historical signal parity relies on the pinned
  reviewed harness and retained run gates, not a second independently implemented signal computation.

## Method and limitations

Frozen before outcomes: `replay_contract.json`; script `replay_exit_variants.py`; exact historical helper copy
`legacy_exit_parity_replay.py`. Only five reviewed function definitions are loaded from that copy; its original
top-level experiment is never executed. S uses level entries, signal sells and next opens. R uses signal transitions
and the specified 3% stop/2% trailing/6% take-profit/60-bar stack, with an assumed OHLC path and gap-open fills.
This is not observed order execution: full fills and the path are assumptions, and actual runtime configuration,
forming candles, venue precision, order rejection, queue delay, spread and depth were not established here.

Drawdown is per-sleeve **bar-close mark-to-market plus terminal liquidation fees**, not only realized-trade PnL
and not a full intrabar drawdown. Exposure is bounded by full bar intervals and touched bars; same-bar R trades
can have lower bound zero but nonzero upper bound. Exact intrabar time is unknown. The historical helper's legacy
realized-only drawdown/exposure metrics are not presented as exact account risk. No shared-portfolio drawdown or
Sharpe is inferred by adding independent sleeves.

Trial accounting: three fixed opt-in settings across five symbols and two entry/exit models give 30 descriptive
contrasts, plus two cost views (60 treatment result rows). Replayed defaults are controls; fees are not independent
strategy trials. `trial_additions.csv` records the 30 conservative symbol/model opportunities. The complete/effective
project-wide count is unresolved; no DSR or selection-adjusted significance was calculated or claimed.

Outputs: `historical_20261114T1706Z/exit_variants_result.json` (contract, input/code pins, all cases and parity),
`trades.csv` (every modeled trade at both costs), `per_symbol_metrics.csv` (unrounded case metrics), original
`SHA256SUMS` and separate `METRICS_SHA256SUMS`. Reproduce with the reviewed script and a NEW output directory;
the script refuses to replace an existing one. Reproduction is not automatic authorization for another run.

## Disposition and open questions

Done, independently reviewed within the stated risks: retained historical default parity, both S/R contrasts,
per-symbol/account/cost metrics and auditable trade/output hashes. Engineering item4's source/offline comparison
requirements are complete; economic advantage and operational readiness are not established. No default, paper experiment, trading eligibility,
live permission, R10 status or original commissioning criterion changes. R10 remains STOPPED. No deployment,
service/scheduler/server, credential/account, external-data, backup/cloud, commit/push or memory operation.

Open questions that could overturn broader conclusions: other regimes/symbols, missing execution observations,
current configuration/forming-candle behavior, different approved exit hypotheses, and prospective performance.
They do not invalidate this fixed historical contrast and are not authority to tune or start more work.

What do I know that could change the owner's decision that I have not yet said? All tested unblocked cases lost
money after the stated costs, even though some exits became earlier and some before-fee results improved. These
variants are implemented correctly but have no demonstrated economic advantage or basis for paper/live promotion.

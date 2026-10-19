# Price Moves After Recorded Liquidation Selling

## Primary Result

**SHOWN: a small positive five-minute price association in this snapshot.**
BTC rose after 14 of 17 sampled selling minutes; ETH after 12 of 17.
The mean moves were larger than ordinary five-minute moves over the same
sampled interval. Declines were included, not discarded.

| Spot market | Selling minutes | Rebounds / declines | Mean subsequent 5m move | Unconditioned 5m mean | Difference | Worst 5m move |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| BTC-USDT | 17 | 14 / 3 | +0.165% | +0.054% | +0.111 percentage points | -0.231% |
| ETH-USDT | 17 | 12 / 5 | +0.182% | +0.074% | +0.108 percentage points | -0.329% |

For a 1,000 USDT reference exposure, those mean gross price moves are
approximately +1.65 and +1.82 USDT, NOT realized or executable profit.
No USD/USDT conversion or user-account valuation is assumed.
The five-minute horizon was fixed before calculation, not selected after
comparing the three outcomes. The cutoff was 2026-10-13 02:11 UTC.

## Full Horizon Curve

| Spot market | Horizon | Rebounds / 17 | Mean price move | Unconditioned mean | Increment over unconditioned |
| --- | ---: | ---: | ---: | ---: | ---: |
| BTC | 1m | 8 | +0.042% | +0.010% | +3.17 bps |
| BTC | 5m (primary) | 14 | +0.165% | +0.054% | +11.09 bps |
| BTC | 15m | 12 | +0.206% | +0.164% | +4.20 bps |
| ETH | 1m | 8 | +0.046% | +0.015% | +3.08 bps |
| ETH | 5m (primary) | 12 | +0.182% | +0.074% | +10.81 bps |
| ETH | 15m | 15 | +0.225% | +0.211% | +1.42 bps |

Perpetual-price results, included in the saved artifact, show the same broad
pattern: five-minute BTC +0.171% versus +0.055% unconditioned, ETH +0.183%
versus +0.074%. These are not an independent replication: they are closely
related markets during the same episode.

## Dependence, Drift and What Was Actually Measured

810 individual long/sell records were reduced to 17 UTC selling-minute bins
per asset. Twelve minutes coincide between assets, producing 22 joint minutes,
not 34 independent market episodes. The full snapshot spans only two hours.

A fixed chronological sensitivity retains the earliest observation, then the
next at least 15 minutes later. Only FOUR observations remain per asset.
Their five-minute mean gross moves stay positive: BTC +0.114%, ETH +0.211%,
each with three rebounds and one decline. But their one-minute means are
negative (BTC -0.014%, ETH -0.069%). Even the spaced observations share one
market regime and are not certified independent cases.

Each mark starts at the first minute's open AFTER the recorded selling minute,
then ends at the completed close one/five/fifteen minutes later. Every minute
of the intervening price path must be present and completed. All sampled
selling minutes have mature, complete paths at all three horizons.

The unconditioned comparison covers every minute anchor between the oldest
and newest sampled liquidation minutes, including event minutes. For five
minutes, 120 mature windows and one immature window are retained per asset.
Immature windows are NOT zero returns or recovery failures. The comparison
is descriptive; it is not randomized, matched for prior decline/volatility,
or evidence of what price would have done without liquidations. The window
itself depends on the capped recent-record sample, not a random historical period.

No selling-intensity threshold, cessation-of-selling signal, fitted rule,
position sizing, stop, profit target or portfolio was introduced. Partial
feeds cannot prove that selling ended. This is a post-selling markout, NOT
an exhaustion strategy or a causal-effect estimate.

## Cost References Without Hiding Gross Results

The saved artifact includes one explicitly HIGH-COST HYPOTHETICAL sensitivity:
0.50% fees and 0.25% adverse price adjustment per side. These are NOT verified
OKX fees. At five minutes, mean reference outcomes are -13.26 quote units for
BTC and -13.09 for ETH on a 1,000-unit reference exposure. These numbers do
not reject the mechanism or establish how a lower-cost venue/account performs.

The mathematical break-even fee per side for the average gross five-minute
reference, assuming ZERO adverse price, is about 8.25 bps BTC / 9.10 bps ETH.
Formula: mean_gross / (2 + mean_gross). This uses uniform reference exposure,
not a compounding account. Spread, slippage, latency and missed fills consume
that small budget; this is not a quoted fee tier or a capital recommendation.
No unit-price gains are added up and advertised as portfolio profit.

## Provenance and Verification

The accepted source diagnostic remains unchanged. New source/plan/results:

- `scripts/research/liquidation_markout_diagnostic.py`
- `tests/test_liquidation_markout_diagnostic.py`
- `research/liquidation_markout_plan_20261012.json`
- `research/liquidation_markout_results_20261012.json`

Source SHA256: `42e26d4ebac939285a5b6339a6aacfaed26df45c6a9c299f4c5a2ba6aaa07b98`.
Plan SHA256: `38b14247a4d82160d79d0e2587f170727060299348c8f3a911d02c4f03efa853`.
Results SHA256: `ac0a2a09aed9eb320c2d064bc69639c7656bb5209953b41922aa867e93c12a06`.

All input hashes and the 22 exact public response receipts are verified before
measurement. Source/input bindings are checked before and after calculation.
Bankruptcy prices are never used as entry/reference prices. No new download.

VERIFIED_ENV: local .venv Python 3.12.
`./.venv/bin/python -B -m pytest -q tests/test_liquidation_markout_diagnostic.py tests/test_liquidation_data_probe.py`
returned **14 passed in 0.32s**. Tests cover timing/arithmetic, complete grids,
unknown/immature outcomes, small gross rebounds that lose under modeled costs,
declines, fixed chronological spacing, future-bar invariance, and fee-budget
math. Full suite was not run.

## Disposition

The positive association is worth reporting and separately replicating. Its
small sample and unknown historical publication latency prevent an actionable
edge or profitability claim. No confidence interval, significance test,
holdout, historical listing/coverage certification or live execution proof.

Active stage: separate Newton GATE review; **READY_FOR_INDEPENDENT_REVIEW**.
No account access, orders, trading/campaign/config changes, collector restart
or new automation. A subsequent replication must keep this measurement contract
fixed rather than select new thresholds after seeing these results.

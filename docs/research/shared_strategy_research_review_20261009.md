# Shared strategy research review - 2026-10-09

Active role: AUDITOR. Objective: review all ten supplied workbooks, all four
pasted documents, and the supplied CMC logger claims; advise on profit research.
State: INCOMPLETE for economic acceptance. This is a review, not deployment or
authorization to alter any experiment, collector, campaign, account or schedule.

## Coverage and proof boundaries

Main review plus two read-only reviewer agents inspected the supplied material.
Workbook audit covered all 46 sheets, 32,933 used-dimension cell positions,
24,749 nonempty cells and 533 formulas. Independent formula evaluation found
zero cached-result discrepancies and zero Excel error cells. All sheets visible.
This is arithmetic/document coverage, not a rerun of every historical experiment.

Each workbook below is in /Users/baitus/Downloads/ and ends _2026-10-09.xlsx.

| Workbook prefix | Sheets | Nonempty cells | Formulas | Disposition |
| --- | ---: | ---: | ---: | --- |
| cryptkeep_dynamic_coin_strategy_simulation | 8 | 1807 | 12 | Exploratory; prior-close fills and concentration need qualification |
| cryptkeep_cmc_trending_deepdive | 4 | 3150 | 0 | Historical proxy test, not actual trending-list backtest |
| cryptkeep_top10_trend_preregistered | 4 | 1658 | 0 | Positive recent return but failed relative benchmark; delisting fills optimistic |
| cryptkeep_three_ideas_preregistered | 4 | 2193 | 0 | Selected versions lost; current-listed universe and close fills limit inference |
| cryptkeep_recovery_market_filter_preregistered | 4 | 2332 | 0 | Selected version lost; reduction in dollar loss was 33.4%, not half |
| cryptkeep_recovery_momentum_preregistered | 4 | 1403 | 0 | Selected version lost despite individual winners |
| cryptkeep_btc_eth_trend_preregistered | 3 | 923 | 0 | Original narrow pass superseded by later stress rejection |
| cryptkeep_research_strategies_binance | 4 | 1810 | 0 | Several low-fee variants positive, none beat BTC in reported test |
| cryptkeep_strategy_search | 6 | 7839 | 461 | Candidate statistics need dependence-aware inference and split purging |
| cryptkeep_blast_vara_strategy_check | 5 | 1634 | 60 | Negative aggregate event results; stop-loss worst-case claim invalid |

Pasted documents reviewed:

- attachments/1635242f-9ed0-45d6-a662-dd76a62b0cc0/Pasted text.txt: entire
  1,141-line compilation, including earlier advice and later reconciliations.
- attachments/c5f7783d-7016-42d5-9fe3-05c1ca04ab2d/Pasted text.txt: entire research summary.
- attachments/1edb36e3-806e-4eef-8f7c-1dac71ff36d2/Pasted text.txt: identical copy.
- attachments/85779c9a-19c6-412b-9e3a-0533f3a2a101/Pasted text.txt: identical copy.

The last three have identical SHA256
593cb519036bb7a51ca4a9ac62c14f158922889985d8136023fbd1156a1dea55.
Duplicates were accounted for, not treated as separate supporting evidence.
Attached recommendations were assessed as content, not executed as instructions.

## Findings, ordered by consequence

### P1 - CMC capture does not preserve exit observations for departed coins

SHOWN: cmc_trending_log/cmc_trending_logger.py:57-72 fetches altcoin quotes only
for the current hidden-boost list. There is no persistent cohort of previously
entered coins; only BTC and ETH are always quoted. The header requires exits at
1, 7 and 30 days. A coin leaving the list can lose its required exit observations.
Measuring only coins remaining or returning introduces outcome-dependent missingness.

Recommendation: first repair capture to retain each admitted event's verified
product through all exit horizons, whether or not it remains trending. Missing
quotes must remain missing with reasons, not be excluded silently or replaced by
an arbitrarily distant nearest quote. Preserve the first snapshot and original
plan. Register any amended inference/entry rules as a new version before using
new outcomes; do not silently rewrite the original preregistration.

### P1 - Event-study stops invent executions through price gaps

SHOWN: blast_vara_20261009/events.py:28-39 returns the stop price whenever a later
bar's low crosses it, regardless of that bar's opening price. Read-only probe of
the actual function: entry 100, stop 95, next hourly open 80/high 85/low 75/close
82 returns -5%, although that bar never trades at 95. The actual executable loss
is unknown; the function's loss cap is demonstrably unsupported.

This invalidates Summary!A22's worst-case protection claim, not necessarily the
direction of its already-negative average results. Model gaps conservatively
and include unavailable liquidity; stop-first ordering within a candle is not
sufficient. Main reviewer reproduced the function directly with an AST-isolated
synthetic input; no original script or market artifact was modified.

### P2 - Generic high fees are mislabeled as this account's economics

SHOWN: research/coinbase_fee_observation_20261008.json records a SPOT account
observation at 2026-10-08T23:40:20Z: maker 25 bps, taker 50 bps. Product-specific
all-in fees and historical tiers explicitly remain UNVERIFIED.
The workbooks and logger use 60/120 bps and repeatedly describe them as actual
Coinbase costs. Higher fees are valid conservative stress scenarios, not the
observed account tier. A candle-close or next-open fill does not establish maker
eligibility, queue position or successful maker execution.

Recommendation: keep old results unchanged and labeled by assumed fees. Run
frozen rules under the observed current taker scenario separately, with product
fee applicability qualified. Do not retune rules or call this a fresh holdout.
Do not infer that lower fees guarantee any candidate becomes profitable.

### P2 - Breakout confidence interval assumes independent trades

SHOWN: strategy_search_20261009/candidate.py:31 bootstraps individual trade
returns, although events can recur after 24 hours while holdings last 72 hours,
and assets share market conditions. The per-entry-day grouping at line 33 is not
used in the bootstrap. The reported positive 95% interval is therefore not a
dependence-aware demonstration of edge. Candidate/search classification uses
entry time, without purging training labels whose exits cross the test boundary.

Recommendation: audit actual boundary overlaps, purge crossing training labels,
and use suitable calendar blocks preserving cross-asset dependence. Distinguish
all candidate events from the trades a capacity-limited portfolio can take.
Neither trial count nor one survivor alone proves chance or genuine edge.

### P2 - Known closing price is not a demonstrated attainable fill

SHOWN: dynamic_coin_simulation_20261009/sim.py:1-3 and Book.buy/sell use the last
completed close as the execution reference. majors_trend_20261009/majors.py:39-41
uses current-bar signals and weights against that same closing price. These can
be descriptive close-based models, but do not prove post-signal executability.
The supplied search uses next-open entries, so this is not a claim that every
study has the identical defect. Execution latency, spreads, fill capacity and
maker behavior remain separate proof requirements.

Coinbase documents that candle timestamps are bucket starts and close is the
last trade in the interval, not an executable post-decision quote:
https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles

### P2 - Delisted coverage and liquidation claims are too strong

SHOWN: top10_trend_20261009/top10.py:9 sells a delisted asset at its last close on
a later Sunday; forward filling is implemented at lines 28-30. Historical marks
are not evidence that the venue still accepted a sale at that price.
fetch_bn_all.py discovers symbols from one exchangeInfo response. Inclusion of
BREAK symbols is useful, but does not alone prove every pair ever listed is
present. The absolute claim of eliminated survivorship bias is UNVERIFIED.
CMC missing-exit penalties are also assumptions rather than observed fills.

### P2 - CMC identity and timing need stronger evidence

SHOWN: logger joins CMC and exchanges by uppercase ticker, not verified asset
identity; CMC IDs/platform/address are saved but not used to verify the join.
Actual wrong-asset quotes in the saved logger snapshot remain UNVERIFIED.
Snapshot time is captured before requests; per-response receive times are absent,
and Binance quotes have no timestamp. Sequential observations must not be called
synchronized or executable quotes. Same-minute reruns can overwrite a snapshot.
Add identity verification, response timestamps, validation and append-only writes.

### P2 - Running schedules and immutable forward evidence are not established

SHOWN: one snapshot, 2026-10-09_0347Z.json, has 100 hidden and 100 shown records,
25 Coinbase bid-bearing quotes, 29 Binance bid-bearing quotes, and separate major
quotes. This verifies that saved run, not future daily execution or delivery.
No scheduler record was established; process/scheduler access was not available
to the independent reviewer. The weekly paper state's status is waiting, with
a header-only ledger, appropriate before its intended first Sunday close.

paper_btc_eth_trend_20261009/paper_btc_eth_trend.py refetches history and overwrites
its ledger/state. It is rolling modeled replay, not immutable captured decisions
or actual execution. Its BTC benchmark receives $1,000 of units without entry
costs while the strategy pays costs. The stored plan header alone does not prove
pre-collection registration chronology or prevent later edits.

### P2 - Research conclusions overstate what these tests reject

SHOWN: top-10 Summary!E13 is $1,167.87 from $1,000; it failed its relative
benchmark but did not lose money. Binance research Summary!E9/E12/E14 reports
positive 20.2%, 9.9%, 8.4% at 0.1% fees, contradicting its only-one-positive
sentence. Thus "every altcoin rule lost" is false. Most supplied selected rules
failed, but failure of these particular long-only rules is not evidence against
all altcoin methods, shorts, relative value, funding or adaptive event research.

CMC's historical weekly rank/volume/price proxies are not a historical actual
trending-list test. Failure of the proxy does not settle the forward hypothesis.
Not beating BTC on total return alone does not demonstrate no value under a
different predeclared risk objective. Do not change the original pass/fail bar
retroactively; distinguish failed registered gate from profitable modeled sample.

The later stress test is inspected separately in btc_eth_stress_test_20261009/:
its rejection supersedes the original BTC/ETH workbook's narrow PASS. Its paired
block interval includes zero, so robust timing value is not established. Its
fixed mix uses the strategy's full-period realized average exposure, explicitly
giving hindsight to the comparator. This is a descriptive comparator, not a
deployable allocation selected in advance or proof that timing adds no value.

### P3 - Additional reporting corrections

- Strategy search Summary!B19/B22: 3x and 2x volume portfolios end $1,094.23 and
  $1,237.80, so "behaves the same" is inaccurate. Split is eight/four months,
  not halves. Three passing grid rows represent one family, not one combination.
- Dynamic Summary!A23 omits DIMO's +24% trade recorded in Leaders check!D3.
- Recovery filter reduces dollar loss from $897.32 to $597.23: 33.4%, not half.
- Pasted event scoreboard says 60 days; both event sheets specify a one-year
  October 2025-2026 study.
- CMC Summary!B9's 28/30 symbol flags include nonlisting rows; 25/26 applies to
  the 83 listing rows. The separate later logger has 25/29 quotes. These are not
  interchangeable counts. The 80% positive over 90 days applies to 55 observations,
  not all 100 current entries.

## Recommended treatment order

1. One bounded collector repair first: complete retained cohorts, verified
   identity, timed quotes and append-only artifacts. Tests must prove a coin
   leaving the list still gets horizon observations; failed fetches remain
   visible; same-minute reruns cannot destroy evidence. No trading/config change.
2. Preserve the original studies; publish a corrected evidence summary and
   versioned plan amendments before new scoring. Fix missingness tolerance,
   mature-cohort rules, dependence-aware inference and sample sufficiency.
3. Repair the stop-gap model and common execution/cost contract. Rerun existing
   frozen candidates once at measured-current fee assumptions and stress fees,
   with consistent net-cost cash/BTC/risk comparators. No new parameter search.
4. Continue the existing separately registered Coinbase USD confirmation study
   unchanged (research/coinbase_confirmation_usd_v1/plan.json), preserving its
   carry-forward account, start/end and fee contract. These new files do not
   authorize replacing or restarting it. Activation/operation not checked here.
5. After trustworthy results, choose the next specific profit hypothesis. Do not
   impose a blanket January stop: historical data remain useful for development,
   diagnostics and mechanism work, but not relabeled independent confirmation.

Keep the rejected BTC/ETH weekly replay only if explicitly useful as a cheap
pipeline diagnostic; pausing it is an operator scope decision, not done here.
Ninety days is a minimum calendar condition, not a power guarantee. Seven-day
cohorts must mature before scoring; a full 90-day entry cohort requires another
seven days for its primary endpoint, and 30 days for its longest secondary one.
Earlier matured cohorts can be reported descriptively without early success
declarations. Do not use a far-away nearest quote to hide a missed scheduled day.

At the user's approximately $20 monthly infrastructure figure, annual overhead
is about $240: 24% of a $1,000 account before tax and any other overhead. This is
an economic reporting hurdle, not a promised return or a reason to lever up.

## Validation and remaining uncertainty

SHOWN: workbook arithmetic audit, complete supplied-file coverage, targeted
source inspection, one saved collector run, current saved account fee receipt,
and reproduced synthetic gap-stop defect. Two separate read-only reviewers
assisted; their lanes were workbook/document coverage and collector evidence.

CLAIMED/UNVERIFIED: pre-run chronology, historical/current product-specific fees,
scheduler continuity, actual fill quality, exhaustive historical symbol universe,
economic significance after corrected dependence tests, live/deployed behavior.
No full suite or full strategy reruns: no implementation changed and those runs
would not resolve the source-level issues identified. No original workbook,
collector, campaign, account, credentials or schedule was changed.

Conclusion: useful exploratory research, not proof that profit is impossible and
not sufficient evidence to promote a strategy. Repair the forward measurement
gap first so the next three months do not collect an incomplete experiment.

# Corrected results: lower-value top-100 coins and entrants

## Direct answer

**SHOWN:** the new-top-100-entrant proxy has the strongest average in this
historical screen. Low unit price alone does not establish a reliable advantage.
It is reasonable to keep researching lower-cap and emerging assets; it is not
reasonable to treat these averages as dependable trading income.

**MODELLED**, after assumed 0.50% fee plus 0.25% adverse price each side:

| Basket | Unique coins | Average net dollars per cycle | Median | Worst |
|---|---:|---:|---:|---:|
| Historical top100 below USD1 | 259 | >= +28.43* | >= -48.36* | >= -399.98* |
| Historical ranks51..100 | 352 | >= +16.11* | >= -34.86* | >= -441.57* |
| New top100 entrants | 107 | +129.35 | -1.25 | -528.27 |
| Broad top100 altcoin control | 383 | >= +17.65* | >= -25.96* | >= -420.29* |

Each cycle uses a separate USD1,000 equal-dollar basket, selected from historical
membership, entered seven days later, held four weeks. 100 non-overlapping
cycle windows, first entry2019-01-13, final exit2026-09-13. No continuous-account
or compounded return is claimed. The archive contains414 weekly snapshots
through2026-10-04. V2 evaluates383 unique eligible IDs across all baskets, not
just present-day survivors. BTC/ETH and identified Bitcoin/wrapped instruments
are excluded, not used as the test investments or performance hurdle.

*Unknown exits remain unknown: 9/7/0/11 selections, respectively. Full allocations
are assigned zero recovery solely to bound results from below, not to pretend
they sold at zero. These rows include migrations as well as unavailable prices.
Entry gaps2/1/0/3 leave assigned cash. Bounds are conditional on the CMC prices
and assumed cost model, not lower bounds on actual exchange profitability.

## What matters about the strongest group

- Entrants invested in78 cycles:28 profitable,50 losing;22 cycles stayed cash.
  Funded-cycle median -USD95.46. A large positive mean does not imply frequent
  wins or a predictable monthly payment.
- The HEX-only cycle entered2020-04-05 produces +USD9,254.81 at reference
  prices. Removing this one cycle only as a post-result concentration diagnostic
  reduces the other99-cycle mean to +USD37.17. This is NOT an optimized variant.
- Other large past contributions: ZEC +USD4,115.07 (entry2025-09-14), TFUEL
  +USD1,761.60 (2021-03-07), SEI +USD1,536.70 (2023-12-10), FARTCOIN
  +USD1,368.18 (2025-03-30). These are attribution, not current coin picks or
  proof they were accessible/liquid on the operator's venue.
- Entrant95% calendar-block mean interval: **-USD35.93..+USD376.46**. Against
  the control on90 complete paired cycles: +USD130.29, simultaneous exploratory
  interval **-USD59.89..+USD466.07** across three comparisons. Every comparison
  includes zero. Statistical superiority and executable profitability remain
  **UNVERIFIED**, not disproven for all possible rules.

## Temporal and cost checks

| Basket | Mean dollars,2019..2022 (52cycles) | Mean dollars,2023onward (48cycles) | Mean,1.20% fee stress |
|---|---:|---:|---:|
| Below USD1 | >= +53.41 | >= +1.37 | >= +14.14 |
| Ranks51..100 | >= +41.64 | >= -11.53 | >= +1.99 |
| New entrants | +167.17 | +88.37 | +116.71 |
| Broad control | >= +35.69 | >= -1.89 | >= +3.50 |

Both segments are exploratory reused history, not untouched confirmation.
Recent-period results do not establish cheap-token or lower-cap-basket advantage.
Entrants remain the stronger hypothesis, but both segment intervals cross zero.
Gross averages are +43.97/+31.47/+143.09/+33.02 dollars (bounds where applicable).
Fees are budgeted within the USD1,000, not funded by extra capital.

## Correction and evidence trail

Version1 is preserved in PROTOCOL.md, results.json, README.md, by_asset.csv and
independent_review.md. Its gate was **INCOMPLETE**: truncated tags admitted
wrapped assets. Its numbers must not be silently presented as corrected values.
The review independently reproduced its arithmetic, not its universe validity.

V2 changes instrument classification only, recorded before its calculation in
CORRECTION_V2.md and instrument_correction_v2.json. Remove exactly11 identified
stable/wrapped IDs; preserve raw ranks, prices, dates, weights rule, delay, costs,
missingness and intervals. No rank backfill or outcome-based filter. This
includes losing and winning excluded assets; for example removing RENBTC's
profitable entrant cycle decreases the entrant mean from139.05 to129.35.

The map cites the primary CMC pages actually consulted; the archived ID/slug
matches are checked across all414 snapshots. Shared governance-category tags
do NOT exclude REN, RSR, FXS or MKR. This repairs demonstrated classification
gaps, not every possible historical taxonomy or supply-action error. Prior
tags may also contain hindsight; historical page first-availability remains
unverified. Both versions remain part of research history, not independent
validation. Three hypotheses/one horizon, corrected selection counts3893/4283/
133 and8382control; whole-project effective trial count remains unresolved.

Prices are CMC exchange aggregates, not executable Coinbase quotes. Weekly
history cannot establish intraday timing, order-book capacity, delisted-venue
outcomes, supply-adjustment correctness or actual spread. Current methodology:
[CMC price aggregation](https://support.coinmarketcap.com/hc/en-us/articles/360015968632-How-are-prices-calculated-on-CoinMarketCap).
Unit price alone is not valuation; capitalization also depends on circulating
supply. [CMC market-data methodology](https://support.coinmarketcap.com/hc/en-us/articles/360034116491-Market-Data).
No claim that BTC/ETH have peaked was assumed or tested.

## Verification and recommendation

VERIFIED_ENV focused command:24 passed in1.31s, exit0 (v1 tests, v2 identity
regressions and coverage registry). No full suite or live execution test.

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_low_value_top100.py tests/test_low_value_top100_v2.py tests/test_symbol_coverage_registry.py
./.venv/bin/python -B -m scripts.research.run_low_value_top100_v2 --archive docs/research/raw_archives_20261009/cmc_weekly_and_trending.tar.xz --input-manifest docs/research/raw_archives_20261009/SHA256SUMS_inputs.txt --output /tmp/low_value_top100_v2_replay.json
```

Output paths must be absent; no evidence overwrite. Source component hashes,
classification and protocol are pinned; full input member hashes are in each
result. Full member rows include all winners, losers, cash gaps and unknowns;
by_asset_v2.csv summarizes1,101 arm/ID groups, including unresolved positions.
Independent v2 review is recorded separately, not inferred from parent's tests.
Implementation at first handoff: **READY_FOR_INDEPENDENT_REVIEW**. Separate
GATE Noether subsequently returned **ACCEPTED_WITH_RISK** for the exact v2
modeled calculation: independently matched400cycles,60removed exposures and all
15interval sets; independently24tests passed. See independent_review_v2.md.
No material blocker remains for this bounded calculation; taxonomy, venue,
historical action and forward-validation risks remain. No trading readiness.

Next justified research action: verify the largest entrant events and instrument
history on accessible venues, then test the frozen entrant question with actual
venue liquidity/cost evidence. Do not choose past winners as today's prospects,
retune to improve this result, or return to a BTC/ETH-only universe. No schedules,
services, credentials, accounts, risk limits or trading changed.

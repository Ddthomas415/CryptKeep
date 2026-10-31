# Desk checks T00-1, T10-5, T11-2, T04-1, T04-3 and triage of scout T00 (2026-10-22, Claude Cowork)

Read-only. No code changed, no market data downloaded, no credentials read, nothing committed. Existing on-disk
archives were read in a scratch folder outside the repo. SHOWN = seen in the files or pages named; CLAIMED = a
source says so; UNVERIFIED = not checked. Descriptive checks only: no strategy was tested, so the trial ledger is
unchanged.

## T00-1: how funding intervals are recorded (latent risk, SHOWN in code)
- `services/analytics/crypto_edge_collector.py` line 187 stores `interval_hours` from the collector plan item,
  default 8.0. It is not read from the venue response and not derived from consecutive funding times.
- The plan in use, `sample_data/crypto_edges/live_collector_plan.json`, lists one funding row: OKX
  `BTC/USDT:USDT` at 8.0.
- `services/strategies/funding_extreme.py` lines 15-30 compare the per-print rate in percent
  (`crypto_edge_context.py` line 164: `rate * 100`) with fixed thresholds (`presets.py` lines 299-300: 0.05 and
  -0.01). The interval is not used to normalise the rate. `crypto_edges.summarize_funding_carry` (lines 17-23)
  applies one interval to all rows.
- `_extract_funding_rate` (collector lines 81-95) falls back to `nextFundingRate` when `fundingRate` is absent,
  so a predicted rate could be stored as if it were the current one.
- A second path already uses altcoin funding with the same flaw: `services/market_data/alternative_data.py`
  `get_funding_rates()` (lines 56-101) reads Binance USDT-M `fundingRate`, applies the same per-print 0.05/-0.01
  thresholds, annualises with a fixed `rate * 3 * 365` (line 89) and ignores the interval.
  `market_intelligence.py` line 150 calls it, `rotation_engine.py` lines 56-58 pass BTC, ETH, SOL, AVAX and LINK
  futures, and `composite_ranker.py` (lines 80-116) turns the result into a ranking bonus or penalty. Users:
  `selector_backtest.py`, `historical_selector_backtest.py` and dashboard pages 38, 42 and 43 (43 writes
  execution plans). No caller in the live order path was found (independent review's grep).
- Effect: for the OKX BTC collector row, probably none (the scout's "BTC/ETH largely excluded" comes from Bybit's
  rules; for OKX BTC it is UNVERIFIED). For the altcoin path above, any contract on a 1-4 hour interval is
  scored against 8-hour thresholds and annualised as if paid 3 times a day, so crowding is understated and
  annualised rates are wrong by up to 8x. The scout CLAIMS about 40% of Binance USDT-M contracts were not on
  8-hour funding in Nov 2025.
- Fix (Codex's code, needs approval): store the funding timestamps or ccxt's interval with each rate (stored
  rows have none today), derive the interval from them, normalise to a per-8-hour rate before any threshold,
  drop the fixed x3/day annualisation, and record which field supplied the rate. Scope: the collector,
  `alternative_data.py` and the composite ranker.
- Research rule (from T00-1): funding rates are compared per stated interval only; never annualise altcoin
  funding at 3 prints a day; applying today's interval to past prints is look-ahead.

## T10-5: recently delisted Coinbase coins in saved universes (no live exposure found, SHOWN)
- Coinbase product snapshot `research/coinbase_listing_probe_20261019/01_products.json` (842 products): BADGER,
  IOTX, STORJ and GYEN USD markets are `delisted` with `trading_disabled` true; BLAST-USD was still `online` on
  2026-10-19 (the scout says trading ended 2026-10-20; CLAIMED).
- None of the five tickers appears in `config/` (except `user.yaml`, which was not read) or in the multi-symbol
  mandate. The live scanner keeps only `active` markets (`coinbase_movers.py` line 24), so delisted products
  drop out automatically.
- They appear only in research files: the ENTR-CB-1 listing candles (STORJ daily candles end 2026-09-28, IOTX
  2026-09-23, matching the suspension dates the scout gives), the 2026-10-09 BLAST studies, and the raw Coinbase
  product list inside the CMC trending logger's snapshots (not its tracked list).
- ENTR-CB-1 host: STORJ last selected 2021-03-28, IOTX 2022-05-22, EOS 2025-05-18, all before their delistings
  (EOS: Nov 2025, CLAIMED by the scout).

## T11-2: saved Coinbase candles around the two outages (descriptive, SHOWN)
- Data: hourly Coinbase candles for 395 USD products, 2025-10-09 to 2026-08-09
  (`docs/research/raw_archives_20261009/coinbase_hourly_prior10m.tar.xz`, extracted outside the repo).
  Coinbase's candle API leaves out intervals with no trades (its documented behaviour, not re-checked here), so
  a missing candle is read as no trades that hour.
- Definitions fixed before counting: window A = 2025-10-20 00:00-23:00 UTC (24 hours), control = 2025-10-13;
  window B = 2026-05-07 23:00 to 2026-05-08 07:00 UTC (9 hours), control = the same hours a week earlier;
  products counted if they traded in the 7 days before and after the window.
- Results:
  - AWS outage, 2025-10-20: BTC and ETH missed no hours; the average product missed 1.39 of 24 hours (control
    0.53; each window uses its own eligible set). 07:00-09:59 UTC was thin (about 255-270 products with a candle
    against about 290 normally), but there is no sign of a matching-engine halt.
  - Matching-engine halt, 2026-05-08: none of the 395 products in the archive has a trade from 02:00 to
    06:59 UTC (5 hours), BTC and ETH included; of the 373 eligible products, 3 missed all 9 window hours. The average product missed 5.73 of 9 hours (control 0.93). Trading was thin in the
    01:00 hour (BTC volume 13.8 against 92 the hour before) and resumed in the 07:00 hour.
  - The move from the last close before the gap (01:00) to the first close after (07:00): median 0.59% across
    370 products, 90th percentile 2.99% (value at rank 0.9n; 2.97% interpolated). The same hours one and two weeks earlier: median 0.73% and 0.84%,
    90th percentile 3.69% and 4.22%. So this halt caused no unusual reopening jump. Close to open across the gap:
    BTC 79,593.10 to 79,590.67; ETH 2,282.06 to 2,282.06. One event only.
  - Timing conflict: Coinbase's own statement, as quoted by FX News Group, says "At 7:48 PM ET... nearly all
    trading on Coinbase halted" (23:48 UTC on May 7), with cancel-only at 2:25 AM and full trading at 3:49 AM ET.
    The saved Exchange API candles instead show BTC trading through the 00:00 and 01:00 UTC hours (volume 92 and
    13.8) and no trades only from 02:00 to 06:59 UTC. The Block's "21:00 ET" refers to delayed sends and receives
    on two networks, not trading, so it does not settle this. The postmortem page could not be opened, so which
    venue or channel the 7:48 PM time refers to is UNVERIFIED.
- Effect: daily candles do not show the halt at all (BTC/USD daily bars exist for 2026-05-07 and 05-08 in
  `market_raw.sqlite`; the 05-08 volume is 44% of 05-07's). Hourly research needs an explicit halt rule; the
  stress-case rule (no fills while halted) is supported, and this one event did not produce a reopening gap.

## T04-1: the CTREND paper's long leg (SHOWN from the open-access JFQA article and working paper)
- Fieberg, Liedtke, Poddig, Walker, Zaremba, JFQA 60(7), 2025, open access (CC BY 4.0). CoinMarketCap data,
  April 2015 to May 2022, coins above USD 1m market cap, returns truncated at 0.5%/99.5%, delisting handling not
  described. 28 price and volume signals (RSI, stochastics, SMAs of 3-200 days, MACD, volume SMAs, Bollinger,
  CCI, Chaikin) combined weekly by a cross-sectional elastic net over a 52-week rolling window; value-weighted
  quintiles, weekly rebalance.
- Weekly returns by quintile (Table 3): low 0.12%, then 0.93%, 1.12%, 2.72%, high 3.98%; high minus low 3.87%
  (t = 5.19). Against the market the high quintile's CAPM alpha is 2.11% a week (t = 3.49, beta 1.01) and the
  low quintile's is -1.70%. Against the 3-factor model with momentum (LTW) the high quintile's alpha falls to
  1.10% (t = 1.94, not significant at 5%) with a momentum loading of 0.52 (t = 10.75), while the low quintile's
  is -1.51%. The market factor averaged 1.89% a week (supplement Table B.2), and CTREND correlates 0.61 with
  momentum. So in raw returns the long leg dominates, but after adjusting for the market and momentum the short
  leg contributes more, and the long leg's edge is largely momentum.
- Top 100 coins (Table 8): low 0.39%, high 3.79%, spread 3.39% (t = 4.49). Largest 10%: high 2.44%.
- Second half of the sample (Nov 2018 to May 2022, Table 5): low -0.72%, high 2.55%, spread 3.26% (t = 4.25).
- Costs (Table 9): the long-short factor turns over 68.46% a week (break-even cost 1.41%, significance lost at
  0.88%); the high quintile alone turns over 62.84% (top 100: 66.74%), with break-even 3.17% (top 100: 2.83%)
  and significance lost at 1.86% (top 100: 1.56%). The paper assumes 30 bp per long-side trade. Nothing after
  May 2022.
- Cost at the repo's standard 0.50% fee plus 0.25% slippage per side, using the paper's convention (2 x turnover
  x cost): about 0.94-1.00% a week for the long leg; about 1.45-1.54% a week at a 0.90% fee.
- Repo counter-evidence: E6 (weekly momentum, Coinbase, 2018-2026) failed; in 2022-26 its top-5 basket turned
  $1,000 into $133, and an equal-weight top-20 basket (BTC and ETH included) ended at $219
  (`xs_momentum_20261012/README.md`, whose stored result still carries a known stale-price defect). Because
  CTREND's long-leg edge is largely momentum, E6's failure bears on it directly.
- What it suggests: an exploratory, out-of-sample-for-the-paper replication on June 2022 to October 2026. Coinbase
  daily candles for 492 USD markets to 2026-10-11 are archived
  (`cryptkeep_data_archive/xs_momentum_20261012_candles_v1`; its PROVENANCE.md warns the downloader may have missed
  windows, and products Coinbase removed from its list are absent) and weekly caps are in the CMC archive. Both
  were already used (E6, VOLFC-1, ENTR-CB-1), and moving the recipe to a Coinbase universe needs many choices that
  must be frozen first, so it is exploratory at best. Needs your approval before any data is touched.

## T04-3: the low-volatility paper (not reachable)
- Pyo and Jang, Finance Research Letters 97 (2026): the full text is on ScienceDirect, which these tools cannot
  open, and ResearchGate returned an error. Nothing was read beyond the scout's summary. If you have access,
  the PDF would settle it.
- Related open evidence: Kaya and Mostowfi (FRL 2022) find long low-volatility portfolios of 35 large coins earn
  positive returns in January 2017 to June 2021 (for example 9.7% a month, t = 1.93, for 3 coins with 12-month
  windows), with costs included but no market benchmark and no post-2021 data. Its universe is coins above USD
  1bn at 2017-01-01 that traded since 2016 (the authors say this limits survivorship; not checked). It does not
  change LOWVOL-1.

## Triage of scout T00 (funding, basis, open interest, liquidations; 10 leads)
- Desk checks (3): T00-1 (done above; it also yields a research rule and a code follow-up, both in its section), T00-3 (read the Cao et al. basis paper before any spot translation),
  T00-9 (whether Coinbase publishes settlement or funding files for its US perp-style futures).
- Research rule (1): T00-8. Liquidation feeds are lower bounds (Binance pushes one liquidation per symbol per
  second; ADL never appears), so any liquidation input is an event flag, not a summed volume.
- Needs your approval (1): T00-4 (a forward-only altcoin open-interest concentration flag).
- Notes (5): T00-5 (funding carry needs a short perp, outside a long-only spot mandate), T00-2, T00-6 and
  T00-7 (evidence against altcoin carry, against funding as a crowding signal once delisted coins are included,
  and against short-horizon funding signals and cross-venue arbitrage; cite before any `funding_extreme`
  promotion), T00-10 (ADL tail risk for carry).
- No ranking change from T00.

## Independent review (2026-10-22, separate agent, read-only)
Verdict on the first version: REJECTED as written, because T04-1 said the paper reports no market comparison or
long-leg turnover when Tables 3 and 9 and supplement Table B.2 do, and that changes the conclusion (the long
leg's edge is largely momentum). Also corrected: the Table 5 sign (-0.72), the T00-1 scope (the
`alternative_data.py` altcoin path), the source of the BTC/ETH exclusion, the fix's prerequisites, The Block
citation (sends and receives, not trading) and Coinbase's own 7:48 PM ET statement, the product counts, the
90th-percentile method, the Kaya and Mostowfi universe wording, and the T00-2 note. The reviewer recomputed every
T11-2 figure independently and confirmed T10-5 and T04-3. With these corrections: ACCEPTED_WITH_RISK.

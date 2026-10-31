# CTREND-OOS: out-of-sample replication of the CTREND trend factor on Coinbase (DRAFT r2, NOT FROZEN)

Status: draft r2, 2026-10-22, Claude Cowork. Revised after one independent review (r1 REJECTED for freezing: two
look-ahead items, an unfixed candidate series and open elastic-net choices; all addressed below; see section 12).
Not frozen, not approved, nothing run, no data opened for this study. A second independent review is required
before any freeze.

Authorisation: nothing in this document is authorised. Approval (1) below covers writing the code and tests; no
code exists yet. Approval (1) also needs the operator's answer on `RESEARCH_BRIEF.md` section 6 (new comparisons
wait until the research path is usable; "No experiment is authorized by this brief"). Freezing = operator
approval + independent review + a work-log entry with the SHA256 of this file and the code.

## 1. Question
Did the published CTREND recipe's top quintile beat a value-weighted market of the same Coinbase universe, after
Coinbase costs, over the test window in section 3, which starts after the paper's data end (May 2022)?

Source: Fieberg, Liedtke, Poddig, Walker, Zaremba, "A Trend Factor for the Cross Section of Cryptocurrency
Returns", JFQA 60(7), 3116-3153 (2025), open access, DOI 10.1017/S0022109024000747, and its online supplement.
Paper results that motivate this (SHOWN): top quintile 3.98% a week raw, CAPM alpha 2.11% (t = 3.49), alpha
against the 3-factor model with momentum 1.10% (t = 1.94), momentum loading 0.52; long-leg turnover 62.84% a week
(66.74% in the top 100). Repo counter-evidence: E6 weekly momentum FAIL (`../xs_momentum_20261012/`).

Label: EXPLORATORY. The window is post-sample for the paper, not pre-publication (the paper was accepted in 2024).
Both data sets were already used by other studies (rule 8). Porting to Coinbase needs the choices in section 4,
all fixed here before any data is opened. A PASS is not evidence of profit; at most it qualifies a separately
approved forward paper track.

## 2. Data (existing archives only; no download, no new API requests)
- Prices and volume: Coinbase Exchange daily candles, 492 USD products (403 online, 89 delisted but still listed
  at fetch), 2017-01-01 to 2026-10-11 (`cryptkeep_data_archive/xs_momentum_20261012_candles_v1/`; PACKAGE.SHA256
  d71001f6...; SHA256SUMS must verify). Rows are (t, low, high, open, close, volume) in base units, as parsed by
  `xs_momentum.py` lines 20-21; dollar volume = close x volume. The code unit-tests this column order. Used before
  by E6 and VOLFC-1.
- Market caps: CoinMarketCap weekly top-1000 snapshots, 2018-11-04 to 2026-10-04, dated Sundays (414 files;
  `raw_archives_20261009/cmc_weekly_and_trending.tar.xz`). Used before by CMC_PROXY, LOW_VALUE_TOP100 and
  ENTR-CB-1.
- Candidate benchmark: Coinbase BTC-USD and ETH-USD daily candles (`raw_archives_20261009/coinbase_btc_eth_daily.tar.xz`,
  D_CB_MAJ, to 2026-10-09).
- Listing cross-check: `research/coinbase_listing_stepB_20261019/listings_v2/listings.json` (fetched separately
  on 2026-10-19).
- Identity (Coinbase product to CMC ID): extends `../coinbase_tradable_entrants_20261019/identity_map_v3/`
  (383 CMC IDs) using saved data only: exact name and slug matches, contract checks only where a saved CMC
  contract record exists, written adjudication of every non-exact case, and valid-from/valid-to dates for
  migrations (e.g. MATIC to POL). No new CMC requests. Ambiguous products are excluded and counted. The map is
  built from today's product list and does not vary over time; the pipeline never reads Coinbase status-at-fetch.
- Exclusions, fixed as a product-level list written before freeze (E6's `xs_momentum.py` line 7 is the
  precedent): stablecoins (the paper's only exclusion); also wrapped, tokenized and liquid-staking-derivative
  assets (an added porting choice, D10), including the 11 IDs removed in `../low_value_top100_20261018/CORRECTION_V2.md`.
  Archived CMC tags are not used for this, because the fetcher kept only the first 12 tags.

## 3. Timing
- Signal time: the Sunday daily close (UTC). Everything used for eligibility, ranks and weights is known by then.
- Portfolio: entry at the Monday daily open (the first trade of the UTC day), exit at the next Monday's open.
  Holding return = next Monday open / this Monday open - 1.
- Estimation returns: Sunday close to Sunday close, so the last window week ends at the signal time.
- Caps: the CMC snapshot dated the signal Sunday (the fetcher requested `date=<Sunday>`; whether it reflects the
  start or end of Sunday, it predates the Monday open). For estimation week s, caps and indicators come from that
  week's starting Sunday.
- Test entries: every Monday from 2022-06-06 to 2026-09-28 (226 weeks; last exit 2026-10-05), unless the Phase 0
  regression-week gate moves the start (section 7c).
- Estimation: a fixed rolling window of the 52 weeks before each test week; with the 210-day indicator buffer the
  earliest data used is about November 2020.

## 4. Recipe and porting choices (all fixed here)
Paper recipe (section III and supplement Appendix A), with standard indicator definitions (D9):
1. 28 indicators from daily data through the signal Sunday:
   - momentum oscillators: rsi (14 days, Wilder smoothing); stochK (14 days) and stochD (3-day SMA of stochK);
     stochRSI (14 days over rsi); cci (20 days, constant 0.015);
   - price SMAs of 3, 5, 10, 20, 50, 100 and 200 days, each divided by the signal-Sunday close; macd = (EMA12 -
     EMA26) / EMA12 of closes; macd_diff_signal = macd minus its 9-day EMA;
   - dollar-volume SMAs of 3-200 days, each divided by the signal-Sunday dollar volume; volmacd and
     volmacd_diff_signal as for macd on dollar volume; chaikin money flow (21 days; a day with high = low has money
     flow 0);
   - Bollinger: middle = 20-day SMA of closes, lower and upper = middle -/+ 2 standard deviations (population,
     ddof = 0), each divided by the close; boll_width = (upper - lower) / middle.
   - Helpers: SMA = mean of the last L values including the current day; EMA with alpha = 2/(L+1), seeded by the
     SMA of the first L values of the 210-day buffer.
2. Each week, each indicator becomes (rank - 1)/(N - 1) - 0.5 over that week's eligible set, average ranks for
   ties.
3. Univariate stage, for each indicator j and each week s in the 52-week window: cross-sectional regression of
   week s's estimation return on the ranked indicator at the start of week s, by cap-weighted least squares with
   week-s caps normalised to sum to 1; coefficients averaged over the window (M = 52 = the window). Fitted forecast
   for coin i in week s: the window-average intercept plus slope times its ranked indicator (D5).
4. Elastic-net stage: one pooled regression over all coin-weeks in the window of the cross-sectionally demeaned
   return (cap-weighted weekly mean subtracted; paper footnote 14) on the 28 fitted forecasts, each forecast
   standardised to unit cap-weighted variance over the window. Weights: each week's caps normalised to sum to 1,
   then rescaled so all weights sum to the number of coin-weeks. Elastic net with L1 ratio 0.5 and an intercept,
   fitted unconstrained (scikit-learn `ElasticNet`, version pinned at freeze). Penalty: 100 values log-spaced from
   the smallest penalty that sets every weight to 0 down to 1e-4 of it; chosen by corrected AIC = n ln(RSS_w/n) +
   2k + 2k(k+1)/(n-k-1), with n = coin-weeks, RSS_w the weighted residual sum of squares and k = non-zero weights
   plus 1. Forecasts with a positive weight are kept.
5. CTREND for the test week = the equal average of the kept forecasts, each built from the window-average
   coefficients and the coin's ranked indicators at the signal Sunday. If none is kept, all 28 are averaged; the
   number of such weeks is reported.
6. Rank eligible coins on CTREND; hold the top floor(N/5), ties broken by the lower CMC ID, value-weighted by
   signal-Sunday caps (uncapped, as in the paper).

Porting choices (deviations from the paper):
- D1 Universe at signal Sunday d: Coinbase USD product mapped to a CMC ID that is in that Sunday's top-1000
  snapshot (the archive's binding floor is CMC rank 1,000, not USD 1m), cap not above BTC's; at least 200 daily
  candles in the 210 days to d, including a candle on d; not on the exclusion list; no internal data gap inside the
  210-day lookback. BTC and ETH are included. No condition uses anything after d.
- D2 Prices and dollar volume from Coinbase candles, not CMC's aggregated volume.
- D3 Truncation: within each estimation window, coin-weeks whose estimation return lies outside the window's
  pooled 0.5th-99.5th percentiles are dropped from the regressions. Never applied to portfolio returns. (The paper
  truncated its whole sample, portfolio returns included.)
- D4 Raw returns in the regressions. In the pooled stage a common risk-free rate would also be removed by the
  weekly demeaning; this differs from the paper's excess returns only negligibly.
- D5 The elastic-net inputs are in-window fitted forecasts. Basis: "parameters are estimated using a fixed rolling
  window of 52 weeks ... used to predict returns for the following week" and "we perform parameter estimation and
  forecast selection using in-sample data". An alternative reading (one-step-ahead forecasts from earlier windows,
  as in the method's sources) is not tested here; it would need data from about November 2019.
- D8 A coin lacking any of the 28 indicators, or with a zero denominator in stochK, stochRSI or cci, is not
  eligible that week.
- D9 Standard indicator definitions instead of the supplement's printed helpers, whose SMA divides L+1 values by
  L-1 and whose EMA uses alpha = 1/(1+L) and is seeded from a price even for volume; the supplement itself says it
  uses standard textbook definitions.
- D10 Extra exclusions (wrapped, tokenized, liquid staking) beyond the paper's stablecoins.

## 5. Execution, costs, cash and missing data
- Trades at the Monday open, labelled modelled (rule 5). Costs on traded notional each week (target weights against
  drifted weights), both sides, including the first purchase and the final sale: primary 0.50% fee + 0.25%
  slippage per side; sensitivity 0.90% fee + 0.25%. Benchmarks pay the same on their own turnover (rule 3).
- A ranked coin with no Monday candle: its target weight is held in cash that week, not redistributed; the same
  rule applies to M; cases are counted.
- No price filling (rule 4). A held coin without a candle at the exit open exits at the first later daily open
  within 7 days; proceeds are held in cash until the next Monday rebalance. If there is no candle within 7 days,
  the exit is unresolved and valued three ways: 0% (primary for PASS), 50%, and the last close.
- Phase 0 cross-checks first and last candle dates against `listings_v2`; mismatches are recorded as data
  failures, not as "no trading".

## 6. Benchmarks (rules 6 and 7)
- M: value-weighted market of the same eligible universe, rebalanced weekly at the same costs (primary comparison).
- BTC hold; 50/50 BTC/ETH rebalanced weekly (fully invested, the comparable-exposure mix); cash (0%).
- The current candidate (BTC+ETH 28-day trend, volatility-scaled, rule unchanged) on D_CB_MAJ via the corrected
  harness `scripts/research/rerun_frozen_stress.py` (SHA256 recorded at freeze), period starting Sunday 2022-06-05
  so its first decision is a Sunday close and matches tracker v2's initialisation; NAV rebased to $1,000 at the
  2022-06-06 open and read at the 2026-10-05 open. Costs: 0.50% fee + 0.25% slippage per side (same as this study,
  used for PASS) and its registered 0.05% slippage (reported).

## 7. Phase 0: data gate (counts and metadata only; no returns, no indicator values)
Phase 0 eligibility = D1 without D8. All must pass or the study ends BLOCKED_DATA:
- a) every test week has at least 50 eligible coins (top quintile at least 10);
- b) the identity map is independently reviewed; at least 90% of the Coinbase product-weeks meeting D1's candle
  rule map to a CMC ID, with "unmapped" counted separately from "mapped but outside the top 1,000";
- c) every regression week used has at least 30 eligible coins; if early windows fail, the test start moves to the
  first Monday whose whole 52-week window passes (a rule fixed now, not a choice made after seeing counts);
- d) every CMC Sunday needed is present with about 1,000 rows;
- e) the listings_v2 cross-check is done and its failures recorded;
- f) the trial count is written down: H2_xs_momentum family = E6 9 + HYBRID 11 (inventory says 10; the higher
  count is used) + DYNAMIC 6 + this study 2 = 28.

## 8. Phase 1: test and decision rules
Primary metric: mean weekly net excess return of the top quintile over M, at the primary cost, 0% delisting
valuation. Inference: moving-block bootstrap of the weekly net excess returns, 4-week blocks, 4,000 resamples,
seed 20261024, percentile 95% interval.
- **FAIL** if the mean weekly net excess is at or below 0 under all three delisting valuations. The CTREND family is
  closed on Coinbase historical data; no variants.
- **PASS** only if all hold, at the 0% valuation: (1) bootstrap 95% lower bound above 0; (2) mean above 0 after
  removing the 4 largest weekly net excess returns; (3) mean above 0 at the 0.90% fee; (4) net terminal value of
  $1,000 above BTC hold and above the current candidate (section 6) over the same dates. A PASS qualifies only a
  separately approved, frozen forward paper track; no capital.
- **INCONCLUSIVE** otherwise, including when the delisting valuation flips the sign. No historical variants; only
  a separate decision on a forward track.
- `research/symbol_coverage.csv` gets one row for every outcome, BLOCKED_DATA included, with the `UNIVERSE:`
  convention and the file's existing statuses: FAIL -> REJECTED_UNDER_TESTED_CONDITIONS, INCONCLUSIVE and
  BLOCKED_DATA -> INCONCLUSIVE (the note says which), PASS -> CANDIDATE with the note "exploratory; forward paper
  track only"; scope string with dates, costs and valuation; note "basket-level; does not set single-symbol status".
- A trial-ledger supplement records the configurations (2), evaluated markets, market-weeks and weekly clusters.

Reported, never deciding: the top-100 sensitivity (eligible coins ranked 1-100 by that Sunday's CMC cap; CTREND
estimated on the full universe; quintiles formed within the subset; the second configuration); 50% and last-close
valuations; all five quintiles' returns; turnover; worst week; maximum drawdown; Sharpe; weekly BTC+ETH weight in
the top quintile and in M; effective number of holdings 1/sum(w^2); the number of forecasts kept each week and the
fallback weeks; comparisons with 50/50 BTC/ETH and cash; DSR at N = 28 (the family count) and at the
convention-specific floor of 754 (752 + 2), which is not an effective N.

Power, stated in advance: tracking error against M about 11.4% a week (paper Table 3 and supplement B.2), so the
standard error of the mean over 226 weeks is about 0.76%. A true excess of 1.2% a week (the paper's gross top
quintile 3.98% minus this study's cost of about 0.94% minus the market's 1.85-1.89%) gives t of about 1.58: about a
35% chance of PASS condition (1) and about a 6% chance of FAIL. A true excess of 0 gives about 2.5% and 50%.
INCONCLUSIVE is the most likely outcome; the test is worth running mainly because a FAIL closes the family at no cost.

## 9. Integrity controls
- Code and tests written and reviewed before any data is opened; their SHA256 frozen with this file; Python and
  library versions pinned.
- Unit tests of every indicator against hand-computed fixtures, of the candle column order, and of D1 timing.
- Look-ahead checks: a perturbation test (change every price, volume and cap after the signal Sunday; ranks and
  weights must stay bit-identical) and timestamp assertions on every input.
- Planted-leak control: a pipeline copy fed next-week returns as an indicator must be flagged by the look-ahead
  checks (scout T07-3 rule). Positive control: a synthetic indicator with planted predictive power must be kept
  by the elastic-net stage.
- An independent blind reimplementation of the portfolio accounting (weights, costs, cash, missing data) on the
  frozen CTREND ranks must agree to the cent on the $1,000 path. The signal itself is not independently
  reimplemented; that is a stated limit.
- No threshold, window, universe or cost change after Phase 0 starts. Amendments are dated, made before the run,
  and never replace the original (rule 1).

## 10. Limitations
- Both data sets were already used; the result is exploratory.
- Survivorship: products Coinbase removed from its product list are missing from the archive (number unknown;
  `wp3_universe_20261016` limit 1). No delisted product in the archive ends before 2022 (87 of 89 end on or after
  2022-06-06), consistent with older delistings missing altogether; this mainly affects the estimation data from
  late 2020 to mid 2022. The bias favours the strategy.
- The universe is narrower than the paper's (Coinbase and CMC top 1,000), early estimation cross-sections are thin,
  and Coinbase volume differs from CMC's.
- CMC caps are weekly aggregator data; CMC may have revised historical supply, and current categories are applied to
  the past.
- The identity map is static and built from today's product list.
- What a New York resident may buy is narrower than Coinbase's list (scout T10-9); not modelled.
- The account-level 0.25%/0.50% tier is SHOWN (2026-10-08); product-specific fees and the effect of the September
  2026 change are UNVERIFIED, so 0.90% is a sensitivity.
- One regime (2022-26), with altcoins weak against BTC; low power (section 8).

## 11. Cost and approvals
$0; no download and no new API requests. About 2-3 working sessions for code and tests, one independent review with a
blind reimplementation, then the run. Approvals, in order: (1) the section-6 brief question, then writing the code and
tests, then freeze after a second independent review; (2) Phase 0; (3) Phase 1; (4) any forward track, later and
separately.

## 12. Review history
- r1 (2026-10-22): independent review REJECTED it for freezing. Fixed in r2: holding-week gap exclusion (look-ahead)
  -> lookback only; Monday-candle eligibility (look-ahead) -> Sunday information only, cash for unbuyable coins;
  candidate series fixed (section 6); elastic-net choices fixed (step 4); printed helper formulas replaced by
  standard definitions (D9); truncation, rank mapping, estimation returns and cap timing fixed; 0%/50%/last-close
  valuations with FAIL requiring all three; Phase 0 regression-week, CMC-completeness and listings cross-check gates;
  identity map without new requests; exclusion list fixed in advance; top-100 sensitivity defined; family count 28;
  symbol_coverage rows for every outcome; integrity perturbation and positive controls; wording on post-sample,
  fee tier and power.

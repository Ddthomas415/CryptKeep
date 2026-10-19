# CryptKeep research brief: read before any strategy or edge work

Last updated 2026-10-15: multi-symbol mandate adopted; E10 added (Claude, cloud session). This brief is a map. The linked files are the evidence, and they win if the two disagree. Update this brief when a result changes status.

Labels follow AGENTS.md: SHOWN (evidence in repo), CLAIMED, UNVERIFIED.

## 0. Scope (read first)
- **CryptKeep is multi-symbol.** See `MULTI_SYMBOL_MANDATE.md`. The supported universe is the 25 symbols in `config/candidate_universe.yaml`, all tradable as Coinbase USD products.
- **The findings below are research evidence for specific symbols and conditions. They are not the project's scope.**
- **Coverage (2026-10-15, after E10; `research/symbol_coverage.csv`):**
  - The 10 Coinbase core pairs have each had a standalone slow-trend test. Results:
    - CANDIDATE vs hold: ETH, AVAX, DOT;
    - INCONCLUSIVE: BTC, SOL, DOGE, ADA;
    - REJECTED under tested conditions: LTC, LINK, XRP.
  - The equal-weight 10-symbol trend portfolio was rejected vs BTC+ETH.
  - 15 symbols (BNB and the tier-2 and watchlist symbols) remain UNTESTED.

## 1. Bottom line
- **No proven edge** (SHOWN).
  - **Candidate:** one, the BTC+ETH 28-day volatility-scaled trend rule. It has better risk-adjusted returns than BTC and fixed BTC/ETH/cash mixes at about 0.5% fees, with smaller drawdowns.
  - **Return:** it has no proven return advantage over BTC, and it depends on costs.
- **The literature agrees:** only slow trend plus volatility scaling survives retail costs for a long-only spot account. Its benefit is mainly drawdown control, not alpha. See `crypto_trading_edges_survey_20261013.md`.
- **Further work:**
  - cost reduction and risk engineering around the candidate;
  - systematic, pre-registered coverage of the wider universe with the families that survive costs (first: E10, the slow-trend portfolio across the Coinbase core pairs);
  - no unregistered signal hunting.

## 2. Costs: confirm before trusting any backtest
- **Account fee tier:** 0.25% maker / 0.50% taker per side. SHOWN for the account-level SPOT tier via an authenticated read on 2026-10-08 (`research/coinbase_fee_observation_20261008.json`). Product-specific fees are UNVERIFIED.
- **Conflicting secondary sources:**
  - entry tier 0.40% / 0.60%;
  - a reported Sep 2026 US change to 0.50% / 0.90%.
  - Both are UNVERIFIED. The operator must confirm BTC-USD and ETH-USD rates in the Coinbase app.
- **Round trip at 0.25/0.50:** 0.50% (maker/maker) to 1.00% (taker/taker), plus spread.
  - Weekly full turnover costs about 26-52%/yr.
  - Monthly full turnover costs about 6-12%/yr.
- **Never use the simple Coinbase buy/sell flow** (0.5-2% spread built in). Use Advanced only.
- **Limit fills are adversely selected:** easy fills tend to be followed by adverse moves. A backtest must model unfilled orders and post-fill drift.
- **Server:** about $20/month. This is an operator estimate (CLAIMED); the invoice is not seen. Workloads: `server_workload_inventory_20261011.md`.
- **Tax:** short-term gains are taxed as ordinary income. Brokers have issued Form 1099-DA since 2025.

## 3. What the evidence says (details and sources: `crypto_trading_edges_survey_20261013.md`)
| Works for this account (modest) | Real but not usable here | Fails at these fees / decayed / debunked |
|---|---|---|
| Slow trend (20-100 day) on BTC/ETH (other symbols untested) | Futures carry / basis (needs futures) | Cross-sectional momentum, size, reversal as tested (E6 basket, leader pullback; scoped in the registry) |
| Volatility scaling, capped at 100%, with rebalance bands | Selling options (variance premium) | Calendar, overnight and intraday rules |
| Avoidance filters: no microcaps, fresh listings, big unlocks, hacked tokens | Arbitrage, order flow, MEV, liquidity-pool provision | Buying listing announcements (move happens before) |
| Funding/basis crash brake: tested 2026-10-13, FAILED as an overlay on the trend candidate | | Most on-chain and sentiment signals (largely repackaged price momentum) |

## 4. Project results to date
| Idea | Status | Evidence |
|---|---|---|
| BTC+ETH 28d trend, vol-scaled | **CANDIDATE** | `btc_eth_corrected_comparison_20261012/`, `dsr_btc_eth_trend_20261011/`, `stress_fee050_exploratory_20261011/` (exploratory), `edge_classification_btc_eth_20261011.md` |
| Same rule, registered stress test at 1.2% | REJECT (stands) | `research/research_corrections_20261009/stress_corrected_v1.json` |
| Altcoin event rules (~448 configs), breakout, recovery/regime, short-hold, CMC proxy, dynamic Coinbase, hybrid | Rejected or inconclusive | `consolidated_economic_summary_20261010.md`, `strategy_decision_report_20261011.md` |
| Top-gainer pullback dip-buying (8 variants) | FAIL: all lost before and after costs | `leader_pullback_study_20261012.md`, `leader_target_test_20261012.md` |
| Dip-recovery screen | Withdrawn (used future information) | `dip_recovery_screen_20261012.md` |
| Weekly altcoin cross-sectional momentum | FAIL; simulator defect annotated | `xs_momentum_20261012/` |
| Funding-rate crash brake (E7) on the candidate | FAIL: no drawdown improvement, slightly lower returns; redundant with the trend signal | `crash_brake_20261013/` |
| Composite v1: 20/50/100/200-day trend ensemble + 10-pt rebalance band (E8) | FAIL: better in 2017-23, much worse in the 2024-26 holdout (Sharpe 0.45 vs 0.87) | `composite_v1_20261013/` |
| Band 0.10 alone on the unchanged candidate (E9) | FAIL on the registered turnover criterion (0.90x, needed ≤ 0.75x); otherwise better Sharpe and ending value in D and H at both fees and half the trades. Criterion mis-specified; resolve with FORWARD tracking, not a re-test | `candidate_band_20261013/` |
| Slow-trend portfolio across 10 core pairs, equal 1/N (E10) | FAIL vs BTC+ETH incumbent (Sharpe 1.20 vs 1.46 in D, 0.51 vs 0.88 in H). Standalone: trend cut drawdowns on every symbol; per-symbol statuses in the registry | `multisymbol_trend_20261015/` |
| Maker vs taker execution | Pre-registration draft v2, NOT frozen; waits on fee confirmation | `maker_taker_prereg_20261011/` |
| CMC trending | Collecting; primary analysis no earlier than 2027-02-15 | `cmc_trending_log/` |
| Forward tracker v2 | Built (23 tests), NOT scheduled; v1 still runs Mondays 00:47 UTC | `paper_btc_eth_trend_v2_20261012/` |

Selection count: about 576 configurations, plus E6-E10 (about 40 more trials including sensitivities); roughly 10-20 effective trials so far. New tests add to this count and to the multiple-testing deflation.

## 5. Research rules (non-negotiable)
1. **Write the rules down before seeing data or results.** Amendments must be dated, made before running, and never replace the original.
2. **Count every variant tried.** Report all of them, losers included. Correct for selection: DSR at realistic N, with sensitivity.
3. **Use real costs:** fee + slippage on every trade, for every strategy AND every benchmark. Report results at both the confirmed tier and a higher-cost tier.
4. **No price filling.** A missing candle is not a tradable price. Failed downloads are recorded as failures, never as "no trading".
5. **Execution:** decide at a close, trade at the next open (or model limit fills honestly). Executions are labelled modelled unless they are actually observed.
6. **Benchmarks:** hold BTC, a fixed BTC/ETH/cash mix at comparable exposure, and cash. Label mixes fully (e.g. 25/25/50 means 50% cash).
7. **Judge new ingredients against the current candidate,** not just against BTC.
8. **Keep the 2024-01-01 to present data as a holdout,** opened once at the end for any new combined strategy.
9. **Preserve originals and registered verdicts.** Exploratory results are labelled exploratory. No profitability claims; DSR is not a profit probability.
10. **Universe and survivorship:**
    - Survivorship bias is large (about 53% of tracked tokens have failed). Use datasets that include delisted coins, and say what is still missing.
    - Every symbol tested counts as a trial.
    - Every negative result is scoped to its symbols and conditions in `research/symbol_coverage.csv`.

## 6. Next steps (as of 2026-10-13) and what not to do
1. Operator: confirm the BTC-USD and ETH-USD maker/taker fees in the app.
2. Re-run the candidate at the confirmed fee (and a higher-cost tier), keeping 2024-26 as the holdout.
3. Operator decision, after review: switch the weekly task to tracker v2 (first decision Sunday 2026-10-18).
4. ~~Crash-brake test~~: done 2026-10-13, FAIL (`crash_brake_20261013/`).
   - Binance funding history is reachable only via the Hetzner host (US IPs are blocked).
   - The data file is preserved under `research/crash_brake_20261013/`.
5. Freeze the maker-vs-taker study once fees are confirmed.
6. ~~Band-only test~~: done (E9). Next: add a 'candidate + band 0.10' account to tracker v2 for forward comparison; needs code, tests and review. Note: 2024-26 was inside the candidate's selection windows, so it is not a true holdout for the candidate.

**Do not:**
- run unregistered signal hunts on any symbol;
- rescue failed variants;
- tune parameters on the holdout;
- generalize a scoped rejection to a whole asset class;
- add paid data or infrastructure without a cost-benefit case (`research_budget_90d_20261011.md`).

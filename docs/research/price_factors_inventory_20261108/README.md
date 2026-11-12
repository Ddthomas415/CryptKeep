# What moves coin prices: what CryptKeep has tested, can access and has built in (2026-11-08)

Bot relation: STANDALONE (an inventory and advice; no result is computed). Bot code in `services/` was read, not run;
runtime configuration not checked.

Written at the owner's request ("make a note the findings", 2026-11-09 UTC). It records three answers Claude gave on
2026-11-08:
- the factors that move prices;
- which of them the repo has data or code for;
- Claude's advice.

Self-checked; Codex to verify. Nothing here is an owner decision.

**Correction made while writing this note:** the 2026-11-08 answer said ATR is "used in exits". No ATR was found in the
runner's exit controls (`services/risk/exit_controls.py`). ATR appears in the regime detector and in the
`sma_200_trend` strategy module (section 2a).

## 1. Factors, and what CryptKeep has tested

Status: **TESTED** (a test or study exists), **DISCUSSED** (listed, never run) or **NO RECORD FOUND**.

| Factor | How it moves the price | Status in CryptKeep | Evidence |
|---|---|---|---|
| Trend (momentum) | Coins rising for weeks tend to keep rising; falling ones keep falling | TESTED. BTC+ETH 28-day trend is the only CANDIDATE. Weekly altcoin momentum FAIL. 10-coin trend (E10) FAIL against BTC+ETH, though it cut drawdowns on every coin | `RESEARCH_BRIEF.md` section 4; `xs_momentum_20261012/`; `multisymbol_trend_20261015/` |
| Bitcoin's direction | Most coins follow BTC and usually fall harder when it falls | TESTED as a filter: a "market up" gate (BTC above its 200-day average and over half of coins above their 50-day average) on the altcoin recovery rule, rejected or inconclusive. Dip study: every dip combination lost in the years BTC fell | `recovery_momentum_20261009/recovery_regime.py`; `RESEARCH_BRIEF.md` section 4; `dip_recovery_majors_20261108/` |
| Interest rates, the dollar, stock markets | Cheap money and rising stocks pull money in; rate rises and sell-offs pull it out | NO RECORD FOUND | Keyword search (method below) |
| Leverage and liquidations | Forced closing of borrowed bets snowballs; funding rates show the crowded side | TESTED: funding crash brake on the candidate (E7) FAIL; BTC/ETH funding carry for one month too small to cover server cost. Liquidation rebound checked once over 2 hours (U-18). Open-interest flag (U-34) and a new funding hypothesis (U-14) not done | `crash_brake_20261013/`; `funding_carry_feasibility_20261012.md`; `liquidation_markout_diagnostic_20261012.md` |
| Money flows (ETFs, stablecoins, exchange deposits) | Inflows add buyers; deposits to exchanges often precede selling | DISCUSSED (U-22, U-35). The research scout found studies showing no effect for on-chain flow signals (U-05 row) | `PROJECT_STATE.md` Undecided ideas |
| Supply changes (unlocks, emissions, burns, halvings) | New tokens add sellers; burns and halvings cut new supply | DISCUSSED (UNLOCK-1 held, U-12; unlock calendar, U-37). Data check INCOMPLETE | `unlock_data_feasibility_20261020.md` |
| Whales and holder concentration | A few big holders can move a thin market | DISCUSSED (U-05, never started) | `PROJECT_STATE.md` |
| Exchange events (listings, delistings, halts, limit-only) | Listings bring buyers; delistings and halts force selling | TESTED in part: new top-100 entrants (ENTR-CB-1) STOP. Fresh-listing filter held (U-13). Historical listing study not run (U-19). A held-coin rule for delistings and limit-only is required in the 25-symbol comparison (ED-002). The survey found most listing gains come before the listing day | `coinbase_tradable_entrants_20261019/`; `crypto_trading_edges_survey_20261013.md` line 31 |
| News, regulation, government | Lawsuits, bans, approvals, tax, enforcement | NO TEST; news sentiment DISCUSSED (U-22); proposed rule R27 (sentiment tends to follow prices) | `claude_research_document_20261020/proposed_rules_reconciliation.md` |
| Hacks and failures | Exploits, de-pegs, exchange collapses | DISCUSSED (U-33) | `PROJECT_STATE.md` |
| Attention and hype | Social media and trending lists bring short bursts of buyers | CMC trending log collecting (analysis no earlier than 2027-02-15). Wikipedia attention (ATTN-1) BLOCKED_DATA. Social sentiment DISCUSSED (U-22) | `cmc_trending_log/`; `attn1_phase0_20261021/` |
| Liquidity | Thin books (small coins, weekends, nights) let small orders move the price | TESTED: calendar, overnight and intraday rules rejected as tested; low-value top-100 screens no edge (U-01). Spread and timing gate never revisited (U-11). Maker/taker study (E1) not frozen | `RESEARCH_BRIEF.md` sections 3-4 |
| Volatility | Big moves follow big moves, in both directions | Used for sizing in the candidate. Chronos-2 volatility forecast (VOLFC-1) FAIL. Dip study: dips fell further before rising | `chronos_vol_forecast_20261018/`; `dip_recovery_majors_20261108/` |
| Short-term bounce (reversal) | Partial rebound after a drop | TESTED: top-gainer pullbacks FAIL (8 variants). Dip-recovery screen withdrawn (H-03). Dip study 2026-11-08: no dependable head start; small gains only in rising years | `leader_pullback_study_20261012.md`; `leader_target_test_20261012.md`; `dip_recovery_majors_20261108/` |
| Fundamentals (fees, users, developer activity) | Usage and revenue support value over time | DISCUSSED (U-22) | `PROJECT_STATE.md` |
| Sectors and narratives | Money rotates into themes (AI, memes, layer-2s) | Never assessed (U-23) | `PROJECT_STATE.md` |
| Manipulation (pump-and-dump, wash trading, spoofing) | Fake demand or volume moves prices | Never assessed (U-23) | `PROJECT_STATE.md` |

## 2. What the repo has: code and data

### 2a. In the bot's code path and used when it trades
Which of these the settings switch on was not checked.
- **Strategies:** the runner's `services/strategies/strategy_registry.py` `SUPPORTED` lists `ema_cross`,
  `mean_reversion_rsi`, `breakout_donchian`, `momentum`, `volatility_reversal`, `gap_fill`, `breakout_volume`,
  `pullback_recovery`, `sma_200_trend` (ES daily trend, 200-day average) and `funding_extreme`. All but
  `funding_extreme` read only the coin's own candles.
- **Volatility (ATR):**
  - `services/market_data/regime_detector.py`.
  - The `sma_200_trend` module (`services/strategies/es_daily_trend.py`), which defines an ATR regime gate and a
    2 x ATR stop. Whether the runner applies that stop was not checked.
- **Market-quality guard:** `services/risk/market_quality_guard.py`. By default it blocks trading when the spread is
  above 500 basis points (5%) or the quote is over 600 seconds old. The runner calls it (`strategy_runner.py` lines 816
  and 1044).

### 2b. In the code but not deciding trades
| Factor | Code | Why it does not decide trades |
|---|---|---|
| Market regime | `select_strategy` runs `detect_regime` on each coin's candles | Output is advisory; the runner uses the configured strategy (`strategy_runner.py` about lines 1377-1384) |
| Funding | `funding_extreme` is connected; the runner reads funding through `services/strategies/crypto_edge_context.py` | Even fresh rows return `ok: False` (`funding_context_unqualified`, qualification not finished), so the strategy holds (`missing_funding_context`) |
| Open interest | `services/market_data/market_intelligence.py` (`get_open_interest_snapshot`, ccxt Binance); `services/strategies/open_interest_shift.py` | Dashboard page `40_Market_Intelligence.py` only; not in `SUPPORTED` |
| Fear & Greed | `services/market_data/alternative_data.py` (`get_fear_greed`, alternative.me, latest 2 days) | Symbol scanner (services and dashboard) only |
| Liquidations, social sentiment | `market_intelligence.py` | Placeholders returning empty values (`scaffold_only_no_live_liquidation_feed`, `scaffold_only_no_social_feed`) |
| Delisting and limit-only exits | `services/execution/exit_deferral.py` | Its header: "Unwired, pure exit planner" |
| Market-context capture | `market_context_capture_v0.md` | Default off; never activated |

### 2c. Data in the repo (research only; the bot does not use it)
- **`docs/research/raw_archives_20261009/`** (see its README):
  - Coinbase hourly candles: 395 USD products, 2025-10-09 to 2026-10-08. Every one of the 10 large coins fell 34-74%
    over this period.
  - Coinbase BTC and ETH daily candles since 2015-16.
  - Binance daily candles: 484 current pairs since 2019, and all 677 pairs ever listed (including delisted) since 2017-08.
  - CoinMarketCap weekly top-1000 snapshots, 2018-11-04 to 2026-10-04 (414 files), plus the 2026-10-09 trending lists.
    Each row holds id, symbol, slug, rank, price, 24-hour volume, market cap, a percentage change (inferred to be 7-day)
    and the date added, plus tags. Circulating supply (market cap / price) and sectors (tags) can be derived; whether
    the tags are as of each date was not checked.
- **Daily candles for 10 large coins:** `research/multisymbol_trend_20261015/data/` (BTC, ETH, SOL, XRP, DOGE, ADA,
  AVAX, LINK, LTC, DOT), from 2017-2021 to 2026-10-11.
- **Listing candles:** `research/coinbase_listing_stepB_20261019/candles/`.
- **Liquidations:** `research/liquidation_data_probe_raw_20261012.json`, a 2-hour BTC/ETH sample. It shows the public
  feed works.
- **Funding:**
  - `research/funding_carry_raw_20261012.json` (BTC/ETH, 2026-09-12 to 10-12), plus OKX funding tooling (`okx_funding_*`).
  - The Binance funding history used by E7 is not stored; only its hashes are, in `crash_brake_result.json`.
- **CMC trending log:** `docs/research/cmc_trending_log/`, still collecting.

### 2d. Nothing in the repo (no data and no code found)
- **Macro:** interest rates, the dollar, stock markets.
- **Flows:** ETF flows and stablecoin flows.
- **On-chain and whale data:** point-in-time data exists from paid vendors (on-chain handoff audit, 2026-11-05).
- **Token unlock schedules:** the sources found need a paid plan or an API key (DefiLlama Pro, Tokenomist); about
  $69-300 per U-12.
- **News and regulation.**
- **Hack events.**
- **Fundamentals.**
- **Manipulation screens.**

## 3. Claude's advice (given 2026-11-08 19:54 UTC; a proposal, no owner decision)
Do not add new market factors yet. First make the one surviving rule trustworthy and cheaper, then test other factors
only as filters on it.

1. **Get tracker v2 running again.**
   - It is the forward test of the only surviving rule, and its state files have not changed since 2026-10-26. It
     missed the 2026-11-01 decision.
   - Owner action: check the Codex Scheduled view.
2. **Cut costs before adding signals: maker versus taker, E1 (already in the plan).**
   - At the 0.50% taker rate the candidate spends about 6% of the account a year on costs
     (`candidate_descriptive_20261107/`). The maker rate is 0.25%, so filling as maker could cut that by up to half.
   - E1 has stalled: its arrival capture is not built, and no freeze was recorded by its 2026-11-03 date (U-10).
3. **Add other factors only as filters on that rule** (stay out or trade smaller), not as new strategies.
   - Why: at least 747 configurations of price-only rules have been tested, and only this rule survived. The edge map
     warns that more variants mostly add false positives.
   - **Funding and open interest: low to medium.** The data is free and the code is mostly built. But E7 already
     failed on this rule, so only a new question on unused data would add anything (U-14).
   - **Fear & Greed: low.** Free, but proposed rule R27 says sentiment tends to follow prices.
   - **Unlocks, delistings, hacks: not now.** They matter for altcoins, not BTC/ETH, and unlock data costs money.
   - **Macro, ETF flows, on-chain, news: skip for now.** No data in the repo, some of it paid, and the weakest evidence
     at this trade size.
4. **One link between the dip study and the candidate:** "buy dips only while the trend rule is on".
   - Dips gained only in rising years, and the trend rule detects rising markets in real time.
   - The gains were small: at best +0.48% per trade, in 10 of 25 combinations, from a split made with hindsight.
   - Testing it needs a plan written before computing and hourly data from a rising period (a download needing owner
     approval). It ranks after items 1 and 2.
5. **Deadline:** under proposed rule R28, any question scored on the CMC trending log must be registered before its
   window opens on 2026-11-10. The research document recommended adding none.

## 4. State when this note was written (checked 2026-11-09 01:01 UTC)
- Tracker v2: `paper_btc_eth_trend_v2_20261012/state/` files still last changed 2026-10-26 00:52 UTC. The decision due
  2026-11-09 01:47 UTC (Sunday 20:47 New York) had not yet happened.
- Newest Codex work-log entry: 2026-11-05 21:12 UTC. Newest commit: `82b5f216e` (2026-11-01).

## Method and limits
- **Code:**
  - A case-insensitive keyword search of `services/**/*.py`. Keywords: funding, open interest, liquidation, sentiment,
    news, on-chain vendor names, unlock, listing/delist, etf, stablecoin, fear and greed, social, macro, volatility,
    spread, whale.
  - The matching files and their importers were then read.
  - A miss does not prove a feature is absent under another name.
  - One false match: "macro" matched "EMACrossover"; no macro code was found.
- **Data:** a file-name search plus the archive README. The CMC row fields were read from one weekly file (2022-06-12).
- **Tested column:** taken from `RESEARCH_BRIEF.md` section 4, the `PROJECT_STATE.md` "Undecided ideas" table and
  the folders named. Those results were not re-checked here.
- **Settings:** `config/user.yaml` was not read, so which strategies are switched on is unknown.

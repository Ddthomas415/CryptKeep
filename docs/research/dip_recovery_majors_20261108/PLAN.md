# How long popular coins take to rise after a small dip: plan, written before any computation

Bot relation: STANDALONE (public price history only; no bot code, configuration or runtime is used); runtime
configuration not applicable.

Owner request (2026-11-08 UTC): gather data on a few popular coins, find when a coin falls 1% to 5%, and see how long
it takes to gain 1% to 5%. Claude proposed the definitions below; the owner approved them with "go ahead".

This is a **descriptive study, not a test.** Nothing is promoted, rejected or wired into the bot. The price files
have been used by earlier studies, so nothing here is holdout evidence (`RESEARCH_BRIEF.md` rule 5.8).

## Earlier related work (searched 2026-11-08)
- `dip_recovery_screen_20261012.md`: withdrawn because it used future information (`PROJECT_STATE.md` H-03,
  `RESEARCH_BRIEF.md` results table).
- `leader_pullback_study_20261012.md`, `leader_target_test_20261012.md`: buying the day's biggest gainers after a
  pullback; all 8 variants lost before and after costs.
- `hourly_leader_recovery_20261012.md`: hourly leaders after 10% or 20% pullbacks, 5% or 10% targets.
- `edge_map_20261013.md`: "Not worth more effort now: more altcoin pump, dip, breakout or momentum variants."
- What differs here: 10 large coins, small dips of 1% to 5% from the 24-hour high, targets of 1% to 5%, and every
  result is set beside buying at any hour.

## Coins (fixed now)
BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK, LTC, DOT: the 10 coins of the existing daily set below.

## Inputs (all already in the repository; no download)
- **Hourly:** `cb/h1/<COIN>-USD.json` and `cb2/h1/<COIN>-USD.json` from
  `docs/research/raw_archives_20261009/coinbase_hourly_last60d.tar.xz` (sha256 `435220c4...`) and
  `coinbase_hourly_prior10m.tar.xz` (`2bb417a2...`). Each file is checked against `SHA256SUMS_inputs.txt`.
  - Columns: time, open, high, low, close, volume (README of the archive; checked: every row has low <= open, close
    <= high).
  - Coverage: 2025-10-09 00:00 to 2026-10-08 23:00 UTC, 8,750 candles per coin. Every coin has the same two 5-hour
    gaps (from 2025-10-25 15:00 and 2026-05-08 01:00 UTC).
- **Daily:** `research/multisymbol_trend_20261015/data/<COIN>-USD.json`, checked against that folder's `SHA256SUMS`.
  - Columns: time, low, high, open, close, volume (Coinbase order; checked: every row fits only this order).
  - Starts: 2017-01-01 for BTC, ETH and LTC; 2019 for XRP and LINK; 2021 for SOL, DOGE, ADA, AVAX and DOT. Ends
    2026-10-11. XRP has no candles for 904 days from 2021-01-20 (Coinbase suspended XRP trading).

## Definitions
- **Drop, hourly:** at each hourly close, D = close / (highest high of the 24 hourly candles ending with this one) - 1.
  D exists only when all 24 of those candles are present.
- **Dip event at level X** (X = 1, 2, 3, 4, 5%), hourly: the first close with D <= -X after a close with D > -X
  (crossing into the dip), while no trade from an earlier event at the same coin, X and Y is open.
- **Drop, daily:** D = the day's close / the day's high - 1 (a daily candle covers the 24 hours ending at its close).
  Event: D <= -X while no trade is open. Each day is a new 24-hour window, so there is no crossing rule.
- **Entry:** the open of the next candle (hourly: that hour must exist; daily: that day must exist). Never the bottom.
- **Target Y** (Y = 1, 2, 3, 4, 5%): entry x (1 + Y). Reached when a high is >= the target, from the entry candle on
  (its high comes after its open). The sale is at the target price, as a resting limit sell would be.
- **Time to target:** candles from entry to the candle where the target is first reached, counting the entry candle
  as 1. Hours for hourly data, days for daily data.
- **Timeout:** 30 days (720 hourly candles, 30 daily candles). A trade that has not reached its target is sold at the
  close of the last candle in that window.
- **Fell further first:** the lowest low from entry up to and including the candle where the target is reached (or to
  the timeout), as % of entry. The target candle's low is included although its timing inside the candle is unknown,
  so this is a worst case.
- **No overlap:** for each coin, X and Y, a new event can start only after the earlier trade ends (the candle where it
  reaches the target, or the timeout candle).
- **Random comparison ("random"):** the same entry, target, timeout and costs, starting from every hourly candle
  (every day, for daily data) that has a complete 24-hour window and a next candle. These starts overlap by design:
  they describe buying at any time.
- **Conservative check:** the target counts only when a candle closes at or above it, and the sale is at the next
  candle's open. Computed for every combination.

## Observation windows
- A rate "within H" (hourly: 24 hours, 7 days, 30 days; daily: 1, 7, 30 days) counts only events whose H-window ends
  on or before the last candle. Events still open when the data end are counted and reported, not treated as failures.
- Hourly windows may contain the two 5-hour gaps. Daily windows that include a missing day (XRP's suspension) are
  excluded and counted.

## Costs
- Fee 0.50% or 1.20% per side, plus 0.05% slippage per side (the same two levels as research item 7; the account's
  current fee tier is unverified).
- Net return of a trade = exit x (1 - 0.0005) x (1 - fee) / (entry x (1 + 0.0005) x (1 + fee)) - 1. A buy plus a sell
  costs about 1.1% at the lower fee and 2.5% at the higher one.
- Net results use only trades with a complete 30-day window.

## Measures, for every coin, X and Y (10 x 5 x 5), hourly and daily, dip events and random
1. Number of events.
2. Share reaching the target within 24 hours, 7 days, 30 days (daily: 1, 7, 30 days).
3. Median time to target, among those reaching it within 30 days.
4. Median and worst "fell further first".
5. Average net return per trade, and the share of trades above zero after costs, at each fee level.
6. The same, pooled over the 10 coins (each event counted once).
7. Consistency: the number of coins (of 10) where dips reach the target within 24 hours (daily: 1 day) more often than
   random; the hourly results for each half of the year (events starting before, or from, 2026-04-09 00:00 UTC);
   daily results by calendar year for -3% / +3%.
8. Context: each coin's price change over the hourly year, and BTC's change per calendar year.

## README contents, fixed now
- Pooled 5 x 5 grids, dip beside random: share within 24 hours (daily: 1 day), share within 30 days, median time,
  average net at the 0.50% fee. Hourly and daily.
- Per coin for -3% / +3%, hourly and daily.
- The five equal pairs (-1% / +1% to -5% / +5%): the two halves of the hourly year, the conservative check, and the
  1.20% fee.
- Daily by calendar year for -3% / +3%.
- Everything else in `results.json`.

## Checks before reporting
- Hand-check 3 events in each data set against the raw candles: entry, target candle, time, lowest low.
- Event counts: resolved plus still-open plus excluded add up to the total.
- Recompute one net return by hand.
- If a check fails: fix, rerun, and say so in the README.

## Not done
- No other coins, drop levels, targets, timeouts, exchanges or fees, and nothing changed after seeing results.
- No significance test. Dips on different coins happen at the same times and hourly events cluster, so pooled counts
  overstate the number of independent observations.
- No order-book data: a price being touched does not guarantee a fill.
- No download, no bot code, no settings.

Budget: 1 session. Stop rule: stop and report if an input checksum fails; no new variant after seeing results.

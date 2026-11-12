# How long popular coins take to rise after a small dip (2026-11-08)

Bot relation: STANDALONE (public price history only; no bot code, configuration or runtime used); runtime
configuration not applicable.

**Descriptive, not a test.** Nothing is promoted, rejected or wired into the bot. The price files were used by earlier
studies, so nothing here is holdout evidence (`RESEARCH_BRIEF.md` rule 5.8). Self-checked; Codex to verify.

| File | SHA256 | Contents |
|---|---|---|
| `PLAN.md` | `b7e5b098...` | Definitions, written before any computation (work-log task card 2026-11-08T00:38:00Z) |
| `describe.py` | `06d4beff...` | The computation; standard-library Python; hash-checks every input |
| `results.json` | `c9c7f8c4...` | Every measure for 10 coins x 5 drops x 5 targets, hourly and daily, dip and random, both target rules |
| `grid.csv` | `f007504e...` | The same, one row per data set, target rule, coin, drop, target and side |

## Question (owner, 2026-11-08)
When a popular coin falls 1% to 5%, how long does it take to gain 1% to 5%?

## How it was measured (full definitions in `PLAN.md`)
- **Coins:** BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK, LTC, DOT, all Coinbase USD prices already in the repository.
  - Hourly: 2025-10-09 to 2026-10-08. Every coin fell over that year, by 34% to 74%.
  - Daily: 2017 (BTC, ETH, LTC), 2019 (XRP, LINK) or 2021 (the rest) to 2026-10-11.
- **Dip:** a close at least X% below the highest price of the previous 24 hours (hourly: the last 24 hourly candles;
  daily: the day's own high). X = 1% to 5%.
- **Buy** at the next candle's open, never at the bottom.
- **Target:** Y% above the buy price (Y = 1% to 5%), sold when the price touches it, as a resting limit sell would be.
- **Waiting:** up to 30 days, then sold at the close. One trade at a time for each coin, drop and target.
- **Random:** the same trade started from every hour (daily data: every day), to show what buying at any time gives.
- **Costs:** 0.50% fee plus 0.05% slippage per side (about 1.1% for a buy and a sell); also 1.20% plus 0.05% (about
  2.5%). The account's current fee tier is unverified.
- **Conservative check:** the target counts only after a candle closes at or above it, and the sale is at the next open.

## Results

**1. How long it takes.**
- **Hourly year:**
  - **+1%:** usually within hours, from a dip or not. After a dip: median 5 to 7 hours, and 66-72% got there within 24
    hours. From any hour: median 8 hours, 68% within 24 hours.
  - **+3%:** median 1 to 2 days after a dip (24.5 to 54 hours), against 46 hours from any hour.
  - **+5%:** median 3 to 8 days after a dip (66 to 188 hours), against 97 hours from any hour.
- **Daily, 2017-2026:** median 1 to 3 days for every combination, dip or not. Daily candles cannot show anything
  shorter than a day.

**2. A dip did not give a dependable head start.**
- **Hourly year:**
  - **Within 24 hours:** dips reached the target more often than random in 22 of the 25 combinations, mostly by a few
    points. The largest gaps came after the smallest dip: a -1% dip reached +5% within 24 hours 21% of the time,
    against 13% from any hour.
  - **Within 30 days:** dips reached the target less often than random in all 25 (-3% / +3%: 77% against 81%).
  - **Fell further first:** dips fell further below the buy price before reaching the target (-3% / +5%: median 9%,
    against 6%).
  - **Halves of the year:** the pattern reversed between them. From October to April, dips did worse than random on
    every measure shown, for all five equal pairs. From April to October they did better on every one.
- **Daily, 2017-2026:**
  - **Within the entry day:** dips reached the target more often than random in all 25 combinations, for at least 9
    of the 10 coins each time (-3% / +3%: 45% against 39%).
  - **Within 30 days:** dips were ahead by less than 3 points (0.7 to 2.9; -3% / +3%: 88% against 87%).
  - **Fell further first:** dips also fell a little further first (-3% / +3%: median 4.4% against 3.9%). That fits
    bigger swings in both directions after a day that closes well below its high, rather than a tilt upward. This
    explanation was not tested.
  - **By year (-3% / +3%):** dips did better than random after costs in only 4 of the 10 years.

**3. Under the main rule, every combination lost money on average after costs, dip or random.**
- **Hourly, 0.50% fee:** dips -1.86% to -4.29% per trade, random -1.75% to -2.70%. Dips were worse than random in all 25.
- **Daily, 0.50% fee:** dips -0.66% to -1.08% per trade, random -1.09% to -1.21%. Dips were less bad in all 25.
- **1.20% fee:** every combination lost under both rules. Dips: about -2.4% per trade daily and -3.3% to -5.6%
  hourly, for the equal pairs.
- **Conservative check:**
  - Hourly: negative everywhere.
  - Daily, at the 0.50% fee: 9 of the 25 dip combinations ended slightly above zero, +0.04% to +0.33% per trade.
    They are mostly the smaller dips with the larger targets (table below the equal pairs). Random starts were
    negative in all 25.
  - Likely reason, not tested: this rule sells at the next open after a close above the target. With 24-hour
    trading, that open is about the close, so a strong day is not capped at the target.
  - Per trade these are small figures, with no significance test. Their years were not checked, and the main
    rule's years were not stable (point 2). They are not evidence of a usable edge.
- **Why the main rule loses:**
  - A +1% target can never win: it is smaller than the 1.1% cost of a buy and a sell, so 0% of those trades ended
    above zero.
  - For larger targets most trades do win, but each win is capped at the target, while the misses are held for 30 days
    and lose a lot.
  - At -3% / +3%, each win nets +1.87%. Worked out from the table figures, the misses averaged about -20% hourly and
    -23% daily.
- **Small differences:** no significance test was run, and dips on different coins happen at the same times (see
  limits), so small differences between dip and random should not be read as real.

## Relation to earlier work
- These results agree with the earlier dip-buying studies that failed: `leader_pullback_study_20261012.md` and
  `leader_target_test_20261012.md` (8 variants, all lost before and after costs).
- They agree with `edge_map_20261013.md` ("Not worth more effort now: more altcoin pump, dip, breakout or momentum
  variants").
- This study used large coins and small dips. It does not revive `dip_recovery_screen_20261012.md`, which stays
  withdrawn (`PROJECT_STATE.md` H-03).

## Checks (SHOWN)
- **Inputs:** the script hash-checks both archives, the 20 hourly files and the 10 daily files before computing.
- **Hand checks against the raw candles,** with separate code, all matching:
  - **BTC hourly, -3% / +3%:** event at the 2025-12-12 15:00 UTC close, -3.89% from the 24-hour high of $93,594.76
    (the previous close was -1.23%). Bought at $89,922.82; target reached 562 hours later (2026-01-05 01:00); lowest
    -6.14%.
  - **BTC hourly 30-day timeout:** bought 2025-10-10 17:00. The window has 715 candles because of a 5-hour data gap.
    The highest high was below the target; sold at the $103,826.64 close.
  - **BTC daily, -3% / +3%:** event 2017-02-09, -7.86% from the day's high. Bought at $993.58; reached on day 2;
    lowest -3.28%.
  - **BTC daily, conservative check:** a timeout from 2017-01-06; the highest close was $1,035.54 against a target of
    $1,037.21.
- **Net return formula:** a +3% target nets +1.8732% at the 0.50% fee, worked out by hand.
- **Counts:** in every cell, events = excluded for a gap + full 30-day window + open when the data end + reached with
  an incomplete window.

## Limits
- **Descriptive only.** No holdout and no significance test. Events cluster: dips on different coins happen at the same
  times, so pooled counts overstate the number of independent observations.
- **Hourly year:** one year only, and a falling one for all 10 coins. The daily figures cover rising and falling years.
- **The trade has no stop-loss:** the 30-day wait drives the losses. No other waiting time, stop or exit was tried.
- **Fills:** a price being touched does not guarantee a fill. Costs are assumptions; the account's fee tier is
  unverified.
- **Daily data errors, kept unchanged as the plan requires:**
  - BTC on 2017-04-15 has a low of $0.06. This bad price is why BTC's worst "fell further first" shows -100%.
  - ETH on 2017-04-15 has a high of $74.98 against an open of $47.19 and a close of $48.94. It can count as reached at
    most a few dip trades, and up to 30 of the 24,963 random starts per target.
  - ETH on 2017-06-21 has a low of $0.10 (the June 2017 exchange flash crash).
  - LTC on 2017-05-03 has a high of $36 against a close of $22.01.
- **Hourly and daily differ in more than candle size:**
  - The drop is measured differently: a rolling 24 hours, against the day's own high.
  - Daily "within 1 day" counts only the entry day.
  - In the daily pooled figures BTC, ETH and LTC weigh more, because they start in 2017.
- **Data gaps:**
  - Hourly: two 5-hour gaps, on 2025-10-25 and 2026-05-08, are left in.
  - Daily: XRP's 904 days without trading from 2021-01-20 fall outside every window.

### Hourly grids (all 10 coins pooled; each cell: dip / random)

**% reaching the target within 24 hours**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | 70 / 68 | 55 / 44 | 40 / 29 | 30 / 19 | 21 / 13 |
| -2% | 66 / 68 | 47 / 44 | 36 / 29 | 27 / 19 | 22 / 13 |
| -3% | 67 / 68 | 45 / 44 | 31 / 29 | 22 / 19 | 17 / 13 |
| -4% | 70 / 68 | 43 / 44 | 32 / 29 | 20 / 19 | 14 / 13 |
| -5% | 72 / 68 | 46 / 44 | 31 / 29 | 21 / 19 | 15 / 13 |

**% reaching the target within 30 days**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | 92 / 93 | 86 / 86 | 78 / 81 | 73 / 76 | 67 / 72 |
| -2% | 91 / 93 | 84 / 86 | 77 / 81 | 70 / 76 | 64 / 72 |
| -3% | 92 / 93 | 85 / 86 | 77 / 81 | 71 / 76 | 64 / 72 |
| -4% | 91 / 93 | 83 / 86 | 77 / 81 | 72 / 76 | 66 / 72 |
| -5% | 91 / 93 | 82 / 86 | 78 / 81 | 71 / 76 | 65 / 72 |

**Median hours to the target, among those reaching it within 30 days**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | 6 / 8 | 12 / 24 | 24.5 / 46 | 37 / 71 | 66 / 97 |
| -2% | 7 / 8 | 18 / 24 | 36.5 / 46 | 56 / 71 | 107 / 97 |
| -3% | 7 / 8 | 23 / 24 | 54 / 46 | 122 / 71 | 163 / 97 |
| -4% | 6 / 8 | 26.5 / 24 | 48 / 46 | 113 / 71 | 188 / 97 |
| -5% | 5 / 8 | 23 / 24 | 47 / 46 | 86 / 71 | 155 / 97 |

**Average result per trade after costs, % (0.50% fee + 0.05% slippage per side)**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | -1.91 / -1.75 | -2.38 / -2.32 | -2.92 / -2.58 | -3.15 / -2.67 | -3.52 / -2.70 |
| -2% | -2.10 / -1.75 | -2.86 / -2.32 | -3.36 / -2.58 | -3.85 / -2.67 | -4.14 / -2.70 |
| -3% | -1.86 / -1.75 | -2.71 / -2.32 | -3.33 / -2.58 | -3.72 / -2.67 | -4.03 / -2.70 |
| -4% | -2.11 / -1.75 | -2.93 / -2.32 | -3.38 / -2.58 | -3.69 / -2.67 | -4.21 / -2.70 |
| -5% | -2.01 / -1.75 | -3.14 / -2.32 | -3.45 / -2.58 | -3.95 / -2.67 | -4.29 / -2.70 |

**Median % it fell below the entry price before reaching the target (or by 30 days)**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | 1 / 1 | 2 / 2 | 4 / 4 | 5 / 5 | 8 / 6 |
| -2% | 1 / 1 | 3 / 2 | 5 / 4 | 7 / 5 | 9 / 6 |
| -3% | 1 / 1 | 3 / 2 | 5 / 4 | 8 / 5 | 9 / 6 |
| -4% | 1 / 1 | 3 / 2 | 5 / 4 | 8 / 5 | 10 / 6 |
| -5% | 1 / 1 | 3 / 2 | 5 / 4 | 8 / 5 | 9 / 6 |

Dip events (pooled): -1%: 838, 498, 362, 302, 256; -2%: 788, 430, 339, 279, 242; -3%: 771, 422, 309, 258, 229; -4%: 640, 386, 292, 241, 208; -5%: 576, 344, 278, 222, 191 (for targets +1% to +5%).
Random starts (pooled): 86,780. Coins (of 10) where dips reached the target within 24 hours more often than random: -1%: 6, 9, 10, 9, 8; -2%: 4, 5, 8, 8, 8; -3%: 4, 3, 5, 7, 7; -4%: 4, 5, 7, 4, 6; -5%: 8, 6, 6, 6, 5.

### Daily grids (all 10 coins pooled; each cell: dip / random)

**% reaching the target within 1 day (the entry day)**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | 77 / 74 | 60 / 54 | 46 / 39 | 36 / 28 | 28 / 21 |
| -2% | 79 / 74 | 61 / 54 | 45 / 39 | 35 / 28 | 27 / 21 |
| -3% | 80 / 74 | 61 / 54 | 45 / 39 | 34 / 28 | 26 / 21 |
| -4% | 83 / 74 | 66 / 54 | 50 / 39 | 37 / 28 | 28 / 21 |
| -5% | 86 / 74 | 69 / 54 | 52 / 39 | 38 / 28 | 30 / 21 |

**% reaching the target within 30 days**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | 96 / 95 | 92 / 91 | 88 / 87 | 85 / 83 | 82 / 79 |
| -2% | 96 / 95 | 92 / 91 | 88 / 87 | 85 / 83 | 82 / 79 |
| -3% | 96 / 95 | 92 / 91 | 88 / 87 | 85 / 83 | 82 / 79 |
| -4% | 97 / 95 | 92 / 91 | 88 / 87 | 85 / 83 | 81 / 79 |
| -5% | 97 / 95 | 93 / 91 | 89 / 87 | 85 / 83 | 81 / 79 |

**Median days to the target, among those reaching it within 30 days**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | 1 / 1 | 1 / 1 | 1 / 2 | 2 / 2 | 2 / 3 |
| -2% | 1 / 1 | 1 / 1 | 1 / 2 | 2 / 2 | 2 / 3 |
| -3% | 1 / 1 | 1 / 1 | 1 / 2 | 2 / 2 | 3 / 3 |
| -4% | 1 / 1 | 1 / 1 | 1 / 2 | 2 / 2 | 2 / 3 |
| -5% | 1 / 1 | 1 / 1 | 1 / 2 | 2 / 2 | 2 / 3 |

**Average result per trade after costs, % (0.50% fee + 0.05% slippage per side)**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | -1.08 / -1.21 | -1.02 / -1.20 | -1.07 / -1.21 | -0.85 / -1.17 | -0.66 / -1.09 |
| -2% | -0.98 / -1.21 | -1.03 / -1.20 | -0.95 / -1.21 | -0.81 / -1.17 | -0.73 / -1.09 |
| -3% | -1.00 / -1.21 | -1.06 / -1.20 | -1.03 / -1.21 | -0.81 / -1.17 | -0.67 / -1.09 |
| -4% | -0.92 / -1.21 | -0.95 / -1.20 | -0.98 / -1.21 | -1.00 / -1.17 | -1.02 / -1.09 |
| -5% | -0.84 / -1.21 | -0.78 / -1.20 | -0.94 / -1.21 | -0.93 / -1.17 | -1.01 / -1.09 |

**Median % it fell below the entry price before reaching the target (or by 30 days)**

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | 3 / 3 | 3 / 3 | 4 / 4 | 5 / 5 | 5 / 5 |
| -2% | 3 / 3 | 3 / 3 | 4 / 4 | 5 / 5 | 5 / 5 |
| -3% | 3 / 3 | 4 / 3 | 4 / 4 | 5 / 5 | 6 / 5 |
| -4% | 3 / 3 | 4 / 3 | 4 / 4 | 5 / 5 | 6 / 5 |
| -5% | 3 / 3 | 4 / 3 | 4 / 4 | 5 / 5 | 6 / 5 |

Dip events (pooled): -1%: 5647, 4010, 3045, 2639, 2329; -2%: 5226, 3753, 2973, 2539, 2207; -3%: 4461, 3305, 2658, 2307, 2042; -4%: 3732, 2878, 2350, 2021, 1798; -5%: 3014, 2438, 2025, 1769, 1584 (for targets +1% to +5%).
Random starts (pooled): 24,963. Coins (of 10) where dips reached the target within 1 day more often than random: -1%: 10, 10, 9, 10, 10; -2%: 10, 10, 10, 10, 10; -3%: 10, 9, 10, 9, 10; -4%: 10, 10, 10, 10, 10; -5%: 10, 10, 10, 10, 10.

### Per coin, -3% dip / +3% target, hourly (each cell: dip / random)

| Coin | Dip events | Within 24 h % | Within 30 days % | Median hours | Average after costs % | Fell further first: median / worst % |
|---|---|---|---|---|---|---|
| BTC | 27 | 11 / 14 | 79 / 76 | 73 / 75 | -1.80 / -2.54 | -2.7 / -35.2 |
| ETH | 32 | 19 / 25 | 82 / 82 | 81 / 48 | -1.87 / -2.77 | -4.5 / -47.0 |
| SOL | 27 | 26 / 30 | 75 / 81 | 57.5 / 39 | -4.84 / -2.53 | -10.8 / -53.3 |
| XRP | 27 | 41 / 27 | 72 / 82 | 13.5 / 65 | -3.55 / -2.02 | -2.8 / -39.2 |
| DOGE | 29 | 41 / 30 | 69 / 76 | 20.5 / 39 | -4.30 / -3.07 | -6.2 / -38.3 |
| ADA | 36 | 33 / 36 | 76 / 82 | 32 / 35 | -3.89 / -3.49 | -4.9 / -46.5 |
| AVAX | 33 | 36 / 33 | 78 / 81 | 61 / 37 | -3.75 / -2.93 | -8.0 / -47.9 |
| LINK | 32 | 34 / 32 | 78 / 86 | 81 / 41 | -2.91 / -1.70 | -6.8 / -48.5 |
| LTC | 30 | 33 / 24 | 72 / 79 | 39 / 58 | -3.12 / -2.20 | -2.9 / -43.6 |
| DOT | 36 | 31 / 35 | 83 / 82 | 31 / 36 | -3.36 / -2.51 | -4.3 / -51.4 |
| All pooled | 309 | 31 / 29 | 77 / 81 | 54 / 46 | -3.33 / -2.58 | -5.0 / -53.3 |

### Per coin, -3% dip / +3% target, daily (each cell: dip / random)

| Coin | Dip events | Within 1 day % | Within 30 days % | Median days | Average after costs % | Fell further first: median / worst % |
|---|---|---|---|---|---|---|
| BTC | 267 | 34 / 27 | 86 / 86 | 2 / 3 | -0.70 / -0.80 | -2.9 / -100.0 |
| ETH | 371 | 45 / 38 | 89 / 87 | 1 / 2 | -0.75 / -1.36 | -3.6 / -100.0 |
| SOL | 258 | 54 / 47 | 91 / 88 | 1 / 1 | -0.58 / -1.33 | -4.1 / -70.4 |
| XRP | 174 | 40 / 32 | 86 / 87 | 2 / 2 | -1.18 / -0.75 | -5.3 / -69.4 |
| DOGE | 226 | 46 / 40 | 88 / 85 | 1 / 2 | -0.94 / -1.49 | -4.8 / -52.5 |
| ADA | 204 | 49 / 41 | 84 / 85 | 1 / 2 | -1.79 / -1.67 | -5.2 / -48.7 |
| AVAX | 196 | 47 / 45 | 86 / 86 | 1 / 1 | -2.10 / -2.01 | -4.6 / -62.5 |
| LINK | 345 | 50 / 47 | 90 / 90 | 1 / 1 | -0.66 / -0.82 | -4.6 / -65.2 |
| LTC | 413 | 44 / 40 | 90 / 88 | 2 / 2 | -0.75 / -0.85 | -4.3 / -66.9 |
| DOT | 204 | 41 / 40 | 85 / 85 | 2 / 2 | -2.01 / -1.73 | -4.9 / -51.0 |
| All pooled | 2658 | 45 / 39 | 88 / 87 | 1 / 2 | -1.03 / -1.21 | -4.4 / -100.0 |

### Equal pairs: the two halves of the hourly year (pooled; each cell: dip / random)

| Pair | Oct-Apr: within 24 h % | Oct-Apr: within 30 days % | Oct-Apr: average after costs % | Apr-Oct: within 24 h % | Apr-Oct: within 30 days % | Apr-Oct: average after costs % | Dip events Oct-Apr / Apr-Oct |
|---|---|---|---|---|---|---|---|
| -1% / +1% | 67 / 70 | 88 / 92 | -3.04 / -1.93 | 72 / 67 | 96 / 93 | -1.00 / -1.55 | 314 / 524 |
| -2% / +2% | 40 / 47 | 77 / 85 | -4.98 / -2.69 | 51 / 41 | 89 / 87 | -1.11 / -1.88 | 171 / 259 |
| -3% / +3% | 24 / 32 | 68 / 80 | -5.89 / -3.14 | 36 / 26 | 85 / 82 | -0.96 / -1.91 | 130 / 179 |
| -4% / +4% | 16 / 21 | 62 / 74 | -6.37 / -3.47 | 24 / 17 | 82 / 79 | -0.89 / -1.72 | 109 / 132 |
| -5% / +5% | 8 / 14 | 55 / 69 | -7.11 / -3.74 | 21 / 11 | 78 / 75 | -0.96 / -1.47 | 91 / 100 |

### Equal pairs: conservative check and the 1.20% fee (pooled; each cell: dip / random)

| Data | Pair | Conservative: within 24 h or 1 day % | Conservative: within 30 days % | Conservative: average after 0.50% costs % | Touch, average after 1.20% costs % |
|---|---|---|---|---|---|
| hourly | -1% / +1% | 62 / 57 | 87 / 89 | -2.24 / -1.98 | -3.27 / -3.12 |
| hourly | -2% / +2% | 40 / 35 | 78 / 83 | -3.24 / -2.44 | -4.21 / -3.67 |
| hourly | -3% / +3% | 24 / 22 | 73 / 78 | -3.53 / -2.59 | -4.68 / -3.93 |
| hourly | -4% / +4% | 17 / 15 | 68 / 73 | -4.00 / -2.59 | -5.03 / -4.02 |
| hourly | -5% / +5% | 12 / 10 | 62 / 69 | -4.38 / -2.60 | -5.62 / -4.05 |
| daily | -1% / +1% | 38 / 37 | 85 / 85 | -0.34 / -0.67 | -2.45 / -2.58 |
| daily | -2% / +2% | 29 / 27 | 82 / 81 | -0.20 / -0.57 | -2.40 / -2.58 |
| daily | -3% / +3% | 22 / 20 | 79 / 78 | -0.09 / -0.51 | -2.41 / -2.59 |
| daily | -4% / +4% | 18 / 14 | 75 / 74 | -0.19 / -0.46 | -2.38 / -2.54 |
| daily | -5% / +5% | 12 / 10 | 71 / 70 | -0.15 / -0.39 | -2.38 / -2.47 |

**Daily, conservative check: average result per trade after costs, % (0.50% fee + 0.05% slippage per side).** Added after seeing the results, because the summary depends on it; the plan fixed only the equal pairs for this table.

| Drop \ target | +1% | +2% | +3% | +4% | +5% |
|---|---|---|---|---|---|
| -1% | -0.34 / -0.67 | -0.17 / -0.57 | +0.05 / -0.51 | +0.15 / -0.46 | +0.31 / -0.39 |
| -2% | -0.35 / -0.67 | -0.20 / -0.57 | +0.04 / -0.51 | +0.17 / -0.46 | +0.30 / -0.39 |
| -3% | -0.41 / -0.67 | -0.23 / -0.57 | -0.09 / -0.51 | +0.14 / -0.46 | +0.33 / -0.39 |
| -4% | -0.56 / -0.67 | -0.43 / -0.57 | -0.35 / -0.51 | -0.19 / -0.46 | +0.06 / -0.39 |
| -5% | -0.54 / -0.67 | -0.66 / -0.57 | -0.49 / -0.51 | -0.44 / -0.46 | -0.15 / -0.39 |

### Daily by calendar year, -3% dip / +3% target (pooled; each cell: dip / random)

| Year | BTC's change in the year % | Dip events | Within 1 day % | Within 30 days % | Average after costs % |
|---|---|---|---|---|---|
| 2017 | +1324 | 157 | 55 / 48 | 94 / 96 | +0.51 / +0.90 |
| 2018 | -73 | 83 | 42 / 41 | 75 / 76 | -5.18 / -5.66 |
| 2019 | +94 | 152 | 44 / 36 | 86 / 86 | -1.75 / -1.20 |
| 2020 | +305 | 255 | 49 / 41 | 95 / 93 | +0.16 / +0.38 |
| 2021 | +59 | 369 | 60 / 55 | 92 / 91 | -0.57 / -0.72 |
| 2022 | -64 | 320 | 42 / 42 | 84 / 86 | -2.40 / -2.30 |
| 2023 | +156 | 379 | 44 / 31 | 90 / 86 | +0.21 / -0.49 |
| 2024 | +121 | 366 | 48 / 39 | 87 / 88 | -1.00 / -0.53 |
| 2025 | -6 | 353 | 42 / 40 | 86 / 87 | -1.36 / -1.05 |
| 2026 (to 11 Oct) | -4 | 224 | 22 / 26 | 84 / 81 | -2.05 / -2.62 |

Price change over the hourly year (2025-10-09 to 2026-10-08): BTC -34%, ETH -45%, SOL -52%, XRP -52%, DOGE -67%, ADA -72%, AVAX -65%, LINK -44%, LTC -47%, DOT -74%.

## Correction and fee arithmetic (2026-11-08T00:58:44Z, Claude, after the owner questioned the fees)
- **Mistake:** the main rule sells with a resting limit order, yet the sale was charged the taker fee (0.50%) plus
  slippage. The account's maker rate is 0.25% (`RESEARCH_BRIEF.md` line 556: 0.25% maker / 0.50% taker, read from the
  account on 2026-10-08). The fee levels themselves were the account's taker rate and the repo's 1.20% stress level.
- **Recomputed exactly from the reported averages** (the cost is a constant factor per trade, so average before costs
  = (1 + average after costs) / 0.98906 - 1). Main rule, pooled:

| Cost assumption | Hourly dips | Hourly random | Daily dips | Daily random |
|---|---|---|---|---|
| As run: 0.50% + 0.05% slippage both sides | -1.86% to -4.29%; 0 of 25 above zero | -1.75% to -2.70%; 0 of 25 | -0.66% to -1.08%; 0 of 25 | -1.09% to -1.21%; 0 of 25 |
| Buy 0.50% + slippage, sell 0.25% maker, no slippage (also applied to 30-day exits, so optimistic) | -1.56% to -4.00%; 0 of 25 | -1.46% to -2.41%; 0 of 25 | -0.36% to -0.78%; 0 of 25 | -0.80% to -0.92%; 0 of 25 |
| No fees and no slippage | -0.77% to -3.23%; 0 of 25 | -0.67% to -1.62%; 0 of 25 | +0.02% to +0.44%; 25 of 25 | -0.12% to 0.00%; 0 of 25 |

- **On $5,000, -3% dip, +5% target** (derived from the same figures):
  - Hourly: 64.5% of 200 trades reached +5% and kept $194 each after 0.50% costs. The rest were sold after 30 days at
    an average of -18.3%, about -$922 each. Average -$202 per trade, or -$148 with no fees.
  - Daily: 82.2% of 2,018 trades reached +5% (+$194 each). The rest averaged -21.5%, about -$1,082. Average -$33
    per trade, or +$22 with no fees.
- **Conclusions:** none change. The losses come mainly from trades that miss the target and are held 30 days, not
  from fees. Fees decide the outcome only for +1% targets, which are smaller than the cost of a buy and a sell, and
  for the daily dips, which are slightly positive before costs.

## Rising and falling years, daily main rule (2026-11-08T01:05:16Z, Claude, after the owner said the data cover a crash period)
- Added at the owner's prompt, after seeing the results. Script `split_up_down_years.py` (sha256 `35786bfb...`), which
  uses `describe.py`'s own functions on the same hash-checked daily files.
- This is a **hindsight split**: trades are grouped by the calendar year they started in, and a year's direction is
  known only after it ends.
- The hourly year (2025-10-09 to 2026-10-08) is the newest data in the repository, and every coin fell over it. It
  cannot be split this way.

| Years (by BTC's calendar-year change) | Cost | Dips: range per trade; combinations above zero | Random: range; above zero |
|---|---|---|---|
| Rising: 2017, 2019, 2020, 2021, 2023, 2024 | 0.50% + slippage both sides | -0.86% to +0.48%; 10 of 25 | -0.94% to +0.08%; 5 of 25 |
| Rising | 0.25% maker sale | -0.56% to +0.78%; 13 of 25 | -0.64% to +0.38%; 10 of 25 |
| Rising | No fees | +0.24% to +1.59%; 25 of 25 | +0.16% to +1.19%; 25 of 25 |
| Falling: 2018, 2022, 2025, 2026 | 0.50% + slippage both sides | -3.41% to -0.81%; 0 of 25 | -2.66% to -1.57%; 0 of 25 |
| Falling | 0.25% maker sale | -3.12% to -0.51%; 0 of 25 | -2.37% to -1.28%; 0 of 25 |
| Falling | No fees | -2.34% to +0.29%; 2 of 25 | -1.59% to -0.49%; 0 of 25 |

- **-3% dip / +5% target in rising years:**
  - 1,312 trades; 86.8% reached the target within 30 days.
  - Average per trade: +0.48% at 0.50% both sides, +0.78% with a maker sale, +1.59% with no fees.
  - Random starts: 82.6% reached the target; +0.08% per trade.
- **The same pair in falling years:** 706 trades, 73.7% reached the target, -2.79% per trade.
- **Limits:** no significance test, the same clustering limits as above, and the split uses hindsight.

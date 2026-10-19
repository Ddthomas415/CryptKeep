# Lower-value top-100 coins and emerging entrants: actual screen results

## Economic answer

SHOWN by the frozen calculation: new top-100 entrants have the strongest
historical average here, but it is concentrated and does not establish an edge.
Low token price by itself is a much weaker discriminator. BTC/ETH were not
purchased. This does not establish that either asset has reached a price peak.

These are MODELLED CMC-reference-price outcomes, not exchange fills. Each row
summarizes 100 independent, fully funded USD1,000 four-week basket cycles. They
are not monthly income, compounded account values or sums of unlimited trades.
Selection 2019-01-06..2026-08-09; entry 2019-01-13..2026-08-16; final exit
2026-09-13. Archive extends to 2026-10-04; its last weeks cannot form another
full cycle on the fixed calendar. Archive: 414 weekly snapshots, 394 unique
eligible assets across all baskets, not today's survivors only.

| Fixed basket | Unique IDs | Mean net dollars/cycle | Median | Worst | Positive cycles |
|---|---:|---:|---:|---:|---:|
| Top 100, token price below USD1 | 264 | >= +28.11* | >= -48.36* | >= -399.98* | >= 44/100* |
| Raw CMC ranks 51..100 | 360 | >= +15.53* | >= -34.86* | >= -441.57* | >= 44/100* |
| New top-100 entrants after four observed outside weeks | 108 | +139.05 | -1.25 | -528.27 | 29/100 |
| Broad eligible top-100 altcoin control | 394 | >= +17.12* | >= -25.96* | >= -420.29* | >= 44/100* |

Primary friction: 0.50% fee plus 0.25% adverse price each side, fee-inclusive
entry sizing. These are scenario assumptions, not measured execution costs.
At the fixed 1.20% fee stress, mean dollars/cycle are >=+13.83, >=+1.42,
+126.13 and >=+2.99 respectively. No thresholds were optimized from these results.

*There are unknown exits: 9 low-price selections, 7 ranks-51..100 selections,
11 control selections. Their entire allocated value is assigned ZERO only for
the displayed conservative bound. This is not an asserted liquidation or loss.
Some disappearances correspond to token migrations; no conversion rights were
invented. Full-series means/medians/worst values are lower bounds, not complete
point estimates. Entry-price gaps (2, 2, 0, 4 respectively) retain their assigned
cash. All these rows remain in results.json; no failed constituent was dropped.

## What the prospect result actually means

The entrant basket invested in 79 cycles and held cash in 21. Of the funded
cycles, 29 were profitable and 50 lost; the funded-cycle median was -USD94.48.
One cycle (HEX, CMC ID5015, entry 2020-04-05) contributed +USD9,254.81 to its
USD1,000 reference-price basket. Other large cycles included ZEC (2025-09-14,
+USD4,115.07), TFUEL (2021-03-07, +USD1,761.60), SEI (2023-12-10,
+USD1,536.70) and FARTCOIN (2025-03-30, +USD1,368.18).
These are retrospective attribution, NOT advance picks or current buy advice.
Historical venue access, CMC classification changes and corporate actions are
not independently verified. No claim that these gains could have been filled.

Removing only the single largest cycle as a concentration diagnostic, NOT a new
trading rule, reduces the remaining 99-cycle mean to +USD46.97. This post-result
diagnostic is not another preferred backtest. The worst cycles include ZIL
(2022-04-03, -USD528.27) and CRV/SKYAI (2026-06-21, -USD459.89).

Calendar-block 95% interval for the entrant mean: -USD29.14 to +USD388.00.
Versus the control on 90 jointly valued cycles: mean +USD141.65, 95% interval
-USD24.43..+USD407.88; conservative simultaneous interval across three
comparisons -USD48.24..+USD474.01. Cheap-token/control differences and
ranks-51..100/control differences also have intervals crossing zero. Statistical
advantage is UNVERIFIED. Conditional comparisons exclude 10 incomplete control
cycles, explicitly, and cannot remove missingness/selection bias.

## Chronological stability

| Basket | 2019..2022: 52 cycles, mean dollars | 2023 onward: 48 cycles, mean dollars |
|---|---:|---:|
| Under USD1 | >= +52.80 | >= +1.37 |
| Ranks 51..100 | >= +40.52 | >= -11.54 |
| New entrants | +185.82 | +88.37 |
| Broad altcoin control | >= +34.69 | >= -1.90 |

Both segments are historical exploratory analysis, not untouched confirmation.
Positive average entrant outcomes in both segments warrant investigation, not
a conclusion of dependable income. Median entrant cycles are -USD35.44 and
USD0.00 including cash, and segment intervals also cross zero.

## Exact design, reproducibility and limits

[PROTOCOL.md](PROTOCOL.md) was frozen before returns, SHA256
`f232050036723229ae9a0fbbc505d1a3df2f0318cd2b13dc12eb92955b1ebf01`.
The three arms, four-week holding period, seven-day entry delay and cost levels
were not changed after observing results. No present-day symbol whitelist or
BTC regime filter; identities are numeric CMC IDs. Stable/wrapped/tokenized
tag filters and near-dollar heuristic are imperfect and may miss wrappers or
exclude a nonstable coin near USD1. CMC rank is not pure market-cap sorting.
CMC reference prices aggregate exchanges and cannot establish executable depth,
Coinbase availability, observed spread or historical action-adjusted returns.
Archived labels may be retrospectively revised. Seven-day delayed entry does
not independently prove when an historical page was first available.

Three hypotheses, one horizon, plus one common control; 3,900 / 4,299 / 134
selection exposures respectively. These selections are not independent trials.
The control has 8,418 selections. Distinct asset union 394; entire prior project
effective trial count remains unresolved. Bootstrap is calendar-blocked,
4-cycle blocks, 4,000 repetitions, fixed seed; no defensible DSR claimed.
No higher-frequency pattern, short sale or fundamental growth model was tested.
No user trading capital or funding commitment is inferred from USD1,000 examples.

VERIFIED_ENV commands (repo-local Python 3.12):

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_low_value_top100.py tests/test_symbol_coverage_registry.py
./.venv/bin/python -B scripts/research/test_low_value_top100.py --archive docs/research/raw_archives_20261009/cmc_weekly_and_trending.tar.xz --input-manifest docs/research/raw_archives_20261009/SHA256SUMS_inputs.txt --protocol docs/research/low_value_top100_20261018/PROTOCOL.md --output /tmp/low_value_top100_replay.json
```

The output path must not exist; the script refuses to overwrite evidence. Replay
should match after removing only provenance.created_utc. Full suite not run.
Initial synthetic test run found an empty-segment summarization error (1 failed,
15 passed); fixed before the sole historical run, 16 then passed. This was not a
rule change. Source hash `388dc98a...`, result hash `fc4acf23...`; full hashes in
the receipt. `by_asset.csv` preserves 1,126 arm/CMC-ID diagnostic rows, including
conditional known-return summaries and unknown-exit counts, not selected winners.

Implementation disposition pending separate review: READY_FOR_INDEPENDENT_REVIEW.
Research conclusion: INCOMPLETE as an executable/profitable strategy. Scope and
existing per-symbol acceptance states remain intact; basket coverage only.

## Recommendation

Continue the lower-cap/emerging universe, with verified new-top-100-entry events
as the strongest lead from THIS screen. Before another strategy run, audit the
largest historical events against venue-specific identity/action-adjusted price
and liquidity evidence. Do not retune this rule on its winning coins. Merely
being below USD1 is not supported as a reliable growth-selection edge here.

Primary methodology sources consulted:
[CMC price calculation](https://support.coinmarketcap.com/hc/en-us/articles/360015968632-How-are-prices-calculated-on-CoinMarketCap),
[CMC market data, capitalization and rank](https://support.coinmarketcap.com/hc/en-us/articles/360034116491-Market-Data).

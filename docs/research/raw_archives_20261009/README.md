# Frozen raw inputs for the 2026-10-09 strategy research

These are the exact input files the research scripts read, exported from the cloud workspace on 2026-10-09.
A new download would not reproduce them. Research data only; no keys, no account data.

## Reproduce

Extract every archive into ONE empty folder (call it `S`); the folder names inside (`cb/`, `bn/`, ...) are the
layout the scripts expect. Then run a script with that folder as its argument, e.g.
`python3 docs/research/top10_trend_20261009/top10.py S > top10.json`, and compare with the committed JSON.
Check integrity first: `sha256sum -c SHA256SUMS_archives.txt`, then after extracting,
`cd S && sha256sum -c ../SHA256SUMS_inputs.txt` (2,377 input files).

| Archive | Folder | Contents | Used by |
|---|---|---|---|
| coinbase_hourly_last60d.tar.xz | cb/ | Coinbase hourly candles, 395 USD products, last 60 days to 2026-10-08 (`h1/*.json`: ts, open, high, low, close, volume) + run outputs | sim.py, short_hold.py, fwd.py, search.py, candidate.py |
| coinbase_hourly_prior10m.tar.xz | cb2/ | Coinbase hourly candles, the 10 months before that | sim_earlier_10_months.py, short_hold/fwd on the earlier window |
| blast_vara.tar.xz | bv/ | BLAST-USD and VARA-USD hourly and daily | events.py |
| binance_daily_current484.tar.xz | bn/ | Binance daily USDT pairs trading on 2026-10-09 (484), since 2019-01-01 (`d1/*.json`: ts_s, open, high, low, close, quote volume) + run outputs | hybrid.py, recovery.py, recovery_regime.py, ideas.py |
| binance_daily_all_incl_delisted.tar.xz | bn_all/ | Binance daily, all 677 USDT pairs ever listed incl. delisted, since 2017-08-01 | top10.py |
| coinbase_btc_eth_daily.tar.xz | maj/ | Coinbase BTC-USD and ETH-USD daily since 2015/2016 + majors.json, stress.json | majors.py, stress_btc_eth.py |
| cmc_weekly_and_trending.tar.xz | cmc/ | CoinMarketCap weekly top-1000 snapshots 2018-11-04..2026-10-04 (414 files) + trending lists of 2026-10-09 | cmc_trend.py, trending_deepdive.py |

## Known gaps

- `rerun_with_jup_super_syrup_20261009` used `bn/d1` plus `JUPUSDT.json` and `SYRUPUSDT.json` copied from `bn_all/d1`
  (SUPERUSDT was already present). Rebuild that folder the same way; it is not archived separately.
- `trending_deepdive.py` fetched each coin's CMC daily history live and did not save it; only its computed output
  (`trending_deepdive.json`) is frozen. That step cannot be reproduced byte-for-byte.
- Scripts were run with Python 3.13 and numpy in the cloud workspace; the laptop has Python 3.10.

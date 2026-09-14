# ES Intraday Coverage Assessment

Active role: AUDITOR. Read-only archive/journal inspection; no backfill or replay.

## SHOWN Coverage

Matched six distinct qualified order IDs to journal timestamps, verified
alternating buy/sell order. Counts include the candle containing entry and exit
(floored UTC timestamps), not a claim that its full price range was observable
at the exact fill time. All data below is Coinbase BTC/USDT.

| Trade window (UTC) | 5m present / expected | Missing 5m | 1h present / expected |
| --- | ---: | ---: | ---: |
| June 16 00:50:55 - June 18 00:04:00 | 552 / 567 | 15 | 0 / 49 |
| June 21 00:04:06 - June 24 00:04:01 | 780 / 865 | 85 | 0 / 73 |
| July 4 00:31:05 - July 9 00:04:00 | 1148 / 1435 | 287 | 121 / 121 |

5m inventory: 12000 rows from June 1 to July 17 09:10 UTC; 1022 gap intervals,
1359 absent grid timestamps between endpoints. No duplicate/off-grid timestamps.
1h inventory: 662 contiguous rows July 1 through July 28 13:00 UTC.
Missing timestamps establish archive coverage gaps, not their cause. Venue
no-trade candle omission versus collection failure has not been established.

Neither intraday series has 210 days of pre-entry history. That is an inventory
observation, not a requirement to warm up a daily SMA with intraday bars.
Previously verified daily BTC/USD history can support a separately labeled
proxy warmup, but must not be silently treated as same-symbol BTC/USDT data.

## Decision

Exact historical runner replay is unsupported by this archive. Even complete
OHLC candles would not recover within-bar ordering, partial daily observations,
actual loop timing, or persisted trailing-peak state. A 60-loop limit is not
a 60-candle limit. Complete hourly coverage for July does not change that.

Recommended next action: bounded public-source re-fetch of the missing 5m
intervals into a separate research artifact, compare timestamps without
overwriting the archive, and classify remaining omissions. Do not fabricate or
forward-fill missing prices. Only then consider explicitly labeled bar-close
sensitivity bounds; these cannot be described as actual historical exits.
No reason is established here to restart campaigns or alter their evidence.

## Reproduction

Artifact directory: .cbp_state/data/research/es_intraday_coverage/20260908/.
es_intraday_coverage_20260908.json SHA256:
39082fdf36b07c9b8da7d917d9ed7785658327b7f9a0ede7df51b535bc330050.
es_intraday_coverage_20260908.py SHA256:
680340eef1da887bc4ea2dce55003808743950ede7fd56b2eeab8a091462859b.
Script contains exact six order IDs, opens both databases mode=ro, records row
hashes and gap intervals. Ran twice with local venv; cmp returned 0 (identical).
No runtime source changed; full suite not rerun for this bounded data audit.

Acceptance state: ACCEPTED for coverage assessment; exact replay UNVERIFIED.

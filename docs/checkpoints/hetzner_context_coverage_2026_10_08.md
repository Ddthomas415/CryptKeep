# Hetzner context collector coverage checkpoint

2026-10-08 approximately 15:08 UTC / 11:08 AM New York. AUDITOR.
Objective: resolve E03 addendum 3's host-context unknowns without changing runtime
or reopening FC-01. VERIFIED_ENV: actual host, read-only SQLite transaction.

## SHOWN

- System service cbp-crypto-edge-collector.service active/running, PID 1585033,
  started October 1 06:03:13 UTC; system cbp-edge-cadence.timer active/waiting.
- Same-named user units are inactive. Do not mistake their status for the actual
  system service. No service restarted.
- Existing collector command uses live_collector_plan.json, 300-second interval,
  live_public source. Archive /var/lib/cbp/data/crypto_edge_research.sqlite.
- Timestamp-only archive inspection establishes these actual series:

| Series | Venue / symbol | Rows | First capture UTC |
| --- | --- | ---: | --- |
| Funding | OKX BTC/USDT:USDT | 21958 | July 18 20:25:49 |
| Basis | OKX BTC/USDT:USDT | 21958 | July 18 20:25:49 |
| Open interest | OKX BTC/USDT:USDT | 21949 | July 18 21:16:48 |
| Quotes | Coinbase BTC/USD | 22565 | July 18 20:25:49 |
| Quotes | Kraken BTC/USD | 22567 | July 18 20:25:49 |
| Order book | Coinbase BTC/USD | 22558 | July 18 21:16:48 |

All series latest capture October 8 15:05:26 UTC, about 198.5 seconds old at
query time. All have 1929 distinct capture timestamps in the trailing seven-day
window; no gaps over an hour; largest interval 325 seconds, including window
edges. Rows were read in one mode=ro transaction, grouped by venue/symbol/source
and duplicate timestamps removed for cadence analysis.

This establishes recent observed cadence and series presence, not continuous
coverage since July, feed validity, sequence completeness, exchange-event latency,
executable liquidity or alpha. No bid/ask/funding/return values were inspected.
Five-minute snapshots cannot support subsecond execution research by themselves.

## Economic consequence

The host has a confirmed context-research role beyond the ES trial. Operator's
approximately 20 USD/month estimate is a platform cost, not automatically an ES
incremental expense. Report total platform cost and explicitly justified allocation
or incremental cost separately. Marginal cost was not measured; do not assume zero.

E03 decision remains the operator's. No capability removed, collector stopped,
campaign revised or closed FC-01 period reused. More host rows from a previously
examined period do not constitute untouched data.

Acceptance: ACCEPTED for this bounded read-only status/coverage checkpoint.
Economic efficacy remains INCOMPLETE. Next research action, if selected: a newly
registered question on appropriately separated data, with horizon/cost/coverage
requirements fixed before inspecting market outcomes. Existing ES endpoint stands.

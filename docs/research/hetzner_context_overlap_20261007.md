# Host context gap and entry-overlap measurement

Active role AUDITOR. Read-only direct SSH, VERIFIED_ENV. No new experiment.

## SHOWN: one read-only database snapshot

Source /var/lib/cbp/data/crypto_edge_research.sqlite, live_public only, grouped
by venue/symbol. Inter-capture gaps measured within each individual series.

| Series | Rows | Maximum gap | Gaps > 1 hour | Elapsed hours in those gaps |
| --- | ---: | ---: | ---: | ---: |
| OKX funding | 21,742 | 20,531 seconds | 16 | 49.486 |
| OKX basis | 21,742 | 20,531 seconds | 16 | 49.399 |
| OKX open interest | 21,733 | 20,531 seconds | 16 | 49.486 |
| Coinbase book | 22,342 | 646 seconds | 0 | 0 |
| Coinbase quote | 22,349 | 675 seconds | 0 | 0 |
| Kraken quote | 22,351 | 675 seconds | 0 | 0 |

Span approximately 1,943 hours from July 18 to October 7. Summed gap duration
includes normal inter-poll time: it is not an exact missing-data duration or
uptime percentage. Zero hour-long gaps does not mean continuous tick coverage.
Rows advanced between the earlier checkpoint and this snapshot.

## SHOWN: archived model timestamp, not an actual execution

Read daily_trend_recent_20260926/result.json, sma200_signal_only arm.
Five modelled buys: September 26, October 20/24, November 1 of 2025 and
August 20, 2026, all represented at 00:00 UTC. Four precede host coverage.
For the August 20 timestamp, a second read-only snapshot selects the latest
capture strictly before 2026-08-20T00:00:00Z per series. All six series return
2026-08-19T23:59:58Z, age 2 seconds. No future row substituted.

This corrects E02's laptop-only zero-overlap result to ONE capture-time-covered
modelled buy in the inspected artifact when host evidence is included.
It does not prove actual strategy decision time, local receive-time availability,
venue equivalence, historical fill costs, or a production replay. The artifact
explicitly excludes the runner's full regime/exit/risk stack. Daily-bar timestamp
semantics must be resolved before joining it to decision-time features.

## Disposition

E02 remains INSUFFICIENT EVIDENCE: one event cannot validate context filtering.
FC-01 stays closed; no parameter rescue or holdout reuse. Host collection has
demonstrated coverage value independent of the daily candidate's entry rate.
Next: reconstruct the archived model's bar/decision timing and full-rule mismatch
before any decision-time context comparison. Do not invent more observations
by calling every context snapshot an independent trade.

No code/tests/campaign/account/config changes. No tests run: this is measurement,
not a behavior fix. No profit, statistical qualification or capital authorization.

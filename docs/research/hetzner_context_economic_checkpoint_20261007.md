# Hetzner context evidence checkpoint - 2026-10-07

Active role: AUDITOR. Read-only, VERIFIED_ENV after direct SSH evidence.
Objective: resolve E03 Addendum 3 host-context unknowns without reopening FC-01.

## SHOWN

Documented runtime probe returned no blockers. Collector PID 1585033 is alive;
system service enabled/active, cadence timer enabled/active. Host checkout is
580ca31ea983af6452a1e02ab8d4b51645e9b43c, not the newly merged PR606 commit.
No deployment inferred or performed. Latest capture 2026-10-07T19:48:36Z.

Read-only SQLite connection, one transaction, grouped by source/venue/symbol:

| Family | Venue / symbol | live_public rows | Calendar dates |
| --- | --- | ---: | ---: |
| Funding | OKX BTC/USDT:USDT | 21,737 | 82 |
| Basis | OKX BTC/USDT:USDT | 21,737 | 82 |
| Open interest | OKX BTC/USDT:USDT | 21,728 | 82 |
| Book | Coinbase BTC/USD | 22,337 | 82 |
| Quote | Coinbase BTC/USD | 22,344 | 82 |
| Quote | Kraken BTC/USD | 22,346 | 82 |

Funding/basis/quotes begin July 18 at 20:25:49 UTC; OI/books begin
July 18 at 21:16:48 UTC. All end at the latest capture above.
82 dates is not proof of uninterrupted coverage or adequate effective samples.
The cadence checker reports derivative families fresh, but quote/book freshness
checks disabled. Actual latest rows for those families were independently read.

## Consequence and next action

E03's unknown whether the host records Coinbase books/quotes is resolved: yes.
Do not charge the whole shared-host bill to one strategy or dismiss context
collection because paper sessions do not trade. No profitability conclusion.
FC-01 stays closed. These rows are not declared an untouched holdout.
Next bounded research step: measure per-series gaps and as-of overlap with
candidate decisions before proposing any new experiment. Preserve the existing
October 13 trial deadline, strategy rules, fees, capital and accounts.
Actual infrastructure bill and current candidate outcomes remain separate inputs.

## Verification limits

No collector start/stop, account/config change, code change, deployment or
backtest. No tests run for this read-only inspection. Runtime JSON report and
read-only SQL results support only the claims above. Documentation checkpoint
complete; strategy/host economic decision remains INCOMPLETE.
PR606 merge-SHA desktop builds, sanity, governance and script-path checks pass;
main CI still in progress at final refresh, not reported as complete.

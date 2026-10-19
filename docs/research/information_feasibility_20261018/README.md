# Information evidence: feasibility count, not a strategy test

Observed October 18, 2026 at 20:19:59 New York (October 19 00:19:59 UTC).
Active role: AUDITOR. The count uses existing public evidence only. No strategy,
forecast, parameter selection, PnL calculation, live fetch or new collector ran.

## Answer

The existing Binance BTC/ETH funding file is the most substantial **available
input for a later bounded research design** among the inspected sources. That is
not a profitable-edge finding. The live context archive is BTC-only, has large
gaps and repeated polls, and cannot support claims of a broad multi-symbol or
latency-sensitive feed. A venue-incident comparison cannot yet be quantified:
there is no verified structured incident ledger in the inspected store or named
research outputs. Its event frequency is UNKNOWN, not zero or "rare".

This closes the missing evidence-count comparison, not the explanation-service
restoration or authorization for a new hypothesis. E7 and the existing carry
feasibility results remain unchanged. Previously seen history is not holdout.

## Shown counts

Source: `.cbp_state/data/crypto_edge_research.sqlite`, filtered to `live_public`.
The three funding fixtures, three basis fixtures and six quote fixtures labeled
`sample_bundle` are separately counted and excluded, not treated as observations.

| Recorded input | Venue / instrument | Valid rows | UTC days with data | Largest capture gap |
| --- | --- | ---: | ---: | ---: |
| Funding polls | OKX BTC/USDT:USDT | 13,781 | 87 | 8.96 days |
| Spot/perp basis price pairs | OKX BTC/USDT:USDT | 13,778 | 87 | 8.96 days |
| Open-interest polls | OKX BTC/USDT:USDT | 10,449 | 56 | 30.74 days |
| Bid/ask snapshots | Coinbase BTC/USD | 14,057 | 90 | 85.84 days |
| Bid/ask snapshots | Kraken BTC/USD | 14,053 | 90 | 85.84 days |
| Visible-book summaries | Coinbase BTC/USD | 10,449 | 57 | 30.74 days |

Funding/basis/OI first captures are July 11; Coinbase/Kraken quotes begin March
23 and book summaries July 2. All end at October 18 20:16:56 New York in this
snapshot. The 311-second median spacing is an observation, not a guaranteed
five-minute cadence. Funding and basis each have four gaps over 24 hours; OI
has six. Valid numeric rows do not prove valid instruments or timely exchange
observations. "Days with data" is not consecutive-day coverage.

At Coinbase quote capture times, **10,431 / 14,057 (74.2%)** have funding, basis
and OI captures at or before that time and no older than 300 seconds. This is a
diagnostic capture-time join, not market-data freshness approval. No future
match is allowed. Polling is sequential and no exchange/first-receive clocks
are established. The reference instruments also differ: Coinbase BTC/USD vs
OKX BTC/USDT perpetual. No USD/USDT conversion, simultaneous executable-price
claim or historical tradability proof follows.

The plan sets `days_to_expiry: 7` for its perpetual basis rows. This is a
configuration assumption, not verified expiry metadata. The count does not use
it for annualized carry. OI unit comparability and actual funding settlement
identity are not established by the live polling rows.

## Historical funding, separately counted

Source: `research/crash_brake_20261013/binance_funding_raw.jsonl`.

| Instrument | Distinct funding timestamps | Recorded range (UTC) | Missing mark-price rows | Before recorded E7 target window |
| --- | ---: | --- | ---: | ---: |
| BTCUSDT | 7,770 | 2019-09-10 to 2026-10-13 | 4,536 | 1,343 |
| ETHUSDT | 7,536 | 2019-11-27 to 2026-10-13 | 4,302 | 1,109 |

No duplicate timestamps or explicit download-error records appear in that file.
Median spacing is eight hours; no adjacent gap exceeds nine hours. These are
file-level counts, not authenticated venue/account payment records or proof
that the original fetch captured everything. Missing mark prices prevent
treating every rate as a fully valued historical execution/carry observation.
The December 2020 E7 boundary comes from the existing data-reuse record. Earlier
rows are outside that recorded target window, **not certified untouched data**.

## Boundaries and next decision

Two interpretation limits: `live_public` is a stored source label, not independent
source authentication; 300 seconds is a declared counting window, not a new
trading/risk threshold. Context coverage remains one underlying asset; the
project's 25-symbol mandate and symbol-status registry are unchanged.

Do not launch an indefinite incident study based on an unsupported event-rate
estimate. Before selecting that direction, establish a point-in-time incident
ledger with publication/first-receipt/revision and product identity. If choosing
funding instead, a later proposal must differ from E7/previous carry research,
freeze its economic question and costs, and disclose reuse. Nothing here
registers or authorizes either study. Service restoration remains separate.

## Reproduce without reopening the current database

`projection.json` contains only fixed public columns from all five tables,
read under one read-only SQLite transaction. The application store was not
instantiated (its initialization changes schema/WAL settings). `counts.json`
pins this projection, the original funding file and the exact counter script.
The source database continues to change; its live-file hash is not presented as
a frozen database identity. No immutable mode that ignores its WAL was used.

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m scripts.research.count_information_evidence \
  --projection docs/research/information_feasibility_20261018/projection.json \
  --funding research/crash_brake_20261013/binance_funding_raw.jsonl \
  --output /private/tmp/cryptkeep_information_feasibility_replay_NEW
```

The output path must be new. Original evidence and existing outputs are never
overwritten. Counts from a fresh database read may legitimately differ.
Targeted synthetic verification: 11 passed. Frozen replay matches every count,
source hash and capture field after sorting the descriptive group list by
table/venue/symbol. Group ordering changes when reading canonical JSON, so no
byte-identical replay claim is made. This is not a full-suite result.

## Independent disposition

Separate GATE reviewer Hegel (`01a15187-d8bb-71c1-8bfb-095bd45e4bac`) returned
ACCEPTED_WITH_RISK, no blockers for these frozen inputs/results. Without
importing the counter or reopening the current database, it recomputed every
numeric/date field, verified input/output hashes, confirmed no future matching
and reran the 11 tests (all passed). The original capture invocation remains
parent-observed proof, not an independently observed transaction.

Accepted limits: the historical parser coerces float/int rather than rejecting
all malformed boolean/fractional inputs; the exact frozen file was separately
validated as finite rates and positive integer timestamps. Basis tenor and
general mark-price validity are not established. The fixture read-only test
does not establish concurrent live-WAL sidecar behavior. Do not expand this
acceptance to arbitrary future inputs, annualized carry, payouts, trading or
operational readiness. Full review: `independent_review.md`.

These new outputs postdate the earlier recovery packages. They are not claimed
committed, pushed or covered by those old backup snapshots.

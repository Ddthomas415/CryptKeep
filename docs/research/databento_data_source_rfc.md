# Databento Data-Source RFC

Date: 2026-07-22

Status: proposed - research data-source design only. No implementation,
credential setup, package install, data purchase, campaign, promotion-gate, or
execution change is authorized by this document.

## Purpose

Databento may be useful for higher-quality historical and live market-data
research where OHLCV is too coarse:

- market-by-order and market-by-price depth
- top-of-book and best-bid-offer history
- trades and volume-at-price studies
- exchange-normalized OHLCV where archive coverage is insufficient
- futures/equities-style session, symbol, and roll research

The first permitted use is read-only research artifact generation. Databento data
must not become a live routing source, trading venue, promotion-evidence source,
or campaign dependency without a separately reviewed implementation and
governance decision.

## Non-Goals

- No API key is added to the repo or operator docs by this RFC.
- No dependency is added.
- No data is fetched.
- No Databento symbol is mapped to a tradeable execution symbol.
- No strategy config, campaign manifest, paper gate, shadow gate, live gate, or
  order-routing path changes.
- No claim is made that Databento data improves profitability.

## Required Decisions Before Implementation

1. Data products and schemas:
   - Choose the exact datasets and schemas, such as MBO, MBP, TBBO, trades, or
     OHLCV.
   - Document whether the target market is crypto, futures, equities, or
     cross-asset context.
2. Cost and quota control:
   - Define monthly cost cap, per-run row cap, and fail-closed behavior when
     requested data exceeds budget.
   - Persist request metadata sufficient to audit cost drivers.
3. Credentials and secrets:
   - Store API keys only through the accepted secrets path.
   - Never write keys into artifacts, logs, errors, or work-log entries.
4. Symbology:
   - Define a one-way research symbol mapping from Databento instrument IDs to
     repository symbols.
   - Do not reuse this mapping for order routing.
5. Dataset provenance:
   - Stamp dataset, schema, venue/source, symbol, query interval, row count,
     source hash, and artifact hash.
6. Retention:
   - Define retention class before any persistent local cache is created.
   - Respect existing retention-policy docs for research artifacts.
7. Reliability:
   - Add source-reachability and quota/error classification before scheduled use.
   - Distinguish source unavailability from strategy or label failure.

## Candidate Research Uses

- Volume-profile acceptance/rejection labels when trade/tick or stronger
  intraday volume data is available.
- Opening-range and session-context validation on markets with robust session
  definitions.
- Displacement versus liquidity-sweep labels using top-of-book or trade prints.
- Futures/equities context research after symbology and session calendars are
  documented.

## Hard Boundaries

- Research artifacts only.
- Read-only client only.
- No private order endpoints.
- No live, shadow, capped-live, or paper campaign dependency.
- No promotion evidence until a separate provenance qualification branch is
  reviewed.
- No operator-host schedule until reachability, cost caps, retention, and
  alerting are reviewed.

## Acceptance Criteria For A Future Implementation

- A separate implementation PR lists datasets/schemas and cost caps.
- Tests prove credentials are redacted from logs, artifacts, and errors.
- Tests prove budget/quota failures fail closed without partial artifact
  promotion.
- Tests prove symbol mapping cannot be imported by order-routing modules.
- Produced artifacts carry dataset/source/query/hash metadata.
- Produced artifacts are labeled `research_only`, `not_campaign_evidence`,
  `not_promotion_evidence`, and `not_execution_input`.
- Operator docs state how to estimate and cap cost before any run.

# Derivatives And Intraday Roadmap Boundary

Date: 2026-07-25

Backlog link: `REMAINING_TASKS.md` Active Backlog item 15.

## Decision

Keep derivatives and intraday work in read-only data collection, archived
research, and replay until separate reviewed controls prove the execution risks
are bounded.

This document does not authorize derivatives execution, short selling, leverage,
margin, live intraday routing, new broker/venue credentials, or strategy
promotion evidence.

## Allowed Near-Term Work

- Read-only public data collection for funding, open interest, basis, quotes,
  OHLCV, and other context rows already covered by accepted collector decisions.
- Archive-backed replay and research reports that carry dataset hashes and
  explicit cost assumptions.
- Intraday OHLCV/session/context labeling over archived data.
- Testnet or sandbox lifecycle probes that are isolated from campaign
  promotion and use no real capital.
- Data-source RFCs, such as the Databento RFC, that do not add credentials,
  dependencies, fetches, campaigns, gates, or execution behavior.

## Blocked Until Separate Review

- Live or capped-live derivatives orders.
- Short-side execution, margin, leverage, borrow, or perpetual futures routing.
- Paper or shadow derivatives campaigns that model executable positions.
- Strategy promotion evidence sourced from derivatives/intraday context without
  a reviewed provenance-qualification change.
- Venue/broker integration that requires private credentials or account
  permissions.
- Any Databento-backed ingestion path that fetches data, stores metered
  datasets, or influences strategy/campaign/gate behavior.

## Required Proof Before Execution Work

Before derivatives or intraday work can leave read-only research, the accepted
packet must include:

- venue or broker compliance and account-permission decision;
- contract/symbology metadata, including tick size, lot size, expiry or
  perpetual funding schedule, and product venue;
- margin model, leverage cap, maintenance margin, and liquidation-buffer model;
- funding, borrow, fee, spread, and slippage cost model;
- reduce-only exit support or an accepted equivalent close-only control;
- fail-closed risk gates for max loss, max notional, exposure, margin
  exhaustion, stale market data, and liquidation proximity;
- sandbox/testnet lifecycle proof for place, reduce-only close, cancel,
  reconcile, halt, and restart;
- archive/walk-forward evidence after measured costs;
- explicit statement that the current paper campaign and promotion gate remain
  unchanged unless a separate reviewed campaign/gate change is accepted.

## Current Source Boundaries

- `docs/research/crypto_edge_source_decision.md` authorizes OKX only as a
  read-only derivatives context source for funding/open-interest/basis research.
- `docs/research/pattern_strategy_backlog.md` keeps price-action and intraday
  labels behind archived research and separate confirmation-filter review.
- `docs/research/databento_data_source_rfc.md` is an RFC only; it does not add
  credentials, dependencies, fetches, storage, campaigns, gates, or execution.
- `docs/architecture/websocket_surface_classification.md` keeps websocket data
  non-canonical until venue support, supervision, freshness, and evidence
  authority are proven.

## Executable Guard

`tests/test_derivatives_intraday_roadmap_guard.py` pins this boundary so
derivatives/intraday research cannot silently become execution, promotion, or
data-source authority through documentation drift.

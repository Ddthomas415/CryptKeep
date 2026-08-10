# Stock Options Requirements Boundary

Date: 2026-08-10

Status: requirements boundary only. No equities/options data integration,
broker connection, credential setup, package install, campaign, promotion-gate,
paper/shadow/live execution, or shared risk budget is authorized by this
document.

## Purpose

This document prevents stock/options work from entering the crypto trading path
as an implicit expansion. Options support is a separate market, data,
compliance, symbology, risk, and lifecycle problem. The first eligible work is
read-only research artifact generation after requirements are reviewed.

## Current Boundary

| Question | Current answer |
|---|---|
| Can stock/options research run in parallel with crypto? | Yes, only as an isolated read-only research lane. |
| Can stock/options execution run in parallel with crypto? | No, not until a separate accepted execution/risk/broker policy proves account and exposure isolation. |
| Can stock/options evidence count toward the crypto paper gate? | No. It has separate symbols, calendars, data provenance, cost model, and risk semantics. |
| Can Databento or another vendor be used? | Only after the data-source RFC covers product, schema, entitlement, cost, retention, and provenance. |
| Can LLM/advisory logic select option trades? | No. Advisory research remains non-authoritative unless a future reviewed gate changes that boundary. |

## Requirements Before Any Implementation

### Account And Broker

- Broker selection and supported account type.
- Options approval level and permitted strategy classes.
- Sandbox or paper-trading lifecycle support.
- API permission scopes, key rotation, and secrets storage.
- Order, cancel, replace, exercise, assignment, and close-position APIs.
- Account-level isolation from crypto state and risk budget.

### Disclosure And Entitlements

- Current OCC/ODD disclosure requirement verified from the operator's broker
  and official source material before any option-order workflow exists.
- OPRA or vendor data entitlement verified before any options-chain or quote
  data is stored, redistributed, or persisted in artifacts.
- Data-vendor license, redistribution, retention, and cost limits documented.

### Symbology And Contract Metadata

- OSI/OCC option symbology parser and formatter.
- Underlying symbol, expiration, strike, right, multiplier, deliverable, and
  contract root.
- Corporate-action adjustment handling.
- Expiration calendar and trading-session calendar.
- Quote currency, contract multiplier, tick size, minimum price variation, and
  lot/contract unit.

### Market Data And Provenance

- Source, dataset, schema, timestamp basis, and vendor entitlement.
- Underlying price, option bid/ask, last, volume, open interest, implied
  volatility, Greeks, and surface timestamping.
- Stale data, crossed quotes, missing bid/ask, wide spread, and illiquid-chain
  rejection rules.
- Artifact hashes and explicit `research_only`, `not_campaign_evidence`,
  `not_promotion_evidence`, and `not_execution_input` labels.

### Risk And Lifecycle

- Buying-power and margin model.
- Max contract count, max premium, max notional-equivalent, max Greeks, and max
  per-underlying exposure.
- Assignment, exercise, early-exercise, expiration, pin risk, and automatic
  exercise policy.
- Close-only and liquidation controls.
- Multi-leg representation and atomicity requirements.
- Fee, commission, spread, slippage, and exercise/assignment cost model.

## First Allowed Implementation

The first implementation, if approved, should be read-only:

1. Load a small fixture options chain or approved static sample.
2. Normalize contracts into a research-only artifact.
3. Validate symbology, contract metadata, timestamps, and provenance.
4. Refuse to emit any campaign, signal, order intent, promotion evidence, or
   shared-risk artifact.

## Acceptance Criteria For A Future Read-Only PR

- Tests prove artifacts are labeled `research_only`, `not_campaign_evidence`,
  `not_promotion_evidence`, and `not_execution_input`.
- Tests prove no options module is imported by live execution, paper execution,
  promotion gates, or order-routing modules.
- Tests prove missing entitlement, missing contract metadata, stale quotes, or
  invalid symbology fail closed.
- Documentation names the data source, entitlement decision, cost cap, retention
  class, and state root.
- The implementation stores data under a separate options research state path.

## Hard Prohibitions Until Separate Review

- No stock/options order routing.
- No broker credentials.
- No paper, shadow, capped-live, or live options campaign.
- No promotion-gate evidence.
- No shared risk budget with crypto.
- No option assignment/exercise workflow.
- No model or LLM output used as capital-moving authority.

# Crypto-Edge Source Decision

Date: 2026-07-05

## Decision

Use OKX as the default read-only derivatives context source for the crypto-edge
collector plan.

This decision applies only to research data collection for funding, open
interest, and basis rows. It does not approve OKX as a live trading venue,
does not enable derivatives execution, and does not change any order routing,
risk gate, promotion gate, or strategy-dispatch behavior.

## Evidence Basis

SHOWN:

- `docs/work_log/review_stabilized_work_log.md` records a bounded read-only OKX
  derivatives collector probe on 2026-07-02.
- That probe returned funding, open-interest, and basis rows.
- The same work-log entry records Binance derivatives availability as blocked
  from the current network with `ExchangeNotAvailable`.
- `scripts/collect_live_crypto_edge_snapshot.py` persists rows as
  `research_only=true` and `execution_enabled=false`.
- `services/analytics/crypto_edge_collector.py` opens public CCXT clients with
  no API key or secret for this collector path.

UNVERIFIED:

- Long-run OKX cadence reliability from the operator host.
- Whether OKX funding/open-interest/basis rows remain available under future
  venue, jurisdiction, or network changes.
- Whether any OKX-derived strategy has positive expectancy after fees, funding,
  spread, and slippage.

## Implementation Consequence

`sample_data/crypto_edges/live_collector_plan.json` uses OKX for:

- funding
- open interest
- basis

Coinbase/Kraken quote and Coinbase order-book rows remain unchanged.

## Hard Boundaries

- No private credentials are required or authorized by this decision.
- No live execution path may consume OKX as a trading venue from this decision.
- No strategy may use OKX context rows for promotion evidence until a separate
  crypto-edge context strategy and provenance-qualification change is reviewed.
- Any scheduled collector must still prove host cadence, recent timestamps, and
  cadence-gap alerting before downstream research treats the history as
  reliable.

## Expected Outcome

The default read-only collector plan should stop depending on the externally
blocked Binance derivatives path and should begin accumulating the funding,
open-interest, and basis history needed for future `funding_extreme` and
`open_interest_shift` research.

## Research Artifact Chain

The current funding research path is read-only and artifact-based:

- `make funding-context-replay` replays stored crypto-edge rows into
  deterministic `funding_extreme` signal context.
- `make funding-context-price-join` joins stored funding snapshots to archived
  OHLCV forward-return rows.
- `make funding-threshold-sensitivity` recomputes hypothetical action counts
  and unit-size modeled forward returns for explicit threshold grids over an
  existing price-join artifact.
- `make funding-threshold-candidate-triage` ranks threshold pairs for manual
  review over an existing sensitivity artifact.

These reports do not change strategy config, start campaigns, modify gates,
route orders, compute portfolio PnL, or produce promotion evidence.

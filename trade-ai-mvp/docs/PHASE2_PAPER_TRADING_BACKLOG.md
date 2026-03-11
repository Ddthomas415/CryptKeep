# Phase 2 Backlog: Paper Trading

This backlog defines the next implementation phase after the Phase 1 research copilot scaffold.
Phase 2 objective: execute simulated orders only, with full auditability and no live capital.

## Exit Criteria
- Paper orders can be created, matched, canceled, and settled in a simulated venue.
- Portfolio/PnL metrics are reproducible from immutable fill/order records.
- Risk controls gate paper orders before acceptance.
- Explain flow references paper positions and recent paper fills.
- Regression tests cover execution, risk gate behavior, and PnL accounting.

## Priority 0: Core Trading Skeleton (Paper Only)
- [x] Create `execution_sim` service for simulated order lifecycle.
- [x] Add tables: `paper_orders`, `paper_fills`, `paper_positions`, `paper_balances`, `paper_equity_curve`.
- [x] Add idempotent `client_order_id` contract.
- [x] Add `POST /paper/orders`, `GET /paper/orders/{id}`, `POST /paper/orders/{id}/cancel`.
- [x] Add matching model with deterministic fill policy (spread/slippage model v1).
- [x] Add strict feature flag `PAPER_TRADING_ENABLED` (default `false`).
- [x] Keep `EXECUTION_ENABLED=false` and reject any live execution paths.

## Priority 1: Risk Gate Integration
- [x] Implement pre-order risk checks: max notional, max position, daily loss limit.
- [x] Persist risk decisions with reasons and thresholds used.
- [x] Add risk decision envelope:
  - [x] `ALLOW`
  - [x] `ALLOW_REDUCE_ONLY`
  - [x] `HALT_NEW_EXPOSURE`
  - [x] `FULL_STOP`
- [x] Enforce reduce-only behavior in simulated matching.

## Priority 2: Portfolio and Analytics
- [x] Build mark-to-market service for paper portfolio using latest snapshots.
- [x] Compute realized/unrealized PnL, drawdown, exposure by asset.
- [x] Add hourly and daily performance snapshots.
- [x] Add baseline benchmark comparison (buy-and-hold BTC, ETH basket).
- [x] Add attribution fields: signal source, rationale, and catalyst tags per order.

## Priority 3: Orchestrator/User Workflow
- [x] Add `POST /query/propose-trade` (proposal only, no auto-submit).
- [x] Add user approval gate in gateway for paper order submission.
- [x] Extend explanation payload with:
  - [x] active paper positions
  - [x] last paper fills
  - [x] current paper risk state
- [x] Add alerts for paper drawdown and concentration breaches.

## Priority 4: Evaluation and Promotion Safety
- [x] Add strategy replay runner against historical market/news events.
- [x] Add shadow-mode comparison between current and challenger signal logic.
- [x] Track paper metrics: Sharpe proxy, max drawdown, hit-rate by regime.
- [x] Require minimum paper performance window before any Phase 3 live discussion.

## Test Plan (must pass before Phase 2 complete)
- [x] Unit tests: order validation, matching, fees, slippage, cancellation.
- [x] Unit tests: risk gate transitions and reduce-only enforcement.
- [x] Integration tests: proposal -> approval -> paper order -> fill -> PnL update.
- [x] Integration tests: outage/degraded dependencies still keep paper state consistent.
- [x] Contract tests: API schemas and error semantics are stable.
- [x] Determinism test: replaying same inputs yields same paper fills.

## Operational/Infra Tasks
- [x] Add migration `0002_paper_trading_schema`.
- [x] Add retention policy for high-volume paper ticks/fills.
- [x] Add dashboard tab for paper positions, fills, and risk state.
- [x] Add Prometheus metrics for paper order latency and rejection reasons.
- [x] Add backup/restore procedure for paper trading tables.

## Deferred to Phase 3 (explicitly not in Phase 2)
- [x] Add dry-run live status/routing/order-intent scaffolding (no execution path).
- [x] Add custody status scaffolding with credential readiness/blockers (no key management implementation).
- [x] Add multi-venue dry-run route scoring (coinbase/binance/kraken public data).
- [x] Add persistent dry-run live intents with approval workflow (approval does not execute).
- [x] Add dry-run deployment checklist endpoint with explicit go/no-go blockers.
- [x] Add dry-run deployment arm/disarm state workflow for operator governance.
- [x] Add dry-run live execution submit endpoint over approved intents (always blocked).
- [x] Add policy-aware dry-run route scoring + route simulation endpoint (`/live/router/policy`, `/live/router/simulate`).
- [x] Persist dry-run route decisions with list endpoint for replay/inspection (`live_route_decisions`, `/live/router/decisions`).
- [x] Add dry-run route analytics endpoint over persisted decisions (`/live/router/analytics`).
- [x] Add threshold-based dry-run route alerting endpoint (`/live/router/alerts`).
- [x] Add dry-run route decision retention maintenance endpoint (`/live/router/maintenance/retention`).
- [x] Add dry-run router runbook endpoint with suggested gate/actions (`/live/router/runbook`).
- [x] Add dry-run multi-venue allocation recommendation endpoint (`/live/router/allocation`).
- [x] Add dry-run unified router gate output endpoint (`/live/router/gate`) for bot-side gating integration.
- [x] Add optional binding risk overlay in unified router gate output (`/live/router/gate?include_risk=true`).
- [x] Add dry-run gate signal persistence + list/summary/retention endpoints (`/live/router/gates*`).
- [x] Add dry-run router incident lifecycle endpoints (`/live/router/incidents/open`, list, get-by-id, reopen, ack, resolve).
- [x] Add dry-run router incident summary + retention maintenance endpoints.
- [x] Add strict opt-in sandbox submit mode in `/live/execution/submit` (`mode=sandbox_submit`, default remains `dry_run` blocked).
- [x] Add provider-aware sandbox execution inventory + dispatch (`/live/execution/providers`, `LIVE_EXECUTION_PROVIDER` contract for `mock`/`coinbase_sandbox`).
- [x] Add custody source/policy scaffolding (`/live/custody/providers`, `/live/custody/policy`, rotation SLA metadata checks).
- [x] Add custody rotation workflow contract endpoints (`/live/custody/rotation/plan`, `/live/custody/rotation/run`) with Phase 2 safety block.
- [x] Add custody key inventory/verification contract endpoints (`/live/custody/keys`, `/live/custody/keys/verify`) with strict/non-strict metadata-only checks.
- [x] Persist live execution submit attempts + add list/get/summary endpoints (`live_execution_submissions`, `/live/execution/submissions*`).
- [x] Add strict opt-in Coinbase sandbox HTTP transport path (`LIVE_EXECUTION_SANDBOX_TRANSPORT_ENABLED`) with passphrase gating and fallback stub mode.
- [x] Add sandbox execution order lifecycle endpoints (`/live/execution/orders/{venue_order_id}/status` and `/cancel`) with persistence-backed stub/transport behavior.
- [x] Add dry-run live execution submission retention maintenance endpoint (`/live/execution/submissions/maintenance/retention`).
- [x] Add dry-run live execution submission status sync endpoint (`/live/execution/submissions/{submission_id}/sync`) with persistence of last sync metadata.
- [x] Add dry-run live execution submission bulk sync endpoint (`/live/execution/submissions/sync`) with partial-success reporting.
- [x] Add per-intent live execution preflight endpoint (`/live/execution/place/preflight`) with explicit gating checks/blockers.
- [x] Add per-intent live execution payload preview endpoint (`/live/execution/place/preview`) for provider payload inspection and can-submit gating.
- [x] Add explicit Phase 3 live placement contract stub endpoint (`/live/execution/place`) that remains hard-blocked and auditable in Phase 2.
- [x] Extend unified submit contract to accept `mode=live_place` and delegate to placement stub (`/live/execution/submit` compatibility path).
- [x] Add live-place analytics endpoint (`/live/execution/place/analytics`) for blocker/outcome aggregation over persisted placement attempts.
- [x] Add intent-aware placement route recommendation endpoint (`/live/execution/place/route`) with single-venue and multi-venue strategy options (no execution path).
- [x] Wire `live_place` and `live_place` submit delegation to accept routing strategy controls (`intent` / `single_venue` / `multi_venue`) and persist route context in blocked attempts.
- [x] Add route strategy comparison endpoint (`/live/execution/place/route/compare`) with deterministic recommendation logic for operator decision support.
- [x] Enforce sandbox provider/venue compatibility in placement routing (`coinbase_sandbox` venue constraints, mismatch blockers, and provider-compatible slice filtering).
- [x] Add `strategy=auto` live placement resolution (compare-driven selection with `requested_strategy`/`resolved_strategy` audit fields).
- [x] Add live-place strategy analytics endpoint (`/live/execution/place/strategy-analytics`) covering requested/resolved strategy mix, auto resolution rate, route feasibility, and provider compatibility.
- [x] Add cost-aware route-compare tie-breaking and estimated-cost outputs (`total_estimated_cost_bps`, `recommended_estimated_cost_bps`) for live-place dry-run strategy decisions.
- [x] Extend strategy analytics with estimated-cost distributions by requested/resolved strategy and auto-vs-non-auto cost deltas.
- [x] Add multi-venue diversification controls (`min_venues`, `max_venue_ratio`) to allocation/placement route contracts with capped-ratio dry-run allocation.
- [x] Extend live-place strategy analytics with diversification diagnostics (allocation rejection reason counts and ratio-cap incidence).
- [x] Add `min_slice_quantity` control for dry-run multi-venue routing to reject dust slices and fail fast when slice constraints are unachievable.
- [x] Map allocation rejection reasons into explicit live placement blockers for route/ops diagnostics.
- [x] Extend live-place strategy analytics with allocation blocker counts and constraint-failure rates.
- [x] Tag no-feasible route-compare outcomes with constraint-failure `recommended_reason` variants when allocation constraints drive the recommendation.
- [x] Add requested/resolved strategy filters to live-place strategy analytics for scoped operator diagnostics.
- [x] Add strategy-transition diagnostics to live-place strategy analytics (`requested->resolved` counts and `auto->intent` fallback count/rate).
- [x] Add route-capacity diagnostics (`requested/allocated quantity`, coverage ratio, shortfall) and shortfall incidence metrics in live-place strategy analytics.
- [x] Add no-feasible route-compare reason variants for allocation capacity shortfall (`no_feasible_route_capacity_shortfall_*`) and per-strategy allocation coverage analytics.
- [x] Add scoped shortfall/coverage filters to live-place strategy analytics (`has_shortfall`, `min_coverage_ratio`) for targeted operator slices.
- [x] Add route-compare ranking diagnostics (`sort_rank`, `sort_key`, `recommended_tie_break_reason`) for deterministic replay/debug.
- [x] Persist auto strategy tie-break diagnostics in live placement attempts and expose tie-break reason distributions in strategy analytics.
- [ ] Live exchange order placement.
- [ ] Live custody or key management.
- [ ] Multi-venue smart routing.
- [ ] Real capital deployment.

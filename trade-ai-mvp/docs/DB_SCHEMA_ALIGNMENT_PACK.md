# Database Schema Alignment Pack (v1)

This pack aligns UI screens, API contracts, service ownership, and persistence.

## Principles
- Separate operational data from analytics/research data.
- Keep config, execution state, research memory, and audit history in distinct domains.
- Do not rely on LLM text as the only source of truth; persist structured facts/events/recommendations.
- Make risky actions fully auditable (`who`, `what`, `why`, `result`).

## Storage Split
- Postgres (operational): users/workspaces/settings/connections/recommendations/approvals/orders/positions/risk/audit.
- Timeseries (Timescale): candles/snapshots/trades/orderbook summaries/risk and pnl series.
- Vector DB (Qdrant): embeddings for documents/archive/explanation memory.
- Object store: raw html/pdfs/transcripts/raw source payloads/reports.

## Domain Tables
- Identity/workspace: `users`, `workspaces`, `workspace_members`.
- Connections: `exchange_connections`, `exchange_credentials`, `provider_connections`, `connection_test_results`.
- Market: `market_snapshots`, `market_candles`, `market_trades`, `market_orderbook_summary`.
- Research: `documents`, `document_assets`, `archive_snapshots`, `events`, `evidence_links`, `document_embeddings`.
- Trading intelligence: `research_queries`, `explanations`, `recommendations`, `recommendation_versions`.
- Execution: `approvals`, `orders`, `fills`, `positions`, `position_snapshots`.
- Risk: `risk_profiles`, `risk_limits`, `risk_status_snapshots`, `risk_events`, `kill_switch_events`, `restricted_assets`.
- Ops: `alerts`, `settings`, `terminal_sessions`, `terminal_commands`, `audit_logs`.

## Endpoint to Table Mapping (high-level)
- `GET /api/v1/dashboard/summary`: reads risk snapshots, positions, connections, providers, recommendations, explanations, events.
- `POST /api/v1/research/explain`: writes `research_queries`, `explanations`, `evidence_links`; reads market/docs/archive/events/vector refs.
- `POST /api/v1/research/search`: reads docs/archive/events/vector refs.
- `GET /api/v1/trading/recommendations*`: reads `recommendations`, `evidence_links`.
- `POST /api/v1/trading/recommendations/:id/approve`: writes `approvals` and `orders`; reads `recommendations`, risk tables, connections.
- `GET /api/v1/risk/*`, `PUT /api/v1/risk/limits`, `POST /api/v1/risk/kill-switch`: reads/writes risk tables.
- `GET/POST/PATCH/DELETE /api/v1/connections/*`: reads/writes connection tables; tests write `connection_test_results`.
- `GET/PUT /api/v1/settings`: reads/writes settings.
- `GET /api/v1/audit/events`: reads `audit_logs`.
- `POST /api/v1/terminal/*`: writes `terminal_commands` and `audit_logs`.

## Service Write Ownership
- Connections service: connection metadata/credentials/tests.
- Market service: market snapshots/candles/trades/orderbook summaries.
- Ingestion service: documents/archive/document-assets/embedding refs.
- Research/orchestrator: research queries/explanations/events/evidence links.
- Trading service: recommendations/approvals/orders/fills/positions.
- Risk service: limits/status snapshots/risk events/kill switch/restrictions.
- Ops service: alerts/settings/terminal/audit.

## Migration Order
1. Core identity/workspace
2. Settings
3. Connections
4. Market
5. Documents/archive/events
6. Research queries/explanations/evidence
7. Recommendations
8. Risk tables
9. Approvals/orders/fills/positions
10. Alerts/terminal/audit

## Index Plan (priority)
- `documents(published_at desc)`, `documents(timeline)`, `documents(content_hash)`, optional GIN on metadata.
- `document_assets(asset_symbol, relevance_score desc)`.
- `events(asset_symbol, event_time desc)`, `events(event_type)`, `events(timeline)`.
- `recommendations(workspace_id, status, created_at desc)`, `recommendations(asset_symbol, created_at desc)`.
- `orders(workspace_id, status, submitted_at desc)`, `orders(exchange_connection_id, submitted_at desc)`.
- `positions(workspace_id, state, updated_at desc)`, `positions(asset_symbol, state)`.
- `risk_status_snapshots(workspace_id, ts desc)`.
- `audit_logs(workspace_id, ts desc)`, `audit_logs(request_id)`, `audit_logs(entity_type, entity_id)`.

## MVP Minimal Set
- `users`, `workspaces`
- `exchange_connections`, `provider_connections`
- `market_snapshots`, `market_candles`
- `documents`, `events`
- `research_queries`, `explanations`
- `recommendations`
- `risk_limits`, `risk_status_snapshots`
- `settings`, `audit_logs`

## Full Production Set
- Identity/workspace: `users`, `workspaces`, `workspace_members`.
- Connections: `exchange_connections`, `exchange_credentials`, `provider_connections`, `connection_test_results`.
- Market: `market_snapshots`, `market_candles`, `market_trades`, `market_orderbook_summary`.
- Research: `documents`, `document_assets`, `archive_snapshots`, `events`, `evidence_links`, `document_embeddings`.
- Trading intelligence/execution: `research_queries`, `explanations`, `recommendations`, `recommendation_versions`, `approvals`, `orders`, `fills`, `positions`, `position_snapshots`.
- Risk: `risk_profiles`, `risk_limits`, `risk_status_snapshots`, `risk_events`, `kill_switch_events`, `restricted_assets`.
- Ops: `alerts`, `settings`, `terminal_sessions`, `terminal_commands`, `audit_logs`.

## Promotion Criteria (MVP -> Production Schema)
- Data volume: sustained ingestion requiring partitioning/retention tiers (market ticks/docs/audit).
- Product scope: live approvals/orders/positions enabled beyond research-only mode.
- Explainability: evidence-link traceability required for recommendation/approval audits.
- Reliability: credential rotation, connection test history, and reconciliation snapshots required by ops policy.
- Compliance: full audit/event provenance and terminal history required for user-action reconstruction.

## Retention and Archival Policy (with config knobs)
- Keep long-term:
  - `audit_logs`, `approvals`, `orders`, `fills`, `positions`, `risk_events`, `kill_switch_events`.
- Archive threshold:
  - raw `documents.raw_text`, `archive_snapshots.raw_text`, high-frequency `market_trades`.
- Keep summarized:
  - `market_candles`, explanation metadata, recommendation lifecycle metadata.
- Config knobs (recommended):
  - `retention.audit_days`
  - `retention.market_ticks_days`
  - `retention.raw_document_days`
  - `retention.archive_raw_days`
  - `retention.position_snapshot_days`
  - `retention.terminal_command_days`

## Specialized Traceability Tables
- Vector references:
  - `document_embeddings(document_id, chunk_index, vector_id, embedding_model, created_at)`.
- Evidence links:
  - `evidence_links(parent_type, parent_id, evidence_type, evidence_ref_id, source_name, timestamp, summary, relevance, confidence, metadata_json)`.

## Connection Credential Split
- `exchange_connections`: operational metadata and status only.
- `exchange_credentials`: encrypted credential blobs, versioning, key fingerprint, rotation metadata.
- `connection_test_results`: immutable test history (`success`, permissions, latency, warnings, raw provider payload metadata).

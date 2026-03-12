# API Ownership and Implementation Order (v1)

This document is the backend contract anti-drift map for `/api/v1`.
It aligns endpoint ownership, implementation order, and persistence mapping.

## 1) Service ownership by endpoint domain

- `gateway`:
  - API envelope, request-id propagation, role header extraction, error shape normalization.
- `orchestrator/research`:
  - `POST /api/v1/research/explain`
  - `POST /api/v1/research/search`
  - `GET /api/v1/research/history`
- `market_data`:
  - `GET /api/v1/market/{asset}/snapshot`
  - `GET /api/v1/market/{asset}/candles`
- `trading`:
  - `GET /api/v1/trading/recommendations`
  - `GET /api/v1/trading/recommendations/{id}`
  - `POST /api/v1/trading/recommendations/{id}/approve|reject`
  - `GET /api/v1/approvals`
  - `POST /api/v1/approvals/{id}/approve|reject`
- `risk`:
  - `GET /api/v1/risk/summary`
  - `GET|PUT /api/v1/risk/limits`
  - `POST /api/v1/risk/kill-switch`
- `connections`:
  - `GET|POST|PATCH|DELETE /api/v1/connections/exchanges`
  - `POST /api/v1/connections/exchanges/test`
  - `GET|POST /api/v1/connections/providers`
  - `POST /api/v1/connections/providers/test`
- `settings/ops`:
  - `GET|PUT /api/v1/settings`
  - `GET /api/v1/audit/events`
- `terminal`:
  - `POST /api/v1/terminal/execute`
  - `POST /api/v1/terminal/confirm`

## 2) Recommended implementation order

1. Envelope + enums + health (`/api/v1/health`, `/api/v1/enums`)
2. Dashboard summary (`/api/v1/dashboard/summary`)
3. Research endpoints
4. Market endpoints
5. Trading recommendation/approval endpoints
6. Risk endpoints
7. Connections endpoints
8. Settings + audit endpoints
9. Controlled terminal endpoints
10. Persistence hardening pass (replace in-memory stores with DB-backed services)

## 3) Persistence mapping source of truth

- Primary schema mapping and endpoint-table matrix:
  - `trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`
- Execution/risk lifecycle constraints:
  - `trade-ai-mvp/docs/STATE_MACHINE_SPEC.md`
- Authorization and policy gates:
  - `trade-ai-mvp/docs/PERMISSIONS_POLICY_MATRIX.md`

## 4) Drift prevention rules

- Every new `/api/v1/*` route must declare:
  - owning service domain
  - persistence writes (if any)
  - policy gates (role/mode/risk/kill-switch/connection)
- Endpoint additions must update:
  - this document
  - `DB_SCHEMA_ALIGNMENT_PACK.md` endpoint-to-table mapping
  - tests in `trade-ai-mvp/tests/test_api_v1_contracts.py`
- Terminal endpoints must remain command-allowlisted and must never execute shell commands.

# Crypto Trading AI

Starter repository for a crypto trading AI platform focused first on:
- Dashboard
- Research
- Connections
- Settings

Trading, Risk, and Terminal are scaffolded but mostly stubbed in this version.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

If the default host ports are already occupied by another repo, use:

```bash
make up-auto-ports
```

That launcher keeps the internal container ports fixed, but automatically picks the next free host ports for:
- Postgres
- Redis
- Qdrant
- backend
- frontend

To preview the resolved host-port mapping without starting containers:

```bash
python scripts/run_compose_auto_ports.py --print-env
```

Backend:
- http://localhost:8000
- docs: http://localhost:8000/docs

Frontend:
- http://localhost:3000

Main goals of this starter
- runnable Docker setup
- FastAPI backend shell
- React/Vite frontend shell
- shared response envelope
- health endpoints
- dashboard summary endpoint
- research explain endpoint
- connections list/test/save endpoints
- settings get/update endpoints

Useful commands

```bash
make up
make up-auto-ports
make down
make migrate
make backend-test
make frontend-test
make sync-workflows
make check-workflows
make generate-schemas
make check-schemas
make check-mock-data
make generate-openapi
make check-openapi
make install-hooks
make precommit-check
make ci-check
```

CI workflow source-of-truth

- Source definitions live in `infra/github/workflows/`.
- Runtime GitHub files live in `.github/workflows/`.
- Keep them aligned with:
  - `make sync-workflows`
  - `make check-workflows`

Pre-commit guardrail

- Install hooks once per clone with `make install-hooks`.
- The installer auto-detects monorepo/nested layout and sets `core.hooksPath` correctly.
- The pre-commit hook enforces:
  - workflow sync check
  - generated OpenAPI sync check
  - OpenAPI/route contract check
  - backend lint (`ruff`)
  - frontend lint (`pnpm lint`)

Frontend live integration tests

- `frontend/tests/unit/api.live.integration.test.ts` covers live backend happy-path calls.
- These run only when `RUN_API_INTEGRATION_TESTS=true`.
- `make ci-check` enables them automatically inside the frontend container.

Current status

Ready:
- backend app shell
- frontend app shell
- health routes
- dashboard route
- research explain route
- connections routes
- settings routes
- audit route
- terminal mock route

Stubbed:
- live trading execution
- paper trading workflow
- event bus
- reconciliation
- terminal command registry depth
- real provider integrations

Next recommended steps
1. replace mock-backed services with repository-backed DB reads/writes
2. wire frontend pages to a typed API client layer instead of inline `fetch`
3. expand risk/trading from stubs into paper-trading workflows
4. add exchange/provider client adapters behind service interfaces
5. extend contract coverage for OpenAPI/schema evolution in CI
6. add worker/event bus primitives for async ingestion/reconciliation

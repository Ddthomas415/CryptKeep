up:
	docker compose up --build

up-auto-ports:
	python3 scripts/run_compose_auto_ports.py

backend-dev:
	python3 scripts/run_backend_auto_port.py

frontend-dev:
	python3 scripts/run_frontend_auto_port.py

down:
	docker compose down

migrate:
	docker compose run --rm backend alembic upgrade head

backend-test:
	docker compose run --rm backend pytest

frontend-test:
	docker compose run --rm frontend sh -c "cd /app/frontend && pnpm test"

backend-shell:
	docker compose run --rm backend sh

frontend-shell:
	docker compose run --rm frontend sh

sync-workflows:
	bash scripts/sync_github_workflows.sh

check-workflows:
	bash scripts/check_github_workflows_sync.sh

generate-schemas:
	docker compose exec -T backend python /app/scripts/generate_shared_schemas.py

check-schemas:
	docker compose exec -T backend python /app/scripts/generate_shared_schemas.py --check

check-mock-data:
	docker compose exec -T backend python /app/scripts/validate_shared_mock_data.py

generate-openapi:
	docker compose exec -T backend python /app/scripts/generate_shared_openapi.py

check-openapi:
	docker compose exec -T backend python /app/scripts/generate_shared_openapi.py --check
	docker compose exec -T backend python /app/scripts/check_openapi_sync.py

install-hooks:
	bash scripts/install_git_hooks.sh

precommit-check:
	bash .githooks/pre-commit

ci-check:
	bash scripts/check_github_workflows_sync.sh
	docker compose exec -T backend python /app/scripts/generate_shared_schemas.py --check
	docker compose exec -T backend python /app/scripts/validate_shared_mock_data.py
	docker compose exec -T backend python /app/scripts/generate_shared_openapi.py --check
	docker compose exec -T backend python /app/scripts/check_openapi_sync.py
	docker compose exec -T backend ruff check /app/backend
	docker compose exec -T backend pytest -q /app/backend/tests
	docker compose exec -T frontend sh -lc "cd /app/frontend && pnpm lint && RUN_API_INTEGRATION_TESTS=true API_INTEGRATION_BASE_URL=http://backend:8000 pnpm test --run"

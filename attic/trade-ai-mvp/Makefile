.PHONY: up down migrate seed test smoke fmt backup-paper restore-paper

up:
	docker compose up --build -d

down:
	docker compose down -v

migrate:
	docker compose exec gateway alembic upgrade head

seed:
	docker compose exec gateway python scripts/seed_assets.py
	docker compose exec gateway python scripts/seed_sources.py

test:
	pytest -q

smoke:
	./scripts/smoke_explain.sh

fmt:
	python -m pip install ruff black >/dev/null 2>&1 || true
	ruff check . || true
	black . || true

backup-paper:
	bash ./scripts/paper_backup.sh

restore-paper:
	bash ./scripts/paper_restore.sh $(FILE)

SHELL := /bin/bash
PY := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON := $(VENV)/bin/python

.DEFAULT_GOAL := help

help:
	@echo "Crypto Bot Pro - common commands"
	@echo ""
	@echo "Install:"
	@echo "  make venv"
	@echo "  make install"
	@echo "  make preflight"
	@echo ""
	@echo "Run:"
	@echo "  make dashboard"
	@echo "  make backend"
	@echo ""
	@echo "Quality:"
	@echo "  make format"
	@echo "  make lint"
	@echo "  make test"
	@echo ""
	@echo "Docker:"
	@echo "  make up / make down / make reset"

venv:
	@$(PY) -m venv $(VENV)
	@$(PIP) install -U pip wheel setuptools

install: venv
	@$(PIP) install -e ".[dev]"

preflight: install
	@$(PYTHON) scripts/preflight_check.py

format: install
	@$(PYTHON) -m black .

lint: install
	@$(PYTHON) -m ruff check .

test: install
	@$(PYTHON) -m pytest -q

dashboard: install
	@$(PYTHON) -m streamlit run dashboard/app.py --server.port 8501

backend: install
	@$(PYTHON) -m backend.main

up:
	@docker compose -f docker/docker-compose.yml up --build

down:
	@docker compose -f docker/docker-compose.yml down

reset:
	@docker compose -f docker/docker-compose.yml down -v --remove-orphans
	@bash scripts/reset_local.sh

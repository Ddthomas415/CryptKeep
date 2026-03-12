PYTHON ?= $(shell if ./.venv/bin/python -V >/dev/null 2>&1; then echo ./.venv/bin/python; elif command -v python3 >/dev/null 2>&1; then echo python3; else echo python; fi)

.PHONY: doctor-strict alignment check-alignment check-alignment-list check-alignment-list-json check-alignment-json check-alignment-json-fast validate-quick validate-json-quick validate-json-fast validate-json validate pre-release-sanity pre-release-sanity-quick pre-release-sanity-json-quick pre-release-sanity-json-fast remaining-tasks phase1-smoke test

doctor-strict:
	$(PYTHON) tools/repo_doctor.py --strict

alignment: check-alignment

check-alignment:
	$(PYTHON) scripts/check_repo_alignment.py

check-alignment-list:
	$(PYTHON) scripts/check_repo_alignment.py --list-tests

check-alignment-list-json:
	@$(PYTHON) scripts/check_repo_alignment.py --list-tests --json

check-alignment-json:
	@$(PYTHON) scripts/check_repo_alignment.py --json

check-alignment-json-fast:
	@CBP_ALIGNMENT_SKIP_GUARDS=1 $(PYTHON) scripts/check_repo_alignment.py --json

validate-quick:
	$(PYTHON) scripts/validate.py --quick

validate-json-quick:
	@$(PYTHON) scripts/validate.py --quick --json

validate-json-fast:
	@CBP_VALIDATE_SKIP_PYTEST=1 $(PYTHON) scripts/validate.py --json

validate-json:
	@$(PYTHON) scripts/validate.py --json

validate:
	$(PYTHON) scripts/validate.py

pre-release-sanity:
	$(PYTHON) scripts/pre_release_sanity.py

pre-release-sanity-quick:
	$(PYTHON) scripts/pre_release_sanity.py --skip-ruff --skip-mypy --skip-pytest --skip-config --skip-imports

pre-release-sanity-json-quick:
	@$(PYTHON) scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy --skip-pytest --skip-config --skip-imports

pre-release-sanity-json-fast:
	@CBP_PRE_RELEASE_SKIP_PYTEST=1 $(PYTHON) scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy

remaining-tasks:
	$(PYTHON) scripts/rebuild_remaining_tasks.py

phase1-smoke:
	$(PYTHON) phase1_research_copilot/scripts/smoke_phase1_copilot.py

test:
	$(PYTHON) -m pytest -q

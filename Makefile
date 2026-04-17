PYTHON ?= $(shell if ./.venv/bin/python -V >/dev/null 2>&1; then echo ./.venv/bin/python; elif command -v python3 >/dev/null 2>&1; then echo python3; else echo python; fi)

CRYPTO_EDGE_INTERVAL_SEC ?= 300
PAPER_EVIDENCE_RUNTIME_SEC ?= 900

.PHONY: doctor-strict alignment check-alignment check-alignment-list check-alignment-list-json check-alignment-json check-alignment-json-fast validate-quick validate-json-quick validate-json-fast validate-json validate pre-release-sanity pre-release-sanity-quick pre-release-sanity-json-quick pre-release-sanity-json-fast remaining-tasks phase1-safety phase1-smoke phase1-smoke-openai load-sample-crypto-edges collect-live-crypto-edges collect-live-crypto-edges-loop stop-live-crypto-edges-loop status-live-crypto-edges-loop collect-paper-strategy-evidence stop-paper-strategy-evidence status-paper-strategy-evidence strategy-evidence-cycle system-diagnostics dashboard docker-up-auto-ports docker-print-auto-ports test test-runtime test-checkpoints

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

phase1-safety:
	$(PYTHON) scripts/run_phase1_safety.py

phase1-smoke:
	$(PYTHON) phase1_research_copilot/scripts/smoke_phase1_copilot.py

phase1-smoke-openai:
	$(PYTHON) phase1_research_copilot/scripts/smoke_phase1_copilot.py --expect-openai

load-sample-crypto-edges:
	$(PYTHON) scripts/load_sample_crypto_edge_data.py --print-report

collect-live-crypto-edges:
	$(PYTHON) scripts/collect_live_crypto_edge_snapshot.py --plan-file sample_data/crypto_edges/live_collector_plan.json --print-report

collect-live-crypto-edges-loop:
	$(PYTHON) scripts/run_crypto_edge_collector_loop.py --plan-file sample_data/crypto_edges/live_collector_plan.json --interval-sec $(CRYPTO_EDGE_INTERVAL_SEC)

stop-live-crypto-edges-loop:
	$(PYTHON) scripts/run_crypto_edge_collector_loop.py --stop

status-live-crypto-edges-loop:
	$(PYTHON) scripts/run_crypto_edge_collector_loop.py --status

collect-paper-strategy-evidence:
	$(PYTHON) scripts/run_paper_strategy_evidence_collector.py --runtime-sec $(PAPER_EVIDENCE_RUNTIME_SEC)

stop-paper-strategy-evidence:
	$(PYTHON) scripts/run_paper_strategy_evidence_collector.py --stop

status-paper-strategy-evidence:
	$(PYTHON) scripts/run_paper_strategy_evidence_collector.py --status

strategy-evidence-cycle:
	$(PYTHON) scripts/run_strategy_evidence_cycle.py --write-decision-record

system-diagnostics:
	$(PYTHON) scripts/run_system_diagnostics.py

dashboard:
	$(PYTHON) scripts/run_dashboard.py --open

docker-up-auto-ports:
	$(PYTHON) docker/run_compose_auto_ports.py

docker-print-auto-ports:
	$(PYTHON) docker/run_compose_auto_ports.py --print-env

test:
	$(PYTHON) -m pytest -q

test-runtime:
	$(PYTHON) -m pytest -q -m runtime tests

test-checkpoints:
	$(PYTHON) -m pytest -q -m checkpoint tests

test-governance:
	$(PYTHON) -m pytest -q \
	  tests/test_governance_blockers_minimum.py \
	  tests/test_governance_audit_repo_anchored.py \
	  tests/test_governance_module_wrappers.py \
	  tests/test_governance_doc_metadata.py \
	  tests/test_direct_origin_guard.py \
	  tests/test_signal_replay.py \
	  tests/test_paper_strategy_evidence_service.py \
	  tests/test_ema_cross_runtime_invalidation.py \
	  tests/test_ops_risk_gate_engine.py \
	  tests/test_auth_gate.py \
	  tests/test_auth_runtime_guard.py \
	  tests/test_auth_capabilities.py \
	  tests/test_dashboard_home_digest.py

precommit-prereqs:
	docker start cbp-backend

.PHONY: governance-smoke
governance-smoke:
	python3 tools/repo_doctor.py --strict
	./scripts/manual_repo_audit.sh quick
	./.venv/bin/python -m pytest -q tests/test_manual_repo_audit_paths.py

# Fast test suite — skips blocking service-loop tests
# Use this in CI or when you don't want to wait for loop tests
test-fast:
	CBP_SKIP_SLOW=1 $(PYTHON) -m pytest tests/ \
		--ignore=tests/test_symbol_scanner.py \
		--ignore=tests/test_dashboard_view_data.py \
		--ignore=tests/test_dashboard_page_runtime.py \
		--ignore=tests/test_dashboard_home_digest.py \
		-q

# Full test suite including slow loop tests (run locally with running services)
test-full:
	$(PYTHON) -m pytest tests/ \
		--ignore=tests/test_symbol_scanner.py \
		--ignore=tests/test_dashboard_view_data.py \
		--ignore=tests/test_dashboard_page_runtime.py \
		--ignore=tests/test_dashboard_home_digest.py \
		-q

# Slow tests only
test-slow:
	$(PYTHON) -m pytest tests/ -m slow -v --tb=short

# Control kernel
kernel-status:
	$(PYTHON) scripts/show_control_kernel_status.py

kernel-status-json:
	$(PYTHON) scripts/show_control_kernel_status.py --json

kernel-promote:
	@echo "Usage: make kernel-promote STRATEGY=<id> REASON=<reason>"
	$(PYTHON) scripts/show_control_kernel_status.py --promote $(STRATEGY) --reason "$(REASON)"

kernel-demote:
	@echo "Usage: make kernel-demote STRATEGY=<id>"
	$(PYTHON) scripts/show_control_kernel_status.py --demote $(STRATEGY) --reason "operator_manual_demotion"

# ES Daily Trend v1 — paper run and promotion gates

# Stop all paper campaign processes cleanly
paper-stop:
	$(PYTHON) - <<'PY'
	import subprocess, pathlib
	flags = pathlib.Path(".cbp_state/runtime/flags")
	flags.mkdir(parents=True, exist_ok=True)
	for stop_flag in ["paper_strategy_evidence.stop", "strategy_runner.stop", "paper_engine.stop"]:
		(flags / stop_flag).write_text("stop\n", encoding="utf-8")
	for proc_name in ["run_es_daily_trend_paper", "run_strategy_runner", "run_paper_engine", "run_tick_publisher"]:
		subprocess.run(["pkill", "-f", f"{proc_name}.py"], capture_output=True)
	print("Paper campaign stop signals sent. Wait 5s for clean shutdown.")
	PY

# Status of all paper campaign processes
paper-ps:
	@ps aux | grep -E "run_es_daily_trend|run_tick_publisher|run_strategy_runner|run_paper_engine" | grep -v grep || echo "No paper campaign processes running"

# Clean stale locks left by killed processes
paper-clean-locks:
	@rm -f .cbp_state/runtime/locks/tick_publisher.lock .cbp_state/runtime/locks/paper_engine.lock .cbp_state/runtime/locks/strategy_runner.lock
	@rm -f .cbp_state/runtime/snapshots/system_status.latest.json
	@rm -f .cbp_state/runtime/flags/paper_strategy_evidence.stop
	@echo "Stale locks and stop flags cleared"

# ES Daily Trend v1 — paper run and promotion gates
STRATEGY_ID ?= es_daily_trend_v1

paper-run:
	$(PYTHON) scripts/run_es_daily_trend_paper.py

paper-status:
	$(PYTHON) scripts/run_es_daily_trend_paper.py --status

paper-dry-run:
	$(PYTHON) scripts/run_es_daily_trend_paper.py --dry-run

check-gates:
	$(PYTHON) scripts/check_promotion_gates.py

check-gates-json:
	$(PYTHON) scripts/check_promotion_gates.py --json

promote-strategy:
	$(PYTHON) scripts/show_control_kernel_status.py --promote $(STRATEGY_ID)

# Paper campaign log tailing
paper-logs:
	@echo "Tailing campaign logs (Ctrl-C to stop)..."
	tail -f .cbp_state/runtime/logs/*.log 2>/dev/null || echo "No log files found — has the campaign started?"

# Developer environment setup
dev-setup:
	$(PYTHON) scripts/install.py
	@echo ""
	@echo "Environment ready. Copy .env from template:"
	@echo "  cp config/templates/.env.template .env"
	@echo ""
	@echo "To run the paper campaign:"
	@echo "  make paper-run"

# Operational safety scripts
kill-switch-on:
	$(PYTHON) scripts/killswitch.py --arm

kill-switch-off:
	$(PYTHON) scripts/killswitch.py --disarm

kill-switch-status:
	$(PYTHON) scripts/killswitch.py --status

# Live gate inspection
gate-inputs:
	$(PYTHON) scripts/show_live_gate_inputs.py

# Test fill injection (paper testing only)
inject-test-fill:
	$(PYTHON) scripts/inject_test_fill.py

# Candidate scan
candidate-scan:
	$(PYTHON) scripts/run_candidate_scan.py

candidate-summary:
	$(PYTHON) scripts/candidate_trade_summary.py

# Live reconciliation (shadow/live stages)
live-reconcile:
	$(PYTHON) scripts/live_reconcile.py

# Script index
script-index:
	@echo "=== Operational Scripts ==="
	@echo "  make paper-run          — run paper campaign"
	@echo "  make check-gates        — promotion gate status"
	@echo "  make kill-switch-on/off — arm/disarm kill switch"
	@echo "  make gate-inputs        — show live gate current values"
	@echo "  make inject-test-fill   — inject a test fill (paper only)"
	@echo "  make candidate-scan     — run candidate signal scan"
	@echo "  make live-reconcile     — reconcile live positions"
	@echo "  make paper-logs         — tail campaign logs"
	@echo "  make dev-setup          — setup developer environment"
	@echo ""
	@echo "Full script list: ls scripts/*.py"

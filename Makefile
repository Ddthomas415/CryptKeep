PYTHON ?= $(shell if ./.venv/bin/python -V >/dev/null 2>&1; then echo ./.venv/bin/python; elif command -v python3 >/dev/null 2>&1; then echo python3; else echo python; fi)

CRYPTO_EDGE_INTERVAL_SEC ?= 300
PAPER_EVIDENCE_RUNTIME_SEC ?= 900
PAPER_CAMPAIGN_CONFIG ?= configs/paper_evidence_campaigns.laptop.json
HETZNER_SSH_TARGET ?= cryptkeep@100.86.128.9
HETZNER_APP_DIR ?= /srv/cryptkeep/app
HETZNER_PAPER_CAMPAIGN_CONFIG ?= configs/paper_evidence_campaigns.hetzner.example.json
HETZNER_STATUS_TIMEOUT_SEC ?= 15
HETZNER_EDGE_EXPECTED_COMMIT ?=
HETZNER_EDGE_EXPECTED_BRANCH ?= master
HETZNER_EDGE_EXPECTED_DERIVATIVES_VENUE ?= okx
HETZNER_EDGE_REMOTE_STATE_DIR ?= /var/lib/cbp
STRATEGY_REVIEW_STRATEGY_ID ?= sma_200_trend
STRATEGY_REVIEW_SYMBOL ?= BTC/USDT
STRATEGY_REVIEW_LOSS_LIMIT ?= 10

.PHONY: doctor-strict alignment check-alignment check-alignment-list check-alignment-list-json check-alignment-json check-alignment-json-fast validate-quick validate-json-quick validate-json-fast validate-json validate pre-release-sanity pre-release-sanity-quick pre-release-sanity-json-quick pre-release-sanity-json-fast remaining-tasks phase1-safety phase1-smoke phase1-smoke-openai load-sample-crypto-edges collect-live-crypto-edges collect-live-crypto-edges-loop stop-live-crypto-edges-loop status-live-crypto-edges-loop check-short-context-readiness collect-paper-strategy-evidence stop-paper-strategy-evidence status-paper-strategy-evidence status-paper-campaigns status-paper-soak status-paper-soak-json status-paper-gate-qualification status-paper-gate-qualification-json status-paper-hetzner status-hetzner-edge-runtime status-paper-all check-hetzner-paper-host-health restore-paper-campaigns recover-paper-campaigns strategy-evidence-cycle system-diagnostics dashboard docker-up-auto-ports docker-print-auto-ports test test-runtime test-checkpoints ai-operator-oversight

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
	$(PYTHON) scripts/smoke_phase1_copilot.py

phase1-smoke-openai:
	$(PYTHON) scripts/smoke_phase1_copilot.py --expect-openai

load-sample-crypto-edges:
	$(PYTHON) scripts/load_sample_crypto_edge_data.py --print-report

collect-live-crypto-edges:
	$(PYTHON) scripts/collect_live_crypto_edge_snapshot.py --plan-file sample_data/crypto_edges/live_collector_plan.json --print-report

collect-live-crypto-edges-loop:
	$(PYTHON) scripts/data/run_crypto_edge_collector_loop.py --plan-file sample_data/crypto_edges/live_collector_plan.json --interval-sec $(CRYPTO_EDGE_INTERVAL_SEC)

stop-live-crypto-edges-loop:
	$(PYTHON) scripts/data/run_crypto_edge_collector_loop.py --stop

status-live-crypto-edges-loop:
	$(PYTHON) scripts/data/run_crypto_edge_collector_loop.py --status

check-short-context-readiness:
	$(PYTHON) scripts/check_short_context_readiness.py

.PHONY: check-paper-campaign-ownership
check-paper-campaign-ownership:
	$(PYTHON) scripts/check_paper_campaign_ownership.py

collect-paper-strategy-evidence:
	$(PYTHON) scripts/run_paper_strategy_evidence_collector.py --runtime-sec $(PAPER_EVIDENCE_RUNTIME_SEC)

stop-paper-strategy-evidence:
	$(PYTHON) scripts/run_paper_strategy_evidence_collector.py --stop

status-paper-strategy-evidence:
	$(PYTHON) scripts/run_paper_strategy_evidence_collector.py --status

status-paper-campaigns:
	$(PYTHON) scripts/restore_paper_campaigns.py --config $(PAPER_CAMPAIGN_CONFIG) --status

status-paper-soak:
	$(PYTHON) scripts/report_supervised_soak_status.py --config $(PAPER_CAMPAIGN_CONFIG)

status-paper-soak-json:
	@$(PYTHON) scripts/report_supervised_soak_status.py --config $(PAPER_CAMPAIGN_CONFIG) --json

status-paper-gate-qualification:
	$(PYTHON) scripts/report_paper_gate_qualification.py

status-paper-gate-qualification-json:
	@$(PYTHON) scripts/report_paper_gate_qualification.py --json

status-paper-hetzner:
	$(PYTHON) scripts/report_hetzner_paper_campaign_status.py --strict --ssh-target $(HETZNER_SSH_TARGET) --app-dir $(HETZNER_APP_DIR) --config $(HETZNER_PAPER_CAMPAIGN_CONFIG) --timeout-sec $(HETZNER_STATUS_TIMEOUT_SEC)

status-hetzner-edge-runtime:
	$(PYTHON) scripts/report_hetzner_crypto_edge_runtime_status.py --strict --ssh-target $(HETZNER_SSH_TARGET) --app-dir $(HETZNER_APP_DIR) --remote-state-dir $(HETZNER_EDGE_REMOTE_STATE_DIR) --expected-branch $(HETZNER_EDGE_EXPECTED_BRANCH) --expected-derivatives-venue $(HETZNER_EDGE_EXPECTED_DERIVATIVES_VENUE) --timeout-sec $(HETZNER_STATUS_TIMEOUT_SEC) $(if $(HETZNER_EDGE_EXPECTED_COMMIT),--expected-commit $(HETZNER_EDGE_EXPECTED_COMMIT),)

status-paper-all:
	@status=0; \
	echo "=== Laptop Paper Soak ==="; \
	$(MAKE) --no-print-directory status-paper-soak || status=$$?; \
	echo ""; \
	echo "=== Hetzner Paper Campaign ==="; \
	$(MAKE) --no-print-directory status-paper-hetzner || status=$$?; \
	exit $$status

check-hetzner-paper-host-health:
	$(PYTHON) scripts/check_hetzner_paper_host_health.py --config $(HETZNER_PAPER_CAMPAIGN_CONFIG)

restore-paper-campaigns:
	$(PYTHON) scripts/restore_paper_campaigns.py --config $(PAPER_CAMPAIGN_CONFIG) --restore

recover-paper-campaigns:
	$(PYTHON) scripts/restore_paper_campaigns.py --config $(PAPER_CAMPAIGN_CONFIG) --restore --preflight-ohlcv --restart-unhealthy --ohlcv-preflight-probe-limit 400 --ohlcv-preflight-attempts 3 --ohlcv-preflight-attempt-delay-sec 2

strategy-evidence-cycle:
	$(PYTHON) scripts/data/run_strategy_evidence_cycle.py --write-decision-record

.PHONY: strategy-review
strategy-review:
	$(MAKE) --no-print-directory status-paper-all
	$(PYTHON) scripts/report_paper_run_diagnostics.py
	$(PYTHON) scripts/dev/replay_paper_losses.py \
		--strategy-id $(STRATEGY_REVIEW_STRATEGY_ID) \
		--symbol $(STRATEGY_REVIEW_SYMBOL) \
		--limit $(STRATEGY_REVIEW_LOSS_LIMIT)

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

.PHONY: test-ci-ignored
test-ci-ignored:
	$(PYTHON) -m pytest -q \
		tests/test_symbol_scanner.py \
		tests/test_dashboard_view_data.py \
		tests/test_dashboard_page_runtime.py \
		tests/test_dashboard_home_digest.py

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

.PHONY: test-governance precommit-prereqs test-fast test-full test-slow
.PHONY: kernel-status kernel-status-json kernel-promote kernel-demote
.PHONY: paper-ps paper-clean-locks paper-run paper-status paper-dry-run
.PHONY: check-gates check-gates-json promote-strategy paper-logs dev-setup
.PHONY: kill-switch-on kill-switch-off kill-switch-status gate-inputs
.PHONY: inject-test-fill candidate-scan candidate-summary candidate-outcomes ai-operator-oversight live-reconcile
.PHONY: pullback-stage0-readiness pullback-stage0-baseline pullback-stage0-verify funding-stage0-readiness funding-stage0-baseline funding-stage0-verify funding-context-replay ohlcv-archive-backfill funding-context-price-join price-action-context-labels price-action-forward-returns price-action-window-stability price-action-candidate-triage check-short-context-readiness
.PHONY: script-index paper-run-short paper-stop-now live-intent-history-schema live-intent-history-schema-init

# Fast test suite — skips blocking service-loop tests
# Use this in CI or when you don't want to wait for loop tests
test-fast:
	CBP_SKIP_SLOW=1 $(PYTHON) -m pytest tests/ -q

# Full test suite including slow loop tests (run locally with running services)
test-full:
	$(PYTHON) -m pytest tests/ -q

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
	$(PYTHON) scripts/dev/run_es_daily_trend_paper.py

paper-status:
	$(PYTHON) scripts/dev/run_es_daily_trend_paper.py --status

paper-dry-run:
	$(PYTHON) scripts/dev/run_es_daily_trend_paper.py --dry-run

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
	$(PYTHON) scripts/live/show_live_gate_inputs.py

# Test fill injection (paper testing only)
inject-test-fill:
	$(PYTHON) scripts/dev/inject_test_fill.py

# Candidate scan
candidate-scan:
	$(PYTHON) scripts/data/run_candidate_scan.py

candidate-summary:
	$(PYTHON) scripts/candidate_trade_summary.py

candidate-outcomes:
	$(PYTHON) scripts/run_candidate_outcome_report.py

ai-operator-oversight:
	$(PYTHON) scripts/run_ai_operator_oversight.py

# Pullback Stage 0 proof helpers (read-only; they do not run the 15-minute proof)
pullback-stage0-readiness:
	$(PYTHON) scripts/check_pullback_stage0_readiness.py

pullback-stage0-baseline:
	$(PYTHON) scripts/verify_pullback_stage0_proof.py --record-baseline

pullback-stage0-verify:
	$(PYTHON) scripts/verify_pullback_stage0_proof.py

# Funding Extreme Stage 0 proof helpers (read-only; they do not run the 15-minute proof)
FUNDING_STAGE0_ARGS ?=
funding-stage0-readiness:
	$(PYTHON) scripts/check_funding_stage0_readiness.py $(FUNDING_STAGE0_ARGS)

funding-stage0-baseline:
	$(PYTHON) scripts/verify_funding_stage0_proof.py --record-baseline $(FUNDING_STAGE0_ARGS)

funding-stage0-verify:
	$(PYTHON) scripts/verify_funding_stage0_proof.py $(FUNDING_STAGE0_ARGS)

FUNDING_CONTEXT_REPLAY_ARGS ?=
funding-context-replay:
	$(PYTHON) scripts/research/run_funding_context_replay.py $(FUNDING_CONTEXT_REPLAY_ARGS)

OHLCV_ARCHIVE_BACKFILL_ARGS ?=
ohlcv-archive-backfill:
	$(PYTHON) scripts/research/run_ohlcv_archive_backfill.py $(OHLCV_ARCHIVE_BACKFILL_ARGS)

FUNDING_CONTEXT_PRICE_JOIN_ARGS ?=
funding-context-price-join:
	$(PYTHON) scripts/research/run_funding_context_price_join.py $(FUNDING_CONTEXT_PRICE_JOIN_ARGS)

FUNDING_THRESHOLD_SENSITIVITY_ARGS ?=
funding-threshold-sensitivity:
	$(PYTHON) scripts/research/run_funding_threshold_sensitivity.py $(FUNDING_THRESHOLD_SENSITIVITY_ARGS)

PRICE_ACTION_CONTEXT_LABELS_ARGS ?=
price-action-context-labels:
	$(PYTHON) scripts/research/run_price_action_context_labels.py $(PRICE_ACTION_CONTEXT_LABELS_ARGS)

PRICE_ACTION_FORWARD_RETURNS_ARGS ?=
price-action-forward-returns:
	$(PYTHON) scripts/research/run_price_action_forward_returns.py $(PRICE_ACTION_FORWARD_RETURNS_ARGS)

PRICE_ACTION_WINDOW_STABILITY_ARGS ?=
price-action-window-stability:
	$(PYTHON) scripts/research/run_price_action_window_stability.py $(PRICE_ACTION_WINDOW_STABILITY_ARGS)

PRICE_ACTION_CANDIDATE_TRIAGE_ARGS ?=
price-action-candidate-triage:
	$(PYTHON) scripts/research/run_price_action_candidate_triage.py $(PRICE_ACTION_CANDIDATE_TRIAGE_ARGS)

# Live reconciliation (shadow/live stages)
live-reconcile:
	$(PYTHON) scripts/dev/live_reconcile.py

live-intent-history-schema:
	$(PYTHON) scripts/check_live_intent_history_schema.py

live-intent-history-schema-init:
	$(PYTHON) scripts/check_live_intent_history_schema.py --init

# Script index
script-index:
	@echo "=== Operational Scripts ==="
	@echo "  make status-paper-all   — daily paper campaign check-in"
	@echo "  make recover-paper-campaigns — guarded paper campaign recovery"
	@echo "  make paper-run          — run paper campaign"
	@echo "  make check-gates        — promotion gate status"
	@echo "  make kill-switch-on/off — arm/disarm kill switch"
	@echo "  make gate-inputs        — show live gate current values"
	@echo "  make inject-test-fill   — inject a test fill (paper only)"
	@echo "  make candidate-scan     — run candidate signal scan"
	@echo "  make candidate-summary  — summarize candidate-attributed paper outcomes"
	@echo "  make candidate-outcomes — write candidate outcome report artifact"
	@echo "  make ai-operator-oversight — write read-only AI operator oversight report"
	@echo "  make live-intent-history-schema — check live intent transition-history schema"
	@echo "  make check-short-context-readiness — check short/context data readiness"
	@echo "  make check-paper-campaign-ownership — check laptop/Hetzner campaign ownership"
	@echo "  make pullback-stage0-readiness — check pullback Stage 0 readiness"
	@echo "  make pullback-stage0-baseline  — record baseline before pullback Stage 0"
	@echo "  make pullback-stage0-verify    — verify pullback Stage 0 after proof"
	@echo "  make funding-stage0-readiness  — check funding_extreme Stage 0 readiness"
	@echo "  make funding-stage0-baseline   — record baseline before funding_extreme Stage 0"
	@echo "  make funding-stage0-verify     — verify funding_extreme Stage 0 after proof"
	@echo "  make funding-context-replay    — replay stored funding_extreme context signals"
	@echo "  make ohlcv-archive-backfill    — backfill archived OHLCV for research"
	@echo "  make funding-context-price-join — join funding context to archived OHLCV"
	@echo "  make price-action-context-labels — label archived OHLCV price-action context"
	@echo "  make price-action-forward-returns — join price-action labels to forward returns"
	@echo "  make price-action-window-stability — compare price-action labels across windows"
	@echo "  make price-action-candidate-triage — rank price-action labels for manual review"
	@echo "  make live-reconcile     — reconcile live positions"
	@echo "  make paper-logs         — tail campaign logs"
	@echo "  make dev-setup          — setup developer environment"
	@echo ""
	@echo "Full script list: ls scripts/*.py"

# Short paper run for development/testing (60s instead of 3600s)
paper-run-short:
	# CBP_USE_SAMPLE_OHLCV=1 allows signal computation without live exchange
	CBP_PAPER_RUNTIME_SEC=60 CBP_USE_SAMPLE_OHLCV=1 $(PYTHON) scripts/dev/run_es_daily_trend_paper.py

# Stop a running paper campaign immediately
paper-stop-now:
	$(PYTHON) scripts/paper_stop.py --force-now

# Script Index

This is the operator-facing map for root `scripts/*.py`.

Use `docs/GOLDEN_PATH.md` for the narrow daily paper-campaign path. Use this
file when you need to know whether a script is a daily command, diagnostic,
emergency control, research tool, release helper, or specialized live-adjacent
surface.

Rules:
- Do not promote a script into the daily operator path unless it is listed in
  `## Canonical Operator`.
- Treat live, reconciliation, model-switching, short-side, exchange smoke, and
  repair scripts as specialized commands that need the relevant runbook or
  reviewer context before use.
- Keep this file aligned with root `scripts/*.py` when adding or removing root
  script entrypoints.

## Canonical Operator

These are the safe daily/operator-facing commands for the current paper evidence
campaign and local operator visibility. Some have Makefile wrappers; use the
Makefile target when one is shown.

Use `make status-paper-all` for the full daily paper check-in across the laptop
and Hetzner-owned campaigns. It is a read-only wrapper around the status targets
listed below.

| Script | Make target | Purpose |
|--------|-------------|---------|
| `bot_status.py` | — | Process status query |
| `check_promotion_gates.py` | `make check-gates` / `make check-gates-json` | Promotion gate status |
| `check_system_health.py` | — | System health summary |
| `doctor.py` | `make doctor-strict` | Diagnostic checks |
| `hetzner_account_status.py` | — | Read-only Hetzner project inventory using an OS-keyring token; never accepts a token argument |
| `killswitch.py` | `make kill-switch-on` / `make kill-switch-off` | Arm/disarm kill switch |
| `op.py` | — | Operator command surface |
| `paper_stop.py` | `make paper-stop-now` | Stop paper campaign |
| `preflight.py` | — | Pre-launch checks |
| `preflight_check.py` | — | Runtime/config preflight check |
| `report_paper_run_diagnostics.py` | — | Paper-run diagnostic report |
| `report_hetzner_paper_campaign_status.py` | `make status-paper-hetzner` | Read-only Tailscale SSH wrapper for Hetzner campaign status with timeout-aware failure reporting |
| `report_paper_campaign_status.py` | — | Read-only campaign-health formatter for configured campaign status payloads without promotion-gate coupling |
| `report_paper_gate_qualification.py` | `make status-paper-gate-qualification` / `make status-paper-gate-qualification-json` | Read-only fill-level explanation for which paper fills count toward the provenance-qualified gate and why rejected/incomplete fills do not count |
| `report_supervised_soak_status.py` | `make status-paper-soak` / `make status-paper-soak-json` | Read-only supervised paper-soak summary across configured campaigns and paper promotion gate status |
| `restore_paper_campaigns.py` | `make status-paper-campaigns` / `make restore-paper-campaigns` | Read-only status by default; explicitly restores only configured paper collectors that are not alive |
| `run_dashboard.py` | `make dashboard` | Dashboard entrypoint |
| `run_paper_sim_monitor.py` | — | Read-only paper simulation monitor, watch management, and local watch-trigger notifications |
| `backup_state.py` | — | Full-state backup/verify/restore (sqlite-API-consistent; restore refuses over live locks; see `docs/FULL_STATE_BACKUP_RESTORE_DRILL.md`) |
| `run_paper_strategy_evidence_collector.py` | `make collect-paper-strategy-evidence` / `make status-paper-strategy-evidence` / `make stop-paper-strategy-evidence` | Managed paper evidence collector; use `--daily-loop --detach` for a persistent daily process and `--max-daily-attempts` to bound retryable failures |
| `run_preflight.py` | — | Preflight entrypoint |
| `run_signal_quality_report.py` | — | Read-only signal-quality report for scoring whether qualified public-OHLCV signals were early enough; `--allow-unqualified-evidence` is research-only |
| `run_system_diagnostics.py` | `make system-diagnostics` | System diagnostics wrapper |
| `show_control_kernel_status.py` | `make kernel-status` / `make kernel-status-json` | Control-kernel status |
| `supervisor_status.py` | — | Supervisor state |
| `validate.py` | `make validate-quick` / `make validate` | Repo validation |

The root `scripts/run_paper_strategy_evidence_collector.py` is authoritative.
The nested `scripts/data/run_paper_strategy_evidence_collector.py` path is a
compatibility delegate only and must not define separate collector behavior.

## Specialized Script Inventory

Root `scripts/` currently contains 110 Python entrypoints. The scripts below are
classified so operators do not have to infer which commands are daily-safe.

### Bootstrap And Internal Helpers

- `__init__.py` — package marker.
- `_bootstrap.py` — repo-root import bootstrap helper used by scripts.

### Paper Campaign Runtime Internals

These are part of the paper runtime path or test harnesses. Prefer the
canonical collector/Makefile wrappers unless debugging a specific subprocess.

- `run_es_daily_trend_paper.py` — paper-campaign orchestrator.
- `run_paper_engine.py` — paper execution engine subprocess.
- `run_paper_scenario.py` — paper scenario runner.
- `run_strategy_runner.py` — strategy signal runner subprocess.
- `run_tick_publisher.py` — market-data snapshot publisher.

### Bot, Process, And Service Control

These affect runtime processes or live-adjacent service loops. Use only with
the relevant runbook or operator context.

- `bot_ctl.py` — historical bot control wrapper.
- `run_bot_runner.py` — managed bot service convergence runner.
- `run_bot_safe.py` — canonical safe bot launch entrypoint.
- `run_intent_consumer_safe.py` — guarded intent consumer.
- `run_intent_executor.py` — intent executor loop.
- `run_intent_executor_safe.py` — guarded intent executor.
- `run_intent_reconciler_safe.py` — guarded intent reconciler.
- `run_live_event_executor.py` — live event executor.
- `run_live_intent_consumer.py` — live intent consumer.
- `run_live_reconciler_safe.py` — guarded live reconciler.
- `run_ops_risk_gate_service.py` — ops risk-gate service.
- `run_ops_signal_adapter.py` — ops signal adapter.
- `service_ctl.py` — service control helper.
- `start_bot.py` — start supervised bot services.
- `stop_bot.py` — stop supervised bot services.
- `watchdog_ctl.py` — watchdog control helper.

### Safety, Emergency, Audit, And Reconciliation

These inspect or repair operational state. Several are safety-critical or
live-adjacent; use with the relevant docs and keep output as audit evidence.

- `audit_view.py` — read-only audit viewer.
- `audit_startup_hardening.py` — read-only startup topology and hardening audit;
  writes audit artifacts only and does not start or stop services.
- `cancel_intent.py` — cancel-flow helper.
- `check_risk_accounting_invariant.py` — risk/fill ledger invariant check.
- `crash_snapshot.py` — crash snapshot viewer/exporter.
- `paper_state_manifest.py` — create or verify deterministic SHA-256 manifests
  for paper state transfer; used by the Hetzner isolated challenger runbook.
- `reconcile_exchange_fills.py` — exchange fill reconciliation.
- `reconcile_order_dedupe.py` — order dedupe reconciliation.
- `reconcile_positions.py` — position reconciliation.
- `repair_risk_sink_failed.py` — risk-sink repair helper.
- `risk_daily_demo.py` — daily risk demo utility.
- `run_reconcile_safe_steps.py` — safe reconciliation step runner.
- `verify_no_direct_create_order.py` — static guard for direct order creation bypasses.

### Market Data, Exchange, And Connectivity

These query exchanges, refresh market metadata, or run feed loops. Smoke tests
may require network access and should not be treated as paper-campaign proof.

- `collect_market_data_multi.py` — multi-exchange market data collection.
- `market_rules_health.py` — market-rules freshness/health check.
- `refresh_market_rules.py` — market-rules refresh.
- `run_user_stream_fills.py` — user-stream fill ingestion.
- `run_ws_ticker_feed.py` — WebSocket ticker feed.
- `run_ws_ticker_feed_safe.py` — guarded WebSocket ticker feed.
- `smoke_binance.py` — Binance connectivity smoke test.
- `smoke_coinbase.py` — Coinbase connectivity smoke test.
- `smoke_exchange.py` — generic exchange smoke test.
- `smoke_gateio.py` — Gate.io connectivity smoke test.

### Cloud Provisioning And Host Safeguards

These inspect or modify cloud-provider controls. Dry-run modes are safe for
planning; apply modes are high-risk and require an accepted review.

- `hetzner_cloud_safeguards.py` — plan by default, or explicitly apply, Hetzner
  Cloud firewall, backup, and delete/rebuild protection safeguards for the paper
  host using the OS-keyring token; use `--access-mode tailscale-only` for the
  accepted no-public-inbound firewall boundary.
- `check_hetzner_paper_host_health.py` — read-only scheduled-safe wrapper around
  the Hetzner host preflight; writes
  `.cbp_state/runtime/snapshots/hetzner_paper_host_health.latest.json` and uses
  the local critical-alert fallback when the preflight fails. It does not SSH,
  restore, stop, or start collectors.
- `hetzner_paper_host_preflight.py` — read-only host readiness check for the
  accepted Hetzner isolated paper challenger path before state transfer or
  collector restore; includes repo/venv/Git/NTP/Tailscale/campaign checks plus
  backup directory, free-space, and free-inode storage checks.

### Candidate, Signal, Learning, And Research

These are research or advisory surfaces unless a separate promotion/activation
decision makes them authoritative.

- `apply_pending_model_switch.py` — apply an approved pending model switch.
- `approve_model_switch.py` — approve a pending model switch.
- `candidate_trade_summary.py` — read-only candidate trade attribution summary;
  use `make candidate-summary`.
- `check_pullback_stage0_readiness.py` — read-only readiness report for the
  accepted `pullback_recovery_default` Stage 0 proof; use
  `make pullback-stage0-readiness`. Writes report artifacts only and prints the
  15-minute operator-run proof command without starting the collector.
- `check_short_context_readiness.py` — read-only short/context data readiness
  check over stored crypto-edge evidence; use
  `make check-short-context-readiness`. It does not contact exchanges or enable
  replay/execution.
- `check_paper_campaign_ownership.py` — read-only laptop/Hetzner campaign
  ownership check; use `make check-paper-campaign-ownership`. It does not SSH,
  restore, stop, or start collectors.
- `check_paper_campaign_runtime_ownership.py` — read-only runtime ownership
  check over already-captured laptop and Hetzner status JSON payloads. It does
  not SSH, restore, stop, or start collectors.
- `plan_managed_paper_campaigns.py` — read-only managed paper-campaign proposal
  planner; writes proposal artifacts only and does not mutate manifests or
  start campaigns.
- `run_candidate_outcome_report.py` — read-only candidate-vs-paper-outcome
  report that writes `.cbp_state/data/candidate_outcomes/` artifacts; use
  `make candidate-outcomes`.
- `run_ai_operator_oversight.py` — read-only one-shot AI operator oversight
  report over existing paper-sim monitor, watch-report, and paper-gate facts;
  use `make ai-operator-oversight`.
- `collect_live_crypto_edge_snapshot.py` — live crypto edge snapshot collection.
- `load_sample_crypto_edge_data.py` — load sample crypto edge data.
- `phase82_apply.py` — phase-specific migration/apply helper.
- `record_crypto_edge_snapshot.py` — record crypto edge snapshot.
- `recompute_signal_reliability.py` — recompute signal reliability.
- `register_evidence_source.py` — evidence-source registration helper.
- `run_phase1_safety.py` — phase 1 safety check wrapper.
- `smoke_phase1_copilot.py` — phase 1 copilot smoke test.
- `test_evidence_webhook_roundtrip.py` — evidence webhook round-trip utility.
- `verify_pullback_stage0_proof.py` — read-only pullback Stage 0 proof
  baseline/verifier; use `make pullback-stage0-baseline` immediately before
  the 15-minute proof, then `make pullback-stage0-verify` after the proof to
  verify public-OHLCV provenance, post-baseline completion, expected commit,
  and canonical fill-count isolation.

### Validation, Alignment, Release, And Maintenance

These are developer/release commands. They can be safe to run locally, but they
are not paper-campaign controls.

- `bootstrap.py` — bootstrap helper.
- `check_repo_alignment.py` — repo alignment guard.
- `generate_release_notes.py` — release-notes generator.
- `install.py` — install/setup helper.
- `set_hetzner_api_token.py` — interactively store/status/delete the Hetzner token in the OS keyring; never accepts a token argument.
- `maintenance.py` — maintenance task runner.
- `pre_release_sanity.py` — pre-release sanity checks.
- `rebuild_remaining_tasks.py` — regenerate remaining-task artifacts.
- `release_checklist.py` — release checklist wrapper.
- `release_validate_manifest.py` — release manifest validator.
- `rotate_logs.py` — log rotation.
- `sync_briefcase_requires.py` — Briefcase requirement sync.
- `tag_release.py` — local tag helper.
- `validate_script_paths.py` — script path/index validator.

### Desktop And UI

These launch or support UI/desktop surfaces. They are optional operator surfaces
unless the deployment path explicitly uses them.

- `run_desktop.py` — desktop app entrypoint.
- `run_desktop_launcher.py` — desktop launcher.

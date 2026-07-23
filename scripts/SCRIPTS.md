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
| `check_ohlcv_preflight.py` | — | Read-only public-OHLCV reachability preflight before governed Stage 0 runs; exit 2 means source/network unreachable, not a strategy result |
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
| `report_hetzner_crypto_edge_runtime_status.py` | `make status-hetzner-edge-runtime` | Read-only Tailscale SSH wrapper for Hetzner crypto-edge runtime readiness; checks accepted checkout/tooling, OKX collector plan, collector status under the deployed `CBP_STATE_DIR`, and collector/cadence scheduling without deploying or starting collectors |
| `report_paper_campaign_status.py` | — | Read-only campaign-health formatter for configured campaign status payloads without promotion-gate coupling |
| `report_paper_gate_qualification.py` | `make status-paper-gate-qualification` / `make status-paper-gate-qualification-json` | Read-only fill-level explanation for which paper fills count toward the provenance-qualified gate and why rejected/incomplete fills do not count |
| `report_supervised_soak_status.py` | `make status-paper-soak` / `make status-paper-soak-json` | Read-only supervised paper-soak summary across configured campaigns and paper promotion gate status |
| `restore_paper_campaigns.py` | `make status-paper-campaigns` / `make restore-paper-campaigns` / `make recover-paper-campaigns` | Read-only status by default; explicitly restores only configured paper collectors that are not alive; `--restore --preflight-ohlcv` blocks launches when the configured public-OHLCV source is unreachable; `--restart-unhealthy` is opt-in and preflight-required for alive unhealthy collectors |
| `run_dashboard.py` | `make dashboard` | Dashboard entrypoint |
| `install_systemd_units.py` | — | Verify and install rendered systemd units from `packaging/systemd/` (dry-run by default; `--repo-dir` targets non-default checkout paths; never arms live trading) |
| `check_live_intent_history_schema.py` | `make live-intent-history-schema` / `make live-intent-history-schema-init` | Check whether the current runtime live-intent queue has `live_trade_intent_events`; read-only by default, `--init` explicitly initializes/migrates the existing queue schema |
| `run_paper_sim_monitor.py` | — | Read-only paper simulation monitor, watch management, and local watch-trigger notifications |
| `backup_state.py` | — | Full-state backup/verify/restore (sqlite-API-consistent; restore refuses over live locks; see `docs/FULL_STATE_BACKUP_RESTORE_DRILL.md`) |
| `run_paper_strategy_evidence_collector.py` | `make collect-paper-strategy-evidence` / `make status-paper-strategy-evidence` / `make stop-paper-strategy-evidence` | Managed paper evidence collector; use `--daily-loop --detach` for a persistent daily process and `--max-daily-attempts` to bound retryable failures |
| `update_paper_campaign_manifest.py` | — | Audited schema-v1 paper-campaign manifest enable/disable update; requires a `campaign_manifest_change` operator event before writing |
| `run_preflight.py` | — | Preflight entrypoint |
| `run_signal_quality_report.py` | — | Read-only signal-quality report for scoring whether qualified public-OHLCV signals were early enough; `--allow-unqualified-evidence` is research-only |
| `run_system_diagnostics.py` | `make system-diagnostics` | System diagnostics wrapper |
| `show_control_kernel_status.py` | `make kernel-status` / `make kernel-status-json` / `make kernel-promote` | Control-kernel status; `--promote` is gate-enforced and fails closed unless the supported promotion gate is ready |
| `supervisor_status.py` | — | Supervisor state |
| `validate.py` | `make validate-quick` / `make validate` | Repo validation |

The root `scripts/run_paper_strategy_evidence_collector.py` is authoritative.
The nested `scripts/data/run_paper_strategy_evidence_collector.py` path is a
compatibility delegate only and must not define separate collector behavior.

## Specialized Script Inventory

Root `scripts/` currently contains 127 Python entrypoints. The scripts below are
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
- `check_funding_stage0_readiness.py` — read-only readiness report for the
  `funding_extreme_default` Stage 0 proof; use
  `make funding-stage0-readiness`. Verifies the known preconditions
  (public-OHLCV reachability, crypto-edge cadence, and fresh OKX funding
  context) and prints the 15-minute operator-run proof command without starting
  the collector. Use `FUNDING_STAGE0_ARGS="--venue okx"` when Coinbase
  public-OHLCV reachability is the blocker and OKX public OHLCV is the intended
  proof source.
  The generated proof command keeps the paper run's `CBP_STATE_DIR` isolated
  while passing `CBP_CRYPTO_EDGE_DB_PATH` / `--strategy-context-db-path` so the
  strategy can read the same crypto-edge store the readiness check validated.
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
- `report_execution_cost_stack.py` — read-only research report over stored
  `shadow_would_be_fill` records; computes taker cost and quote-only maker
  metrics, requires stored subsequent price path before fill-probability
  conclusions, and never changes routing, order type, or paper campaign
  behavior.
- `research/run_funding_context_replay.py` — read-only `funding_extreme`
  signal-distribution replay over stored crypto-edge funding snapshots; writes
  dataset-hashed JSON artifacts only and does not compute PnL, expectancy, or
  promotion evidence. Use `make funding-context-replay`.
- `research/run_ohlcv_archive_backfill.py` — research-data ingestion tool that
  backfills the local market OHLCV archive from public exchange OHLCV and
  writes a dataset-hashed JSON summary; it does not affect campaigns, gates,
  or trading. Use `make ohlcv-archive-backfill`.
- `research/run_funding_context_price_join.py` — read-only
  `funding_extreme` forward-return report joining stored funding snapshots to
  archived OHLCV rows; computes unit-size modeled forward returns only and
  does not simulate portfolio PnL, expectancy, campaign state, or promotion
  eligibility. Use `make funding-context-price-join`.
- `research/run_funding_threshold_sensitivity.py` — read-only
  `funding_extreme` threshold sensitivity report over an existing
  funding-context price-join JSON artifact; recomputes hypothetical
  action counts and unit-size modeled forward returns for explicit threshold
  grids, does not change strategy config, fetch data, start campaigns, or
  produce promotion evidence. Use `make funding-threshold-sensitivity`.
- `research/run_price_action_context_labels.py` — read-only OHLCV
  price-action context label artifact over the existing market archive;
  labels fair-value gaps, engulfing candles, swing failures, break/retest,
  rejection wicks, displacement bars, opening-range state, and
  acceptance/rejection context without changing strategy config, campaigns,
  gates, or promotion evidence. Use `make price-action-context-labels`.
- `research/run_price_action_forward_returns.py` — read-only
  label-conditioned forward-return report over archived OHLCV; computes
  unit-size long/short modeled returns after explicit fee/slippage assumptions
  for price-action label buckets and does not change strategy config,
  campaigns, gates, execution, or promotion evidence. Use
  `make price-action-forward-returns`.
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
- `verify_funding_stage0_proof.py` — read-only `funding_extreme` Stage 0 proof
  baseline/verifier; use `make funding-stage0-baseline` immediately before the
  15-minute proof, then `make funding-stage0-verify` after the proof to verify
  public-OHLCV provenance, fresh funding-context consumption, post-baseline
  completion, expected commit, and canonical fill-count isolation. Pass the
  same `FUNDING_STAGE0_ARGS` to baseline and verify if the proof uses a
  non-default OHLCV venue/symbol. If the proof uses an isolated state dir plus
  a shared crypto-edge store, preserve the readiness-generated
  `CBP_CRYPTO_EDGE_DB_PATH` / `--strategy-context-db-path` values.

### Validation, Alignment, Release, And Maintenance

These are developer/release commands. They can be safe to run locally, but they
are not paper-campaign controls.

- `bootstrap.py` — bootstrap helper.
- `check_repo_alignment.py` — repo alignment guard.
- `generate_release_notes.py` — release-notes generator.
- `install.py` — install/setup helper.
- `audit_coverage_matrix.py` — operator/action audit coverage matrix (SHOWN/PARTIAL/MISSING per policy family; `--strict` capped-live posture; see `docs/OPERATOR_ACTION_AUDIT_COVERAGE.md`).
- `record_operator_event.py` — append one manual operator/action audit event to
  the unified JSONL journal; redacts secret-like payload fields.
- `check_operator_arm_to_halt_replay.py` — replay a live arm/resume event
  followed by halt/disable from operator-event journal records; writes
  launch-packet evidence with `--evidence-dest`.
- `check_operator_event_secrets.py` — scan operator event journal payloads for
  unredacted secret-like fields without printing leaked values; `--require-events`
  is the launch-packet posture.
- `check_dead_man.py` — dead-man liveness check over trading-loop heartbeats (exit 0/1/2; `--alert` dispatches via the alert stack; driven by `packaging/systemd/cbp-dead-man.timer`).
- `check_edge_cadence.py` — read-only crypto-edge collector cadence/dead-man check over stored funding/OI/basis snapshot timestamps (exit 0/1/2; `--alert` best-effort; schedulable by `packaging/systemd/cbp-edge-cadence.timer`).
- `check_supply_chain.py` — pin integrity + environment match + optional pip-audit lane; `--evidence-dest` writes launch-packet provenance JSON (see `docs/SUPPLY_CHAIN_RELEASE_POLICY.md`).
- `check_cost_assumptions.py` — read-only paper fee/slippage cost-assumption
  validator for the active `user.yaml`; reports paper-fill, evidence-scoring,
  dormant lookup, and backtest cost surfaces without mutating config or trading
  state.
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

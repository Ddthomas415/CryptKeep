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

Executable guard:
- `tests/test_script_index_alignment_guard.py` pins the alignment boundary
  among this file, `docs/GOLDEN_PATH.md`, `REMAINING_TASKS.md`, and the
  Makefile `script-index` target. Update that guard in the same change when a
  command is promoted into the daily operator path, moved out of it, or given a
  new Makefile wrapper.

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
| `report_hetzner_paper_campaign_status.py` | `make status-paper-hetzner` | Read-only remote wrapper for Hetzner campaign status with timeout-aware failure reporting; the script and Make target default to direct `ssh` to the Tailscale IP and support `HETZNER_STATUS_TRANSPORT=tailscale-ssh` when Tailscale SSH browser auth is intentionally preferred |
| `report_hetzner_crypto_edge_runtime_status.py` | `make status-hetzner-edge-runtime` | Read-only remote wrapper for Hetzner crypto-edge runtime readiness; the script and Make target default to direct `ssh` to the Tailscale IP, support `HETZNER_STATUS_TRANSPORT=tailscale-ssh`, and checks accepted checkout/tooling, OKX collector plan, collector status under the deployed `CBP_STATE_DIR`, collector/cadence scheduling, and fresh funding/open-interest/basis cadence without deploying or starting collectors |
| `report_hetzner_dependency_alignment_status.py` | `make status-hetzner-dependency-alignment` / `make status-hetzner-dependency-alignment-json` | Read-only remote wrapper for Hetzner dependency alignment; runs the host supply-chain checker and `pip install --dry-run -r requirements-pinned.txt`, reports pin/environment mismatches and dry-run package deltas, and never installs packages, deploys code, or restarts services |
| `report_roadmap_tracking_status.py` | `make roadmap-tracking-status` / `make roadmap-tracking-status-json` | Read-only roadmap organizer report over `docs/ROADMAP_TRACKING_CHECKLIST.md`; verifies linked source docs, required status commands, and non-authority boundaries without running campaigns, fetching market data, closing proof, deciding backlog items, or mutating state |
| `report_backlog_lane_status.py` | `make backlog-lane-status` / `make backlog-lane-status-json` | Read-only planning report over `docs/BACKLOG_EXECUTION_LANES.md`; supports `BACKLOG_LANE_STATUS_LANE`; summarizes backlog lane counts and source hashes without deciding backlog items or changing runtime state |
| `report_operator_proof_status.py` | `make operator-proof-status` / `make operator-proof-status-json` | Read-only report over passive/operator-evidence lane items and proof/coverage markers in `REMAINING_TASKS.md`; supports `OPERATOR_PROOF_STATUS_CATEGORY`, `OPERATOR_PROOF_STATUS_LINE`, and `OPERATOR_PROOF_STATUS_PASSIVE_ORDINAL`; focused proof filters suppress unrelated passive rows while preserving source counts; includes proof next actions without running campaigns, fetching market data, closing proof, or mutating state |
| `report_operator_read_only_command_status.py` | `make operator-read-only-command-status` / `make operator-read-only-command-status-json` | Read-only wiring inventory for medium-lane operator command surfaces: campaign planners, gate diagnostics, optional reports, host diagnostics, host status wrappers, and platform-event packet checks; supports `OPERATOR_READ_ONLY_COMMAND_STATUS_MEDIUM_LANE_ITEM` and `OPERATOR_READ_ONLY_COMMAND_STATUS_COMMAND_ID`; does not run commands, campaigns, market-data fetches, proof closure, or runtime mutation |
| `report_operator_status_bundle.py` | `make operator-status` / `make operator-status-json` | Read-only bundle of backlog lane, research pipeline, research artifact inventory, research command, operator read-only command, and operator proof status reports for check-ins; supports `OPERATOR_STATUS_SECTION` and underlying backlog/research-pipeline/research-artifact/research-command/operator-read-only/proof filters, including `OPERATOR_STATUS_BACKLOG_LANE_ORDINAL`, `OPERATOR_STATUS_RESEARCH_ARTIFACT_LANE`, `OPERATOR_STATUS_RESEARCH_ARTIFACT_ID`, `OPERATOR_STATUS_OPERATOR_READ_ONLY_MEDIUM_LANE_ITEM`, proof category/line, and `OPERATOR_STATUS_OPERATOR_PROOF_PASSIVE_ORDINAL`; surfaces next actions without running pipelines/campaigns/commands, fetching market data, closing proof, deciding backlog items, or mutating state |
| `report_operator_next_actions.py` | `make operator-next-actions` / `make operator-next-actions-json` / `make operator-next-actions-passive-json` | Read-only compact next-action report derived from operator status; includes roadmap tracking, research pipeline, research artifact, research command, operator read-only command, passive operator-evidence, and proof-marker action lanes; supports `OPERATOR_NEXT_ACTIONS_MAX`, `OPERATOR_NEXT_ACTIONS_LANE`, `OPERATOR_NEXT_ACTIONS_REASON`, `OPERATOR_NEXT_ACTIONS_EXCLUDE_REASON`, `OPERATOR_NEXT_ACTIONS_SOURCE`, and source-report filters (`OPERATOR_NEXT_ACTIONS_BACKLOG_LANE`, `OPERATOR_NEXT_ACTIONS_BACKLOG_LANE_ORDINAL`, `OPERATOR_NEXT_ACTIONS_RESEARCH_PIPELINE`, `OPERATOR_NEXT_ACTIONS_RESEARCH_ARTIFACT_LANE`, `OPERATOR_NEXT_ACTIONS_RESEARCH_ARTIFACT_ID`, `OPERATOR_NEXT_ACTIONS_RESEARCH_COMMAND_LANE`, `OPERATOR_NEXT_ACTIONS_RESEARCH_COMMAND_INPUT_CLASS`, `OPERATOR_NEXT_ACTIONS_RESEARCH_COMMAND_ID`, `OPERATOR_NEXT_ACTIONS_OPERATOR_READ_ONLY_MEDIUM_LANE_ITEM`, `OPERATOR_NEXT_ACTIONS_OPERATOR_READ_ONLY_COMMAND_ID`, `OPERATOR_NEXT_ACTIONS_OPERATOR_PROOF_CATEGORY`, `OPERATOR_NEXT_ACTIONS_OPERATOR_PROOF_LINE`, `OPERATOR_NEXT_ACTIONS_OPERATOR_PROOF_PASSIVE_ORDINAL`); `operator-next-actions-passive[-json]` is the standard passive-operator-evidence view with host-side, proof-ready, capped-live, and coverage rows excluded; does not run research, campaigns, commands, market-data fetches, proof closure, or runtime mutation |
| `report_operator_briefing.py` | `make operator-briefing` / `make operator-briefing-json` / `make record-operator-briefing` | Read-only advisory briefing over existing operator status, next-action, paper-gate velocity, cost-assumption, and campaign-status reports; uses `PAPER_CAMPAIGN_CONFIG` for the campaign section so it matches `status-paper-campaigns`; summarizes campaign/gate/cost/action state and recommendations without moving capital, starting/stopping campaigns, fetching market data, changing config, promoting strategies, or mutating runtime state. `record-operator-briefing` writes latest and timestamped JSON/Markdown briefing artifacts under `.cbp_state/data/operator_briefing/` for daily/on-demand operator checkpoints |
| `report_paper_campaign_status.py` | — | Read-only campaign-health formatter for configured campaign status payloads without promotion-gate coupling |
| `report_paper_gate_qualification.py` | `make status-paper-gate-qualification` / `make status-paper-gate-qualification-json` | Read-only fill-level explanation for which paper fills count toward the provenance-qualified gate and why rejected/incomplete fills do not count |
| `report_paper_gate_velocity.py` | `make status-paper-gate-velocity` / `make status-paper-gate-velocity-json` / `make record-paper-gate-velocity` | Read-only paper-gate velocity report by default; estimates completion from completed provenance-qualified round-trip close cadence and qualified source-bar cadence, then reports the slower active blocker while keeping legacy/all-history fills diagnostic only. `record-paper-gate-velocity` writes the current report under `.cbp_state/data/paper_gate_velocity/` as operator evidence |
| `report_supervised_soak_status.py` | `make status-paper-soak` / `make status-paper-soak-json` | Read-only supervised paper-soak summary across configured campaigns and paper promotion gate status |
| `restore_paper_campaigns.py` | `make status-paper-campaigns` / `make restore-paper-campaigns` / `make recover-paper-campaigns` | Read-only status by default; explicitly restores only configured paper collectors that are not alive; `--restore --preflight-ohlcv` blocks launches when the configured public-OHLCV source is unreachable; `--restart-unhealthy` is opt-in and preflight-required for alive unhealthy collectors |
| `run_dashboard.py` | `make dashboard` | Dashboard entrypoint |
| `install_systemd_units.py` | — | Verify and install rendered systemd units from `packaging/systemd/` (dry-run by default; `--repo-dir` targets non-default checkout paths; never arms live trading) |
| `check_live_intent_history_schema.py` | `make live-intent-history-schema` / `make live-intent-history-schema-json` / `make live-intent-history-schema-init` | Check whether the current runtime live-intent queue has `live_trade_intent_events`; read-only by default, `--init` explicitly initializes/migrates the existing queue schema |
| `run_paper_sim_monitor.py` | — | Read-only paper simulation monitor, watch management, and local watch-trigger notifications |
| `backup_state.py` | `make backup-state STATE_BACKUP_DEST=<backup_dir>` | Full-state backup/verify/restore (sqlite-API-consistent; restore refuses over live locks; see `docs/FULL_STATE_BACKUP_RESTORE_DRILL.md`) |
| `run_paper_strategy_evidence_collector.py` | `make collect-paper-strategy-evidence` / `make status-paper-strategy-evidence` / `make stop-paper-strategy-evidence` | Managed paper evidence collector; use `--daily-loop --detach` for a persistent daily process and `--max-daily-attempts` to bound retryable failures |
| `update_paper_campaign_manifest.py` | — | Audited schema-v1 paper-campaign manifest enable/disable update; requires a `campaign_manifest_change` operator event before writing |
| `run_preflight.py` | — | Preflight entrypoint |
| `run_signal_quality_report.py` | — | Read-only signal-quality report for scoring whether qualified public-OHLCV signals were early enough; `--allow-unqualified-evidence` is research-only |
| `run_system_diagnostics.py` | `make system-diagnostics` | System diagnostics wrapper |
| `smoke_exchange.py` | `make smoke-exchange-sandbox` / `make record-exchange-sandbox-smoke` / `make record-exchange-sandbox-exception` | Exchange sandbox smoke check; `record-exchange-sandbox-smoke` writes standard evidence under `.cbp_state/data/exchange_sandbox_smoke/`; `record-exchange-sandbox-exception` records an explicit operator exception after restricted-location evidence |
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
- `smoke_exchange.py` — generic exchange smoke test; use
  `make smoke-exchange-sandbox` for the standard sandbox orderbook smoke.
- `smoke_gateio.py` — Gate.io connectivity smoke test.

### Cloud Provisioning And Host Safeguards

These inspect or modify cloud-provider controls. Dry-run modes are safe for
planning; apply modes are high-risk and require an accepted review.

- `hetzner_cloud_safeguards.py` — plan by default, or explicitly apply, Hetzner
  Cloud firewall, backup, and delete/rebuild protection safeguards for the paper
  host using the OS-keyring token; use `--access-mode tailscale-only` for the
  accepted no-public-inbound firewall boundary.
- `report_hetzner_paper_host_health.py` — read-only laptop/operator wrapper
  that runs the Hetzner host-health check on the Hetzner host through the same
  direct-SSH-to-Tailscale-IP path as `make status-paper-hetzner`; this is what
  `make check-hetzner-paper-host-health` invokes from a laptop.
- `check_hetzner_paper_host_health.py` — read-only scheduled-safe host-local wrapper around
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
- `plan_multi_symbol_paper_campaigns.py` — paper-only multi-symbol candidate
  campaign generator; scans a symbol universe, ranks strategy/symbol candidates,
  OHLCV-preflights proposed rows, and writes proposal artifacts only without
  mutating active manifests or starting campaigns. Use
  `make plan-multi-symbol-paper-campaigns-json` for the default read-only
  `--no-write` proposal check.
- `report_hetzner_multi_venue_proposal_status.py` — read-only status check for
  the disabled Hetzner Gate.io/Binance paper-research proposal manifest. Use
  `make status-hetzner-multi-venue-proposals-json` for structure-only checks,
  or add `HETZNER_MULTI_VENUE_PROPOSAL_ARGS=--preflight` to run public-OHLCV
  preflights without enabling campaigns, mutating manifests, counting canonical
  promotion evidence, or routing orders. Binance remains behind
  `CBP_VENUE=binance CBP_ALLOW_BINANCE=1`.
- `make status-hetzner-gateio-challenger` reports the isolated Gate.io
  challenger manifest after it is present on Hetzner. `make
  restore-hetzner-gateio-challenger` is the reviewed, preflight-required
  restore path for that single paper/research candidate; it must not be run
  from a stale host checkout.
- `make status-hetzner-binance-challenger` reports the isolated Binance
  challenger manifest after it is present on Hetzner. `make
  restore-hetzner-binance-challenger` is the reviewed, preflight-required
  restore path for that single paper/research candidate and runs with
  `CBP_VENUE=binance CBP_ALLOW_BINANCE=1`; it must not be run from a stale
  host checkout.
- `run_candidate_outcome_report.py` — read-only candidate-vs-paper-outcome
  report that writes `.cbp_state/data/candidate_outcomes/` artifacts; use
  `make candidate-outcomes`.
- `report_execution_cost_stack.py` — read-only research report over stored
  `shadow_would_be_fill` records; computes taker cost and quote-only maker
  metrics, requires stored subsequent price path before fill-probability
  conclusions, and never changes routing, order type, or paper campaign
  behavior. Use `make record-execution-cost-stack` to write the standard
  artifact.
- `research/run_funding_context_replay.py` — read-only `funding_extreme`
  signal-distribution replay over stored crypto-edge funding snapshots; writes
  dataset-hashed JSON artifacts only and does not compute PnL, expectancy, or
  promotion evidence. Use `make funding-context-replay`.
- `research/run_ohlcv_archive_backfill.py` — research-data ingestion tool that
  backfills the local market OHLCV archive from public exchange OHLCV and
  writes a dataset-hashed JSON summary; it does not affect campaigns, gates,
  or trading. Use `make ohlcv-archive-backfill`.
- `research/run_archive_walk_forward.py` — research-only archive-backed
  anchored walk-forward runner for one strategy config; writes a dataset-hashed
  JSON artifact, does not sweep or rank parameters, and does not create
  promotion evidence. Use `make archive-walk-forward`.
- `research/run_archive_parameter_sweep.py` — research-only archive-backed
  parameter sweep over an explicit grid; ranks descriptive walk-forward
  artifacts only and does not promote, mutate, or select strategy configs. Use
  `make archive-parameter-sweep`.
- `research/run_archive_parameter_sweep_triage.py` — read-only triage report
  over an existing `archive_backed_parameter_sweep_v1` JSON artifact; ranks
  sweep variants for manual review only and does not rerun backtests, change
  strategy config, start campaigns, or produce promotion evidence. Use
  `make archive-parameter-sweep-triage`.
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
- `research/run_funding_threshold_window_stability.py` — read-only
  funding-threshold window-stability report over an existing
  funding-context price-join JSON artifact; compares threshold-pair behavior
  across fixed row windows and does not change strategy config, campaigns,
  gates, execution, or promotion evidence. Use
  `make funding-threshold-window-stability`.
- `research/run_funding_threshold_candidate_triage.py` — read-only
  funding-threshold candidate triage report over an existing
  `funding_threshold_sensitivity_v1` JSON artifact; ranks threshold pairs for
  manual review only and does not change strategy config, campaigns, gates,
  execution, or promotion evidence. Use
  `make funding-threshold-candidate-triage`.
- `research/run_funding_threshold_stability_triage.py` — read-only
  stability-aware funding-threshold triage report over an existing
  `funding_threshold_window_stability_v1` JSON artifact; ranks threshold pairs
  for manual review only and does not change strategy config, campaigns, gates,
  execution, or promotion evidence. Use
  `make funding-threshold-stability-triage`.
- `research/run_funding_threshold_research_pipeline.py` — read-only pipeline
  wrapper that runs the accepted funding context price-join, sensitivity,
  direct triage, window-stability, and stability-triage reports in sequence
  and writes a summary manifest. It does not change collectors, strategy
  config, campaigns, gates, ingestion, execution, or promotion evidence. Use
  `make funding-threshold-research-pipeline`.
- `research/run_crypto_edge_strategy_readiness.py` — read-only crypto-edge
  strategy readiness matrix over current source-tree wiring; classifies
  `funding_extreme`, `open_interest_shift`, and `order_book_imbalance` as
  Stage 0 wired, config-only, or unregistered without fetching data, starting
  campaigns, or changing promotion gates. Use
  `make crypto-edge-strategy-readiness`.
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
- `research/run_price_action_window_stability.py` — read-only multi-window
  price-action stability report over archived OHLCV; compares label-conditioned
  forward returns against unconditioned baselines across windows and does not
  change strategy config, campaigns, gates, execution, or promotion evidence.
  Use `make price-action-window-stability`.
- `research/run_price_action_candidate_triage.py` — read-only price-action
  candidate triage report over archived OHLCV; ranks label/side pairs for
  manual review only and does not change strategy config, campaigns, gates,
  execution, or promotion evidence. Use `make price-action-candidate-triage`.
- `research/run_price_action_research_pipeline.py` — read-only pipeline wrapper
  that runs the accepted price-action labels, forward-returns, window-stability,
  and candidate-triage reports in sequence and writes a summary manifest. It
  does not change strategy config, campaigns, gates, ingestion, execution, or
  promotion evidence. Use `make price-action-research-pipeline`.
- `research/report_research_pipeline_status.py` — read-only status report over
  accepted research pipeline wiring and latest summary artifacts. It checks
  script/Makefile/SCRIPTS registration and reports whether the latest
  funding-threshold and price-action `pipeline_summary.json` artifacts are
  present and `ok=true`, with `blocking_reason`/`next_action` fields for
  missing artifacts or wiring drift; it does not run pipelines, fetch data, or mutate
  research, strategy, campaign, gate, or execution state. Use
  `make research-pipeline-status` or `make research-pipeline-status-json`;
  supports `RESEARCH_PIPELINE_STATUS_PIPELINE` for one-pipeline views.
- `research/report_research_artifact_inventory.py` — read-only inventory over
  accepted archive, funding-threshold, and price-action research artifacts. It
  reports latest artifact path, hash, marker, status, producer-plan metadata,
  and next action for missing or malformed artifacts; it does not run research
  jobs, fetch data, write artifacts, choose producer inputs, or mutate
  strategy, campaign, gate, or execution state. Use
  `make research-artifact-inventory` or
  `make research-artifact-inventory-json`; supports
  `RESEARCH_ARTIFACT_INVENTORY_LANE` and
  `RESEARCH_ARTIFACT_INVENTORY_ARTIFACT_ID` for focused views.
- `research/report_research_command_status.py` — read-only status report over
  accepted research command wiring and input classes. It checks script,
  Makefile target, and SCRIPTS registration for archive, funding, price-action,
  and status research commands, with `blocking_reason`/`next_action` fields for
  wiring drift; it does not run research jobs, fetch data, generate artifacts,
  or mutate strategy, campaign, gate, or execution state.
  Use `make research-command-status` or `make research-command-status-json`;
  supports `RESEARCH_COMMAND_STATUS_LANE` and
  `RESEARCH_COMMAND_STATUS_INPUT_CLASS` /
  `RESEARCH_COMMAND_STATUS_COMMAND_ID` for focused views.
- `run_ai_operator_oversight.py` — read-only one-shot AI operator oversight
  report over existing paper-sim monitor, watch-report, and paper-gate facts;
  use `make ai-operator-oversight`.
- `report_operator_briefing.py` — read-only advisory briefing over existing
  operator status, next-action, paper-gate velocity, and cost-assumption
  reports; use `make operator-briefing`, `make operator-briefing-json`, or
  `make record-operator-briefing` for latest and timestamped artifacts.
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
  Passive operator-evidence decisions recognized by
  `report_operator_proof_status.py` use
  `--action passive_operator_decision` with one of these targets:
  `manual_strategy_performance_decision`,
  `composite_hybrid_paper_advancement_decision`, or
  `funding_extreme_persistent_campaign_decision`. Accepted result values for
  those passive decisions include `accepted`, `accepted_with_risk`,
  `declined`, `research_only`, and `no_persistent_campaign`. Standard passive
  decision records can be written through
  `make record-manual-strategy-performance-decision OPERATOR_DECISION_REASON='<reason>'`,
  `make record-composite-hybrid-paper-decision OPERATOR_DECISION_REASON='<reason>'`,
  or
  `make record-funding-extreme-persistent-campaign-decision OPERATOR_DECISION_REASON='<reason>'`.
  Runbook checkpoints recognized by `report_operator_proof_status.py` can be
  written through
  `make record-hetzner-state-migration-checkpoint OPERATOR_CHECKPOINT_REASON='<reason>'`,
  `make record-paper-to-shadow-first-hour-checkpoint OPERATOR_CHECKPOINT_REASON='<reason>'`,
  `make record-backup-restore-drill-checkpoint OPERATOR_CHECKPOINT_REASON='<reason>'`,
  or
  `make record-server-secrets-rotation-checkpoint OPERATOR_CHECKPOINT_REASON='<reason>'`.
- `check_operator_arm_to_halt_replay.py` — replay a live arm/resume event
  followed by halt/disable from operator-event journal records; supports
  `make operator-arm-to-halt-replay[-json]` and
  `OPERATOR_ARM_TO_HALT_REPLAY_PATH`; `make record-operator-arm-to-halt-replay`
  writes standard replay evidence under
  `.cbp_state/data/operator_arm_to_halt_replay/`.
- `check_operator_event_secrets.py` — scan operator event journal payloads for
  unredacted secret-like fields without printing leaked values; supports
  `make operator-event-secrets[-json]`, `OPERATOR_EVENT_PATH`,
  `OPERATOR_EVENT_REQUIRE_EVENTS`, `OPERATOR_EVENT_REQUIRE_ACTION`, and
  `OPERATOR_EVENT_EVIDENCE_DEST`;
  `make record-operator-event-secrets` runs the launch-packet posture with
  `--require-events`. `make record-ai-provider-event-secrets` and
  `make record-ai-report-event-secrets` additionally require real
  `ai_copilot_external_provider_call` or `ai_copilot_report_write` events.
- `check_backup_artifact_secrets.py` — scan a backup artifact directory for
  high-confidence secret indicators without printing leaked values; supports
  `make check-backup-artifact-secrets STATE_BACKUP_ARTIFACT=<backup_dir>` and
  records a `state_backup_secret_scan` operator event.
- `check_dead_man.py` — dead-man liveness check over trading-loop heartbeats;
  supports `make check-dead-man[-json]`, `DEAD_MAN_NAMES`, and
  `DEAD_MAN_MAX_AGE_S`; exit 0/1/2; `--alert` dispatches via the alert stack;
  driven by `packaging/systemd/cbp-dead-man.timer`.
- `check_edge_cadence.py` — read-only crypto-edge collector cadence/dead-man
  check over stored funding/OI/basis snapshot timestamps; supports
  `make check-edge-cadence[-json]` and `EDGE_CADENCE_STORE_PATH`; exit 0/1/2;
  `--alert` best-effort; schedulable by
  `packaging/systemd/cbp-edge-cadence.timer`.
- `check_supply_chain.py` — pin integrity + environment match + optional
  pip-audit lane; supports `make check-supply-chain[-json]` and
  `make record-supply-chain`; `record-supply-chain` writes standard
  provenance evidence under `.cbp_state/data/supply_chain/` (see
  `docs/SUPPLY_CHAIN_RELEASE_POLICY.md`).
- `check_credential_source_posture.py` — read-only exchange credential-source
  report that names keyring/env/missing source without printing credential
  values; supports `make credential-source-posture[-json]`,
  `CREDENTIAL_SOURCE_POSTURE_VENUE`, and `--fail-on-env` for stricter manual
  checks.
- `smoke_exchange.py` — exchange sandbox smoke check; supports
  `make smoke-exchange-sandbox` and `make record-exchange-sandbox-smoke`;
  the record target writes standard evidence under
  `.cbp_state/data/exchange_sandbox_smoke/`.
- `check_cost_assumptions.py` — read-only paper fee/slippage cost-assumption
  validator for the active `user.yaml`; supports
  `make check-cost-assumptions[-json]` and `make record-cost-assumptions`;
  reports paper-fill, evidence-scoring, dormant lookup, and backtest cost
  surfaces without mutating config or trading state. The record target writes
  the current verification artifact under `.cbp_state/data/cost_assumptions/`
  and treats warning reports as recorded evidence, while fail/config errors
  still exit non-zero.
- `report_platform_event_journal.py` — read-only summary of the append-only
  platform event journal for research/campaign/evidence observability; supports
  `make platform-event-journal[-json]`; returns exit 2 with
  `--require-events` when no event rows exist.
- `check_platform_event_secrets.py` — scan platform event journal payloads for
  unredacted secret-like fields without printing leaked values; supports
  `make platform-event-secrets[-json]`, `--require-events`, and
  `--evidence-dest`.
- `check_platform_event_integrity.py` — validate platform event journal envelope
  shape and supported event types; supports `make platform-event-integrity[-json]`,
  `--require-events`, and `--evidence-dest`.
- `report_platform_event_packet.py` — read-only platform event evidence-packet
  report combining summary, integrity, and secret-scan checks; supports
  `make platform-event-packet[-json]`, `--require-events`, and
  `--evidence-dest`.
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

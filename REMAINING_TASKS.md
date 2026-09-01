# Remaining Tasks

This file is a lightweight index only.

## Current state
The active operating state is paper-evidence collection, not live launch.

SHOWN:
- `master`, `origin/master`, and `review-stabilized` are kept aligned after
  accepted PR merges. Verify the exact current boundary with
  `git rev-parse HEAD origin/master origin/review-stabilized`. 2026-07-04:
  PR #211 merged the accepted `review-stabilized` batch to `master`, then
  `review-stabilized` was fast-forwarded; all three refs were verified at
  `7861f7292b418f8ccbc53ca002635618f87a079b`.
- Laptop-owned paper campaigns are healthy as of the 2026-08-28 guarded
  recovery/status refresh:
  - `es_daily_trend_v1`: `running`, `collecting`
  - `breakout_default`: `running`, `collecting`
  - `make status-paper-soak` reported `2/2 running`
- 2026-08-31 read-only status checkpoint:
  - laptop campaigns remain `2/2 running`
  - `es_daily_trend_v1`: `idle`, `waiting_for_next_day`, `fills=20`,
    `closed=10`, `pnl=31.4369`
  - `breakout_default`: `idle`, `waiting_for_next_day`, `fills=23`,
    `closed=11`, `pnl=4.2183`
  - canonical gate remains `3/5` provenance-qualified round trips with `2`
    remaining; evidence writer status is `ok`
  - `make status-paper-gate-velocity` projects completion in `21` days at the
    current observed cadence, estimated
    `2026-09-21T05:54:47.809287+00:00`; days and qualified-bar thresholds are
    already complete, so round trips are the blocking threshold
  - checkpoint:
    `docs/checkpoints/paper_campaign_status_2026_08_31.md`
- Hetzner-owned `ema_cross_default` is healthy when checked through the
  Hetzner campaign manifest:
  - `ema_cross_default`: `fills=15`, `closed=7`, `pnl=-2.3016`
  - latest fill: `2026-08-24T00:01:55.857611+00:00`
  - status: `idle`, `waiting_for_next_day`, session evidence already recorded
    for `2026-08-28`
- 2026-08-31 out-of-sandbox read-only Hetzner status checkpoint:
  - `ema_cross_default`: `1/1 running`, `idle`, `waiting_for_next_day`,
    `fills=16`, `closed=8`, `pnl=-2.3183`
  - latest fill: `2026-08-29T00:02:44.159494+00:00`
  - session evidence already recorded for `2026-08-31`
  - recommendation: `continue_paper_observation`
  - checkpoint:
    `docs/checkpoints/paper_campaign_status_2026_08_31.md`
- Codex sandboxed Tailscale may report
  `tailscale_cli_preferences_unavailable` or `ssh_operation_not_permitted`; use
  a normal operator terminal or approved out-of-sandbox status check when
  Hetzner status must be verified.
- Canonical `es_daily_trend_v1` paper promotion remains blocked at `3/5`
  provenance-qualified round trips, with `2` remaining. 2026-07-21 local
  `make status-paper-gate-qualification` reports `qualified=3`,
  `all_history=10`, `counted=6`, `incomplete=1`, and `rejected=9`; local
  `make status-paper-soak` reports laptop campaigns `2/2 running`.
- `make status-paper-gate-qualification` now explains which fills count,
  remain incomplete, or are rejected by provenance checks.
- `make status-paper-soak` and `make status-paper-all` now surface compact
  paper-history qualification details directly in the daily status output.
- Raw all-history currently reports `9` closed trades, but those remain
  diagnostic unless both entry and exit fills carry the required non-sample
  public-OHLCV provenance.
- 2026-08-28 status refresh is recorded in
  `docs/checkpoints/hetzner_laptop_readonly_status_2026_08_28.md`. SHOWN:
  laptop campaigns recovered to `2/2 running`; Hetzner `ema_cross_default`
  remained `1/1 running`; Hetzner crypto-edge runtime was ready; dependency
  alignment remained open because the host checkout was still
  `6c0903d318756d27eb6414a01abbfc8c8e879ae5` while local `origin/master` was
  `5b39d051e8d0063a8fc731c68d384f63e1f5a9d3`, and the same 10 pinned-package
  mismatches remained. No host package install, deploy, or service restart was
  run.
- 2026-08-28 dependency-alignment proof is recorded in
  `docs/checkpoints/hetzner_dependency_alignment_proof_2026_08_28.md`. SHOWN:
  the operator-approved no-restart host venv alignment upgraded host `pip` to
  `26.2`, installed the 10 pinned-package updates, wrote a pre-change rollback
  freeze under `/tmp/cryptkeep_supply_chain/`, and produced post-change
  supply-chain JSON with `pin_integrity.ok=true`, `environment.ok=true`,
  `mismatches=[]`, and `not_installed=[]`. Post-change read-only checks showed
  Hetzner crypto-edge runtime ready and `ema_cross_default` still `1/1`
  running. Remaining host blocker: checkout sync from
  `6c0903d318756d27eb6414a01abbfc8c8e879ae5` to current master; host
  vulnerability audit and SBOM/hash-lock decisions remain separate.
- 2026-08-29 checkout-sync proof is recorded in
  `docs/checkpoints/hetzner_checkout_sync_2026_08_29.md`. SHOWN: Hetzner
  `/srv/cryptkeep/app` fast-forwarded without restart from
  `6c0903d318756d27eb6414a01abbfc8c8e879ae5` to current master
  `0018c1213214f74033a70c59949e9ed86e3cfbad`; post-sync dependency alignment
  was ready with no package mismatches and `pip_dry_run.status=no_changes`;
  crypto-edge runtime remained ready; Hetzner paper campaign remained `1/1`
  running; and host health reported `hetzner_paper_host_healthy`. Remaining
  host-side release-policy work: vulnerability audit approval/waiver and
  SBOM/hash-lock decision.
- 2026-09-01 read-only Hetzner status is recorded in
  `docs/checkpoints/hetzner_readonly_status_2026_09_01.md`. SHOWN:
  `check_supply_chain.py --audit --json` reported pin integrity OK and
  environment alignment OK on `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`, but
  `vulnerability_audit.ran=false` with `reason=pip_audit_unavailable`.
  Hetzner `ema_cross_default` remained `1/1` running and idle for the next UTC
  day, and host crypto-edge cadence under `CBP_STATE_DIR=/var/lib/cbp` remained
  fresh with `missing=[]` and `stale=[]`. No host sync, service restart, package
  install, config edit, campaign start/stop, gate change, live routing, or
  execution action was run. Remaining release-policy work: install/enable
  `pip-audit` on host or explicitly waive vulnerability audit, then decide
  SBOM/hash-lock requirements.
- 2026-07-06 strategy validation note: do not add another persistent campaign
  before proof. The next runnable non-persistent validation candidate is
  `pullback_recovery_default`, via isolated Stage 0 proof. `funding_extreme`
  remains the higher-value profitability candidate, but it is blocked on the
  crypto-edge/context strategy wiring path before it can produce governed
  paper evidence.

Current accepted checkpoint:

- docs/checkpoints/paper_gate_status_2026_06_24.md

## Canonical blocker list
Root-runtime launch blockers are tracked separately. They are not the same as
the current paper-evidence campaign blocker.

- docs/checkpoints/launch_blockers_root_runtime.md

Strategy-evaluation work is tracked separately:

- docs/checkpoints/strategy_signal_quality_plan_2026_05_22.md
- docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md
- docs/checkpoints/composite_hybrid_strategy_wrapper_design_2026_06_24.md
- docs/checkpoints/composite_hybrid_leaderboard_comparison_2026_06_27.md
- docs/checkpoints/composite_hybrid_long_window_variant_proof_2026_06_29.md
- docs/checkpoints/short_market_strategy_research_spec_2026_06_19.md
- docs/checkpoints/short_context_readiness_report_2026_06_29.md
- docs/checkpoints/candidate_layer_read_only_activation_objective_2026_06_22.md
- docs/checkpoints/pr43_ai_operator_oversight_rebuild_objective_2026_06_28.md
- docs/checkpoints/pr43_managed_multi_symbol_runtime_objective_2026_06_28.md
- docs/checkpoints/pr43_safe_pipeline_startup_hardening_objective_2026_06_28.md
- docs/checkpoints/hetzner_paper_campaign_ownership_proof_2026_06_30.md
- docs/checkpoints/hetzner_paper_runtime_ownership_proof_2026_06_30.md
- docs/checkpoints/hetzner_storage_preflight_proof_2026_07_01.md
- docs/checkpoints/hetzner_paper_host_health_alerting_proof_2026_07_01.md
- docs/checkpoints/hetzner_canonical_state_migration_template_2026_07_01.md

Top-level roadmap tracking checklist:

- docs/ROADMAP_TRACKING_CHECKLIST.md

## Active Backlog
These are the remaining tasks visible from the accepted checkpoint and planning
documents. Keep implementation scoped; high-risk runtime, launch, strategy, or
deployment work still needs independent review.

1. Continue canonical paper evidence collection until `es_daily_trend_v1`
   satisfies its active `slow_daily_single_symbol_v1` policy: 45 calendar days,
   60 qualified source bars, and 5 provenance-qualified round trips.
   2026-07-18 design review: configurable paper promotion gate policy RFC is
   drafted in
   `docs/decisions/paper_promotion_gate_policy_rfc_2026-07-18.md`. The RFC
   does not authorize implementation and does not change the current
   `es_daily_trend_v1` gate. It proposes strategy-class policies so slow daily
   systems can be evaluated by qualified live-data bars plus a smaller minimum
   number of full qualified cycles, while archive/walk-forward remains the
   statistical edge proof. Current rule remains: do not weaken provenance, do
   not count legacy fills, and continue using the existing gate until the RFC is
   reviewed, approved, implemented, and validated.
   2026-07-18 implementation proof is ready for independent review:
   configurable paper promotion policies now resolve from
   `promotion.paper.policy` with `legacy_round_trip_v1` as the default. The
   default legacy gate preserves the existing 30-day/10-round-trip behavior and
   exact `paper_progress` compatibility. Explicit strategy-class policies
   cannot lower thresholds below their class floors; `cohort_start` is enforced
   as read-time filtering so older evidence stays audit-visible but cannot
   count toward the new cohort; and qualified-bar counting records unique
   provenance-qualified source bars, not runner loop iterations. The first
   implemented classes are `slow_daily_single_symbol_v1`,
   `intraday_single_symbol_v1`, and `context_edge_v1`. No current strategy
   config is changed in this patch; adopting a non-legacy policy still requires
   a reviewed config change and fresh gate output.
   2026-07-22: executable paper-promotion gate policy RFC guard is ready for
   independent review. `tests/test_paper_promotion_gate_policy_rfc_guard.py`
   pins the RFC scope, policy classes/defaults, qualified-bar definition,
   cohort/migration boundaries, OHLCV reliability separation, and backlog link.
   This is docs/test only and does not change promotion policy loading, current
   ES config, gate thresholds, campaign evidence, OHLCV retry behavior, or
   execution behavior.
   SEPARATE WORK ITEM - OHLCV source outage blocked-state and retry-budget
   protection: campaign validation must not depend on repeatedly exhausting
   daily attempts when the configured upstream market-data source is
   unavailable. Add a reliability path that classifies configured public-OHLCV
   fetch failures as `blocked:ohlcv_source_unreachable`, preserves the error
   payload, avoids consuming daily strategy retry budget for known source
   outages, alerts only on state transitions, and automatically recovers when
   the same configured source preflight succeeds. This item is independent of
   promotion-gate policy; gate redesign must not mask infrastructure failures.
   2026-07-25: read-only paper-gate velocity report is ready for independent
   review. `scripts/report_paper_gate_velocity.py` / `make
   status-paper-gate-velocity` now estimates completion from completed
   provenance-qualified round-trip close timestamps, refuses projections with
   fewer than two closes, surfaces legacy/all-history exclusions as diagnostic
   only, and leaves gate policy/evidence unchanged.
   2026-08-14: current paper-gate velocity checkpoint is recorded in
   `docs/checkpoints/paper_gate_velocity_2026_08_14.md`. `make
   record-paper-gate-velocity` wrote
   `.cbp_state/data/paper_gate_velocity/paper_gate_velocity.20260814T051531Z.json`
   with `3/5` qualified round trips, `53/60` qualified bars, round trips as
   the active blocker, and projected completion on `2026-09-04T05:15:31Z`.
   This is evidence recording only and does not change policy, provenance, or
   campaign behavior.
   2026-07-18: guarded paper campaign restore is ready for independent review.
   `restore_paper_campaigns.py --restore --preflight-ohlcv` uses the existing
   public-OHLCV preflight before starting a dead collector, reports
   `preflight_blocked` on unreachable campaign data, and does not launch the
   collector in that state. The default guard probes 400 rows to match managed
   `strategy_runner` fallback lookback; plain `--restore` behavior is
   preserved.
   2026-07-18 implementation proof is ready for independent review for the
   public-OHLCV outage reliability slice. The daily paper evidence collector
   now runs the existing read-only OHLCV preflight before consuming a daily
   campaign attempt for `public_ohlcv_*` sources. If the configured source is
   unreachable, it writes `status=blocked`,
   `reason=ohlcv_source_unreachable`, preserves the full preflight payload,
   and marks `retry_budget_consumed=false` without starting the campaign or
   logging a failed session attempt. A later successful preflight allows the
   loop to proceed normally. Campaign alerts now include transition-deduped
   warning-level `blocked` notifications.
   2026-07-18 follow-up implementation proof is ready for independent review:
   `restore_paper_campaigns.py --restore --preflight-ohlcv --restart-unhealthy`
   can replace alive unhealthy paper collectors only after their configured
   OHLCV source preflight passes. Plain `--restore` still leaves live
   collectors unchanged, `--restart-unhealthy` is refused unless preflight is
   enabled, and preflight failure blocks before any stop/start action. Added
   `make recover-paper-campaigns` as the guarded operator shortcut for
   pre-merge or manually started parents parked after `no_public_ohlcv`.
   2026-07-18 follow-up: live laptop recovery showed preflight could pass and
   replacement collectors could still park immediately at
   `daily_retry_limit_exhausted` because the retry count is derived from
   persisted same-day session evidence. Recovery now preserves that evidence
   but, after a successful OHLCV preflight for a same-day OHLCV/daily-limit
   failure, launches with a one-attempt override
   (`launch_max_daily_attempts = previous_daily_attempts + 1`) and reports the
   override in `recovery_attempt_override`.
2. After the paper gate reaches 10 qualified round trips, write the manual
   strategy performance decision against the accepted baseline. Before relying
   on the expectancy/manual-review gate, populate or explicitly waive the
   currently null `backtest_expectations` fields in
   `configs/strategies/es_daily_trend_v1.yaml` from an accepted parity/backtest
   baseline; otherwise the gate can report count readiness while the strategy
   performance comparison remains unresolved.
   If archive-first backtesting lands before the manual review, prefer an
   archive-backed multi-year baseline with dataset hashes over any shallow
   single-fetch baseline. Do not populate the expectancy fields from a
   short-window or non-reproducible run unless that limitation is explicitly
   accepted in the decision record.
   Ground truth must come from the operator-host gate/status command output
   (`make status-paper-gate-qualification` or the equivalent gate JSON), not
   from stale counts copied into this backlog.
   2026-07-12 authority-boundary audit follow-up: before any real promotion,
   choose the promotion-authority model for script/Makefile stage transitions
   (gate-enforced, human-only, or artifact-backed) because the documented
   `make promote-strategy` path reaches `deployment_stage.promote()` without
   consuming the gate verdict. Also choose the canonical expectancy model for
   fallback/no-history and retirement consumers; the primary paper-history path
   is per-closed-trade, but the JSONL fallback and retirement checks still use
   different denominator semantics. This is decision work, not part of the
   strategy-selection runtime fix.
   2026-07-12 follow-up implementation proof is ready for independent review:
   the documented operator promotion entrypoint now fails closed unless
   `check_promotion_gates.run_check()` reports ready for the strategy's current
   stage, and the paper-promotion JSONL fallback no longer computes an
   authoritative per-fill expectancy. Decision records:
   `docs/decisions/promotion_stage_authority_decision.md` and
   `docs/decisions/canonical_expectancy_decision.md`. Remaining before real
   promotion: GitHub CI/review, plus operator-host gate output as ground truth.
   2026-07-22 follow-up implementation proof is ready for independent review:
   paper gate metric output now labels authoritative expectancy as
   `expectancy_unit=closed_trade` / `expectancy_denominator=closed_trades` and
   marks JSONL fallback metrics as non-authoritative for paper promotion.
   New measurement-contract tests prove the paper path uses
   provenance-qualified paper history, keeps JSONL per-fill PnL out of
   paper-promotion expectancy, and computes qualified expectancy net of fees
   per closed trade.
   2026-07-22: executable canonical-expectancy decision guard is ready for
   independent review. `tests/test_canonical_expectancy_decision_guard.py`
   pins the authoritative paper-history source, JSONL fallback boundary,
   legacy helper boundary, authority rationale, and backlog link. This is
   docs/test only and does not change promotion gates, metric calculations,
   paper history, or fallback behavior.
   2026-07-22: executable promotion-stage authority decision guard is ready
   for independent review.
   `tests/test_promotion_stage_authority_decision_guard.py` pins the
   gate-enforced operator entrypoint, implemented boundary, strategy scope
   boundary, authority rationale, and backlog link. This is docs/test only
   and does not change promotion gates, stage mutation logic, strategy support,
   deployment, or execution behavior.
3. Build the shadow would-be-fill recorder before treating shadow slippage
   gates as actionable. The shadow gate asks for fill/slippage evidence, but
   observe-only shadow submit currently blocks real submissions and does not
   create would-be-fill records. Add a paper/shadow-safe recorder that captures
   intended side, quantity, reference price, contemporaneous bid/ask or depth,
   estimated fill price, slippage, strategy id, stage, and provenance. Proof
   must show shadow mode still creates zero live orders while
   `scripts/check_promotion_gates.py --stage shadow --json` can see the
   slippage evidence needed for manual review. Implementation proof is ready
   for independent review: observe-only submit records one idempotent
   `shadow_would_be_fill` fill-evidence record per pending live intent, does
   not instantiate the exchange client, leaves the intent pending, and writes
   zero execution-store fills. 2026-07-15 backlog hygiene: the recorder is
   present on `master` in `services/execution/_executor_submit.py`, with
   promotion-gate and executor regressions covering visibility and zero live
   side effects. Remaining work is operational shadow-stage evidence: run a
   shadow session that produces real `shadow_would_be_fill` records, then use
   the gate/report artifacts for manual slippage and cost review.
4. Prove private lifecycle runtime flow in one reachable supported
   sandbox/testnet venue, or record an explicit human exception decision. This
   proof can run before the paper gate clears because it is a no-capital
   execution-stack learning exercise, not a promotion decision. Keep it
   isolated from paper evidence, require sandbox/testnet credentials only, and
   record place/fill/cancel/reconcile evidence without changing strategy stage.
5. Produce the launch evidence packet: restart/recovery, kill-switch,
   reconciliation halt/resume, rollback, and lifecycle or exception evidence.
6. Continue only the remaining PR #43 rebuild candidates from clean `master`.
   AI operator oversight is independently accepted as a read-only one-shot
   synthesis report over existing monitor/watch/gate artifacts; do not rebuild
   a second background monitor. Managed multi-symbol paper runtime now has a
   read-only proposal planner implementation proof ready for independent
   review; do not implement autonomous campaign starts or mutate manifests.
   Safe pipeline wrapper/startup hardening is accepted as a read-only startup
   topology/gap audit; do not implement a new wrapper unless a current-master
   gap is reproduced and separately reviewed. Supervised-soak reporting and
   durable pipeline log evidence are already rebuilt/closed.
7. Run the full post-fix isolated Stage 0 proof for
   `pullback_recovery_default` before enabling any persistent campaign. The
   read-only readiness report is accepted and merged; run
   `make pullback-stage0-baseline` immediately before the long proof and
   `make pullback-stage0-verify` afterward. After proof, decide whether to add
   `pullback_recovery_default` to the leaderboard/default candidate set and
   create a governed strategy config before treating it as more than an
   isolated candidate. 2026-07-06 check-in confirmed this remains the next
   runnable strategy-validation action; keep it isolated until Stage 0 proof
   passes, and do not start it as a persistent campaign first.
   2026-07-11: post-fix isolated Stage 0 proof passed. Baseline was recorded
   at commit `2953af16a`; the 15-minute proof completed after baseline with
   zero blocking verifier checks, matched expected commit `2953af16a`, carried
   public OHLCV provenance (`coinbase`, `BTC/USDT`, `5m`), preserved
   `pullback_recovery_default` strategy attribution, reconciled successfully,
   and left canonical paper fill count unchanged (`176` before and after).
   The strategy held during the window (`pullback_out_of_range`,
   `no_rebound_confirmation`) with no new fills. Remaining action: decide
   whether to keep this as an isolated candidate, add it to the leaderboard /
   default candidate set, or create a governed persistent campaign config.
   2026-07-11 decision recorded in
   `docs/strategies/pullback_recovery_stage0_decision_2026-07-11.md`:
   keep `pullback_recovery_default` as an isolated research candidate. It is
   already present in the research leaderboard and already has a
   governance-only config, but it remains `campaign_enabled=false`,
   `promotion_candidate=false`, and `trade_enabled=false`. Do not start a
   persistent paper campaign until archive-backed baseline expectations,
   positive net-fee research evidence, no-trade filter review, and a separately
   reviewed campaign manifest exist.
   2026-07-22: executable pullback Stage 0 decision guard is ready for
   independent review. `tests/test_pullback_stage0_decision_guard.py` pins
   the isolated research candidate decision, Stage 0 evidence boundary,
   required-before-promotion list, allowed/not-allowed uses, and disabled
   governance config. This is docs/test only and does not change strategy
   config values, campaign manifests, paper gates, promotion status, or
   execution behavior.
8. Keep composite/hybrid paper advancement blocked. The long-window variant
   proof is accepted and now shows three realized synthetic windows, but the
   candidate still has synthetic-only, low-confidence evidence and no persisted
   paper-history support.
9. Continue short/context follow-through from the accepted readiness report.
   The repo-side mixed-venue collector conflict is fixed by allowing the
   read-only research collector to open non-Binance public clients while
   `CBP_VENUE=binance` and `CBP_ALLOW_BINANCE=1` authorize Binance. Resolve the
   remaining Binance derivatives public-data `ExchangeNotAvailable` failure or
   choose a compliant read-only derivatives venue before relying on derivatives
   row families. A bounded read-only OKX probe on 2026-07-02 collected funding,
   open-interest, and basis rows. 2026-07-05: OKX is documented as the default
   read-only derivatives context source for the crypto-edge collector plan in
   `docs/research/crypto_edge_source_decision.md`; this does not approve OKX
   for live routing or strategy promotion evidence. Remaining short/context
   proof is now data-readiness, not venue selection: keep replay fixture-only
   unless `make check-short-context-readiness` reports
   `live_public_replay_ready=true`. 2026-07-14: crypto-edge store numeric
   ingestion proof is ready for independent review. `funding_rate`,
   `interval_hours`, basis `spot_px`/`perp_px`/`days_to_expiry`, and optional
   quote `bid`/`ask` are now validated before snapshot rows are persisted;
   invalid rows roll back the whole snapshot instead of leaving partial
   funding/basis/quote evidence. OI and order-book validation already existed
   and was left unchanged.
10. Make the strategy registry fail closed before new discovery wiring lands.
   Earlier audit found `strategy_registry.compute_signal()` fell back to
   `ema_cross` when `strategy.name` was unknown. That was a latent
   evidence-poisoning risk once new names like `funding_extreme` entered
   campaign configs. Unknown strategies needed to produce a non-actionable
   error/hold result visible in session evidence, proving a typo could not emit
   an actionable signal.
   Implementation is independently accepted: the registry returns `ok=false`,
   `action=hold`, and `reason=unknown_strategy` for explicit unknown names
   while preserving the existing missing-name `ema_cross` default.
   Runner/evidence integration proof is independently accepted: explicit
   unknown names remain unsupported through runner config resolution, the
   public-OHLCV runner loop records `signal_ok=false` and
   `signal_reason=unknown_strategy`, and no intents, paper orders, or paper
   fills are created.
11. Build archive-first backtesting before relying on strategy comparisons.
   `services/backtest/signal_replay.py` currently fetches OHLCV live with a
   shallow single-call default, while `storage/market_store_sqlite.py` already
   has a `market_ohlcv` archive table. Promote paginated OHLCV ingestion into a
   reusable archive path, make backtests read archive-first with dataset hashes,
   and prove repeated runs over the same archive are byte-identical. After the
   archive proof lands, add a systematic parameter-sweep and walk-forward
   research runner over registered strategy families so discovery throughput is
   measured by reproducible out-of-sample hypotheses, not hand-picked one-off
   windows.
   2026-07-11: first archive-first slice is accepted.
   `MarketStore.load_ohlcv()` reads archived OHLCV from `market_ohlcv`;
   `services.backtest.ohlcv_archive` normalizes/deduplicates archived rows and
   emits a deterministic dataset hash; `signal_replay.fetch_ohlcv()` now uses a
   complete archive window before falling back to the existing exchange fetch.
   Incomplete/missing archives do not shrink a backtest window silently; they
   retain the old ccxt fallback behavior. 2026-07-11: second archive-first
   slice is accepted. Strategy evidence windows now carry
   `dataset_hash` and a `dataset` metadata block with source, venue,
   timeframe, symbol, bars, and start/end timestamps; the persisted evidence
   report includes a `dataset_summary` across all scored windows. Current
   synthetic windows are labeled `synthetic_evidence_window` rather than
   archive data, and any future archive/provided window can carry its own
   source/path metadata. 2026-07-11: third archive-first slice is accepted.
   `signal_replay.fetch_ohlcv_with_meta()` surfaces rows
   plus source/dataset-hash metadata while preserving `fetch_ohlcv()` as a
   bare-rows compatibility wrapper; `ohlcv_archive.paginate_ohlcv()` and
   `backfill_archive()` provide reusable, fetcher-injectable pagination and
   idempotent archive upsert; the ES daily-trend baseline report now persists
   a `dataset` block with the exact-row SHA-256. 2026-07-11: fourth
   archive-first slice is accepted.
   `walk_forward.run_archive_backed_walk_forward()` runs one explicit strategy
   config over a complete archive window, stamps the top-level artifact and
   every walk-forward window with the archive dataset hash, and refuses
   incomplete archives rather than falling back to live OHLCV.
   `scripts/research/run_archive_walk_forward.py` writes the same research-only
   JSON artifact from a JSON/YAML config. 2026-07-11: fifth archive-first
   slice is accepted. `services.backtest.parameter_sweep`
   expands bounded dot-path parameter grids, runs each variant through the
   archive-backed walk-forward wrapper, and emits deterministic research-only
   ranks with explicit ranking policy, dataset summary, config hashes, and
   top-variant metadata. `scripts/research/run_archive_parameter_sweep.py`
   writes the ranked JSON artifact from a base config plus grid file. Remaining
   item #11 work after acceptance is operational, not code plumbing: run real
   multi-year archive sweeps and require separate review before any strategy
   config or campaign changes use the results. 2026-07-14: market OHLCV archive
   2026-07-22: archive parameter-sweep triage is ready for independent review.
   `services.analytics.archive_parameter_sweep_triage` and
   `scripts/research/run_archive_parameter_sweep_triage.py` consume an existing
   `archive_backed_parameter_sweep_v1` artifact and rank variants for manual
   review using explicit window/trade/non-negative-window/return/drawdown
   thresholds. It does not rerun backtests, change strategy config, start
   campaigns, or produce campaign/promotion/profitability evidence; it consumes
   the source sweep metrics as-is and does not verify the sweep's cost
   assumptions. Remaining item #11 work is still operational: run real
   multi-year archive sweeps and require separate review before any strategy
   config or campaign changes use the results. 2026-07-14: market OHLCV archive
   numeric-ingestion proof is ready for independent review. `MarketStore` now
   rejects non-positive or non-finite OHLCV timestamps/prices, invalid high/low
   envelopes, and non-finite/negative volume before writing `market_ohlcv`,
   while preserving missing-volume rows. This protects dataset hashes and
   archive-backed walk-forward inputs from malformed bars. 2026-07-22:
   executable walk-forward research doc guard is ready for independent review.
   `docs/research/walk_forward_validation.md` now reflects the accepted
   archive-backed walk-forward and bounded parameter-sweep tooling while
   preserving research-only, fail-closed archive, hash-stamped artifact,
   non-authority, and review-before-use boundaries.
   `tests/test_walk_forward_research_doc_guard.py` pins those boundaries. This
   is docs/test only and does not change backtest math, sweep ranking,
   promotion gates, strategy configs, campaigns, or execution behavior.
   2026-07-22: executable strategy-feedback ledger doc guard is ready for
   review. `docs/research/strategy_feedback_ledger.md` now names the ledger as
   descriptive persisted-paper-fill metadata that may only adjust research
   leaderboard scores; it is not promotion, strategy-config, position-sizing,
   campaign, live-routing, or execution authority. Any use beyond research
   ranking requires a separate reviewed config, campaign, gate, or execution
   change with its own proof.
   `tests/test_strategy_feedback_ledger_doc_guard.py` pins those boundaries
   and the strategy-expansion roadmap link. This is docs/test only and does not
   change feedback math, leaderboard ranking, strategy configs, campaigns,
   promotion gates, or execution behavior.
   2026-07-22: executable strategy-expansion roadmap guard is ready for
   review. `docs/research/strategy_expansion_roadmap.md` now reflects the
   accepted archive-backed walk-forward, bounded parameter-sweep, and
   strategy-feedback ledger tooling while preserving the roadmap as sequencing
   guidance only. `tests/test_strategy_expansion_roadmap_guard.py` pins the
   conservative build order, research-only status, non-authority boundaries,
   and no-implementation-approval rule. This is docs/test only and does not
   change research tooling, leaderboard logic, strategy configs, campaigns,
   promotion gates, or execution behavior.
   2026-07-14:
   market ticker ingestion proof is ready for independent review.
   `MarketStore.upsert_ticker()` now rejects non-positive or non-finite
   present prices, crossed bid/ask pairs, non-finite or negative present
   volumes, and invalid timestamps before writing `market_tickers`, while
   preserving partial tickers with missing nullable quote fields. This protects
   unified market views from malformed ticker rows without changing archive or
   campaign behavior.
12. Wire crypto-edge context strategies into the research/paper execution path.
    `funding_extreme`, `open_interest_shift`, and `order_book_imbalance` exist
    as context-signal modules, and `funding_extreme_default` /
    `open_interest_shift_default` exist in presets/config tooling, but
    `strategy_registry.py` only executes OHLCV strategies today. Add the
    smallest read-only/paper context contract needed to pass crypto-edge rows
    into strategies, then prove one context strategy can emit
    provenance-qualified paper evidence without enabling live execution. Wire
    `funding_extreme` first because OKX funding is the smallest proven input and
    its cadence fits REST snapshots. Defer `open_interest_shift` until previous
    OI state is derived from snapshot history. Defer `order_book_imbalance`
    until a tighter-cadence or streaming depth path exists; depth REST snapshots
    are not sufficient proof-quality evidence for that signal. Treat
    `funding_extreme` as the flagship profitability hypothesis once wired;
    keep `es_daily_trend_v1` framed as the pipeline-validation strategy unless
    later evidence proves it is also the best profit candidate. Include a
    shared `regime_context` provider in this context contract. The flagship
    `sma_200_trend` path already computes and enforces
    `es_daily_trend.regime_stability()`; extract that market-state awareness so
    other strategies can consume the same regime facts without duplicating
    logic, while proving current `sma_200_trend` behavior remains unchanged.
    Treat `composite_hybrid` confirmation mode as a context/confirmation
    consumer, not as a standalone live strategy, until archive-backed
    walk-forward evidence and paper provenance justify runtime registration.
    2026-07-06 check-in confirmed `funding_extreme` should not be treated as
    the next immediate campaign start; it is the next higher-value strategy
    validation target after the context/crypto-edge contract can feed governed
    paper evidence. 2026-07-11: first context-strategy slice was independently
    reviewed and accepted. `strategy_registry.compute_signal()` now accepts an
    optional explicit `context` payload, registers `funding_extreme`, fails
    closed with `missing_funding_context` when no funding context is supplied,
    and can route direct percent or nested decimal funding rows into
    `funding_extreme.signal_from_context()`. `funding_extreme` is explicitly
    excluded from candidate-advisor recommendations until governed context paper
    provenance exists. 2026-07-11: second slice was independently reviewed and
    accepted by the operator.
    A read-only funding context provider now selects fresh `live_public`
    funding rows from the crypto-edge store, converts stored decimal rates into
    `funding_rate_pct`, and fails closed on missing/stale/malformed context.
    `strategy_runner` recognizes `funding_extreme`, passes fresh context into
    the registry only for that strategy, and surfaces context diagnostics in
    status/intent metadata. 2026-07-11: third slice was independently reviewed
    and accepted by the operator. The paper runner now accepts optional `strategy_context_symbol` and
    `strategy_context_venue` overrides, passes them through the managed
    campaign CLI as `--strategy-context-symbol/--strategy-context-venue`, and
    records the resolved context symbol/venue in status/intent metadata. This
    preserves existing defaults while allowing spot OHLCV/ticks to be paired
    with OKX perp funding context for `funding_extreme`. SHOWN: in-process
    proof consumed fresh `live_public` OKX `BTC/USDT:USDT` funding context
    and Coinbase public OHLCV, returning `action=hold`, `reason=funding_neutral`,
    `strategy_context_ok=true`. FILED, NOT FIXED: the managed subprocess
    Stage 0 campaign still fails with `no_public_ohlcv` because child
    `strategy_runner` / tick-publisher processes report public exchange
    metadata `NetworkError` even when direct in-process fetches succeed.
    2026-07-11: component-env leakage slice was independently reviewed and
    accepted by the operator.
    Managed paper child processes no longer receive global `CBP_VENUE` /
    `CBP_SYMBOLS`; the service now passes `CBP_COMPONENT_VENUE` /
    `CBP_COMPONENT_SYMBOLS`, and the strategy runner / tick publisher prefer
    those values while preserving legacy direct-script fallback. SHOWN: unit
    tests prove parent global env cannot leak into managed children, and a
    child-process probe using the service env returned Coinbase public OHLCV
    rows with `CBP_VENUE`/`CBP_SYMBOLS` absent. FILED, NOT FIXED: local
    managed Stage 0 still fails with `no_public_ohlcv` because this host shows
    intermittent Coinbase DNS/metadata failures in isolated subprocess probes;
    do not treat that as an accepted end-to-end paper proof. Remaining item
    #12 work: prove a governed `funding_extreme` paper evidence session
    end-to-end on a stable network/host without enabling live execution.
    2026-07-11: public-OHLCV reachability preflight tooling is ready for
    independent review. `scripts/check_ohlcv_preflight.py` mirrors the runner
    fetch path (`make_exchange` -> `map_symbol` -> `fetch_ohlcv`) and exits
    `0` for reachable/non-empty public OHLCV, `1` for config/empty-source
    problems, and `2` for network/source unreachable. This does not fix host
    DNS, but it makes the Stage 0 precondition explicit so `no_public_ohlcv`
    cannot be mistaken for a strategy result when the source is unreachable.
    2026-07-11: `funding_extreme` Stage 0 readiness/proof helper tooling is
    ready for independent review. `make funding-stage0-readiness` verifies the
    three known preconditions before the governed 15-minute proof:
    Coinbase public-OHLCV reachability for `BTC/USDT` on `public_ohlcv_5m`,
    crypto-edge cadence, and fresh OKX `BTC/USDT:USDT` `live_public` funding
    context. `make funding-stage0-baseline` records pre-proof canonical and
    challenger state, and `make funding-stage0-verify` checks that a completed
    post-baseline session consumed public OHLCV plus funding context while
    leaving canonical fill counts unchanged. This is tooling only; it does not
    complete item #12 until the operator-run Stage 0 campaign passes.
    2026-07-11 follow-up: default Coinbase OHLCV readiness blocked on
    `NetworkError: coinbase GET https://api.coinbase.com/v2/currencies`, while
    `scripts/check_ohlcv_preflight.py --venue okx --symbol BTC/USDT
    --signal-source public_ohlcv_5m --json` passed with 5 rows. A configurable
    OHLCV proof-source slice is ready for independent review so operators can
    run `make funding-stage0-readiness FUNDING_STAGE0_ARGS="--venue okx"` and
    have baseline/verify check the same venue contract. The readiness helper
    uses bounded public-OHLCV retry attempts, and the OKX readiness command
    passed outside the sandbox with zero blockers.
    2026-07-11/12: governed isolated `funding_extreme_default` Stage 0 proof
    passed after seeding the challenger crypto-edge store from canonical
    crypto-edge evidence and using the OKX OHLCV contract. SHOWN:
    `make funding-stage0-verify FUNDING_STAGE0_ARGS="--venue okx"` returned
    `status=passed`, `blocking_checks=0`, `expected_commit=f652f8321`,
    completed session `2026-07-12T02:53:13.816650+00:00`,
    reconciliation `pass`, `market_data_source=public_ohlcv`,
    `ohlcv_sample_mode=false`, OHLCV `okx BTC/USDT 5m`,
    `strategy_context_ok=true`, `strategy_context_reason=funding_context_ready`,
    context `live_public okx BTC/USDT:USDT`, signal `hold/funding_neutral`,
    canonical fill count unchanged at `176`, challenger fill count `0`.
    Decision recorded in
    `docs/strategies/funding_extreme_stage0_decision_2026-07-11.md`: Stage 0
    wiring proof accepted, but no persistent campaign or promotion treatment
    until archive-backed research and the high-risk crypto-edge qualification
    extension are separately reviewed.
    2026-08-30: a second isolated `funding_extreme_default` Stage 0 wiring
    proof was recorded after current readiness passed. The one-shot proof used
    Coinbase public OHLCV (`BTC/USDT`, `public_ohlcv_5m`) with OKX live-public
    funding context (`BTC/USDT:USDT`) and completed at commit `4e21a4c69`.
    SHOWN: terminal collector result `status=completed`, `reason=completed`,
    `signal_action=hold`, `enqueued_total=0`, `fills_delta=0`,
    `closed_trades_delta=0`, and `net_realized_pnl_delta=0.0`. The default
    verifier first failed because its saved baseline expected stale commit
    `fd7f11e9c` and OHLCV venue `okx`; rerunning the verifier read-only with
    the actual accepted contract returned `status=passed` and
    `blocking_checks=0`. Checkpoint:
    `docs/checkpoints/funding_extreme_stage0_proof_2026_08_30.md`. This
    confirms wiring and live-public context consumption only; it does not show
    profitability, actionable fill behavior, promotion qualification, or
    persistent-campaign suitability.
    2026-07-21 follow-up proof-workflow fix: the readiness helper and paper
    evidence collector now carry an explicit
    `CBP_CRYPTO_EDGE_DB_PATH` / `--strategy-context-db-path` override. This
    keeps the proof run's `CBP_STATE_DIR` isolated while letting
    `funding_extreme` read the same crypto-edge store that readiness validated,
    replacing the prior manual copy/seeding workaround. No live routing,
    persistent campaign, strategy promotion, or canonical paper-campaign
    behavior is authorized by this wiring.
    2026-07-22: executable funding Stage 0 decision guard is ready for
    independent review. `tests/test_funding_stage0_decision_guard.py` pins
    the non-promotion status, proof contract, confirmed/unconfirmed boundaries,
    next conditions, backlog link, and required Stage 0 tooling presence. This
    is docs/test only and does not change context plumbing, research reports,
    promotion qualification, campaign manifests, paper gates, or execution
    behavior.
    2026-07-18: research-only funding context replay is ready for independent
    review. `services.analytics.funding_context_replay` and
    `scripts/research/run_funding_context_replay.py` replay stored
    `funding_extreme` signals from crypto-edge funding snapshots, stamp a
    deterministic dataset hash, and report action/reason counts. This is
    signal-distribution evidence only: no price-path join, no PnL, no
    expectancy, no campaign start, and no promotion evidence. Remaining
    `funding_extreme` research blocker: build or run a separately reviewed
    price-joined context walk-forward before any persistent campaign decision.
    2026-07-18 host proof recorded in
    `docs/checkpoints/funding_context_replay_host_proof_2026_07_18.md`:
    Hetzner replay over stored OKX `live_public` funding snapshots returned
    `ok=true`, `row_count=16`, dataset hash
    `84eda056e7db868e01b44fcc7bc05322cfa37675ae14d1035212f588b6f54b9c`,
    `action_counts={"hold": 16}`, and `reason_counts={"funding_neutral": 16}`.
    This confirms deterministic signal replay over host data, not profitability.
    2026-07-18: research-only funding/price join is ready for independent
    review. `services.analytics.funding_context_price_join` and
    `scripts/research/run_funding_context_price_join.py` join stored funding
    snapshots to archived OHLCV rows and compute unit-size modeled forward
    returns after configured fee/slippage. This remains research-only:
    forward-return rows are not portfolio PnL, not expectancy, not campaign
    state, and not promotion evidence. Before a persistent `funding_extreme`
    campaign decision, run this against sufficient host funding history plus a
    complete accepted OHLCV archive and review the resulting artifact.
    2026-07-20/21: host check after PR #351 confirmed the next blocker:
    Hetzner has stored funding data (`funding_row_count=50` in the
    price-join path) but no `/var/lib/cbp/data/market_raw.sqlite`, so the
    report returns `ok=false`, `reason=archive_missing`. A research-data
    ingestion CLI is ready for independent review:
    `scripts/research/run_ohlcv_archive_backfill.py` / `make
    ohlcv-archive-backfill` wraps the accepted `backfill_archive()` primitive,
    fetches public OHLCV directly from the exchange factory so it cannot read
    from the archive it is populating, and writes only the market archive plus
    a dataset-hashed JSON summary. It does not change campaigns, gates, live
    execution, routing, or strategy evidence.
    2026-07-21: host proof recorded in
    `docs/checkpoints/funding_price_join_host_proof_2026_07_21.md`.
    Hetzner was synced to `5eb36cbb5` with no service restart. OKX `BTC/USDT`
    5m archive backfill wrote `1021` rows to
    `/var/lib/cbp/data/market_raw.sqlite` with dataset hash
    `d2a661e606423760075844b4e1df88bd0dca3161d89292e1187f3e13207e243b`.
    The funding/price join then returned `ok=true`, `joined_rows=498`,
    `dataset_hash=f01778c070ab4feaf6aa7f5271e5fd2ed95544a774e6ae0fa9f972e83986b51b`,
    `action_counts={"hold":498}`, and
    `reason_counts={"funding_neutral":498}`. Interpretation: the archive
    blocker is closed for this bounded host window, but the stored funding
    sample produced zero actionable `funding_extreme` rows under current
    thresholds; this is not profitability evidence.
    2026-07-21: research-only funding-threshold sensitivity tooling is ready
    for independent review. `services.analytics.funding_threshold_sensitivity`
    and `scripts/research/run_funding_threshold_sensitivity.py` consume an
    existing `funding_context_price_join_v1` artifact and recompute
    hypothetical action counts plus unit-size modeled forward returns for
    explicit `long_threshold_pct` / `short_threshold_pct` grids. This is a
    report consumer only: it does not fetch data, change strategy config,
    start campaigns, compute portfolio PnL, or produce promotion evidence.
    2026-07-22: research-only funding-threshold window stability is ready for
    independent review. `services.analytics.funding_threshold_window_stability`
    and `scripts/research/run_funding_threshold_window_stability.py` consume
    an existing `funding_context_price_join_v1` artifact, split its rows into
    fixed complete windows, and summarize threshold-pair behavior across
    windows using the source artifact's cost assumptions. It fails closed if
    the source artifact lacks fee/slippage assumptions and remains
    research-only: no data fetch, strategy config change, campaign, gate,
    portfolio PnL, or promotion evidence.
    2026-07-22: research-only funding-threshold candidate triage is ready for
    independent review. `services.analytics.funding_threshold_candidate_triage`
    and `scripts/research/run_funding_threshold_candidate_triage.py` consume
    an existing `funding_threshold_sensitivity_v1` artifact and rank threshold
    pairs for manual review using explicit minimum input rows, actionable rows,
    actionable share, positive ratio, and average net forward-return
    thresholds. This is still triage only: it does not fetch data, change
    strategy config, start campaigns, compute portfolio PnL, or produce
    campaign/promotion/profitability evidence.
    2026-07-22: research-only funding-threshold stability triage is ready for
    independent review. `services.analytics.funding_threshold_stability_triage`
    and `scripts/research/run_funding_threshold_stability_triage.py` consume
    an existing `funding_threshold_window_stability_v1` artifact and rank
    threshold pairs for manual review using window count, actionable-window
    ratio, positive-window ratio, average modeled forward return, and worst
    window average return thresholds. This remains a report consumer only and
    is not strategy config, campaign evidence, promotion evidence, profitability
    evidence, or an activation decision.
    2026-07-25: read-only funding-threshold research pipeline wrapper is ready
    for independent review.
    `scripts/research/run_funding_threshold_research_pipeline.py` runs the
    accepted funding/price join, threshold sensitivity, direct candidate
    triage, window-stability, and stability-triage reports in sequence, writes
    each report plus a summary manifest, and stops fail-closed when any step
    cannot produce an `ok=true` artifact. `make
    funding-threshold-research-pipeline` and `scripts/SCRIPTS.md` expose the
    wrapper. This is research orchestration only; it does not change
    collectors, thresholds, scoring logic, strategy config, campaigns, gates,
    data ingestion, live routing, execution, or promotion evidence.
    2026-07-28: funding-threshold research pipeline negative-threshold argv
    handling is ready for independent review. The wrapper now passes long/short
    threshold CSVs using `--flag=value` form, so default negative short
    thresholds are not misparsed by downstream `argparse` as option flags.
    SHOWN locally after research archive backfill: `make
    funding-threshold-research-pipeline` returns `ok=true`, writes five
    expected research-only step artifacts, and `make research-pipeline-status-json`
    reports both wired research pipelines as `latest_ok` with no action
    required. This remains research orchestration only; it does not change
    collectors, thresholds, scoring logic, strategy config, campaigns, gates,
    data ingestion policy, live routing, execution, or promotion evidence.
    2026-08-25: local research refresh recorded in
    `docs/checkpoints/research_pipeline_refresh_2026_08_25.md`. `make
    funding-threshold-research-pipeline` returned `ok=true` and wrote five
    research-only artifacts under
    `.cbp_state/data/research/funding_threshold_pipeline/20260825T050434Z`.
    The joined sample had `414` rows and funding-rate percentages from
    `0.00303595` to `0.01`; both direct candidate triage and stability triage
    produced `0` review candidates across `16` threshold pairs. Interpretation:
    current default funding thresholds still do not produce an actionable
    `funding_extreme` candidate on this local artifact window; this is not a
    campaign, promotion, or profitability decision.
    2026-07-22: research-only crypto-edge strategy readiness matrix is ready
    for independent review. `services.analytics.crypto_edge_strategy_readiness`
    and `scripts/research/run_crypto_edge_strategy_readiness.py` classify the
    current context-strategy wiring without fetching data, starting campaigns,
    or changing gates. SHOWN by the report: `funding_extreme` is
    `stage0_wired_research_only`; `open_interest_shift` is
    `config_only_research_placeholder` with `trade_enabled=false`; and
    `order_book_imbalance` is `signal_module_unregistered`. This is source-tree
    readiness evidence only, not campaign, promotion, or profitability
    evidence.
13. Treat any paper-qualification extension for crypto-edge provenance as
    high-risk gate work. The proof must show an edge-compliant fill is accepted
    and a deliberately stale/mismatched edge fixture is rejected, while existing
    OHLCV qualification fixtures remain unchanged. Also prove the session stays
    paper-only: deployment stage is paper, live intent/order tables are
    unchanged before/after, and the diff does not touch live execution or risk
    gates.
    2026-07-12: crypto-edge paper qualification extension is ready for
    independent review. The shared paper-history qualification service now
    requires `strategy_context_*` provenance only for context strategies
    (`funding_extreme`, `open_interest_shift`, `order_book_imbalance`) or
    configs that explicitly declare `strategy_context_*`. Fresh matching
    `funding_extreme` context counts toward qualified paper round trips;
    stale or mismatched context is rejected with stable reasons while existing
    OHLCV-only gate fixtures remain unchanged. Diff boundary is limited to
    paper qualification tests/docs; no live execution or risk-gate files are
    touched.
    2026-07-18: independently reviewed and accepted by the operator with the
    high-risk boundary preserved. Recheck proof: the fresh matching
    `funding_extreme` context round trip counts, and stale/mismatched context
    rejects (`2 passed`). Acceptance state: `ACCEPTED_WITH_RISK`.
14. Start scheduled read-only crypto-edge collection from the accepted OKX
    source decision. Funding and open-interest history mostly accrue in real
    time, and Binance derivatives remain unavailable from the current network.
    Treat this as a one-venue research focus until one venue/strategy pair
    proves expectancy; multi-exchange remains a scaling objective, not the
    near-term discovery path. Collect a broader plausible symbol universe than
    the active campaign needs and, if read-only support is available, at least
    one second venue for comparison.
    Add a cadence-gap alert for the edge collector specifically; a silent
    collector outage burns unrecoverable funding/OI history even when paper
    campaigns keep running. The first post-decision proof should verify the
    collector schedule on the host, show recent snapshot timestamps, and report
    any cadence gaps before more strategy wiring depends on that history.
    2026-07-05: read-only OKX source decision is documented in
    `docs/research/crypto_edge_source_decision.md`; the default
    `sample_data/crypto_edges/live_collector_plan.json` now uses OKX for
    funding, open-interest, and basis rows. This does not approve OKX for live
    routing, derivatives execution, strategy promotion evidence, or
    order-routing venue use. Remaining proof: operator-host schedule, recent
    OKX snapshot timestamps, cadence-gap alerting, and downstream context
    strategy/provenance review. 2026-07-11 review of the proposed
    `check_edge_cadence.py` patch accepted the read-only checker direction but
    required revision before merge. 2026-07-11: revised code slice is ready for
    independent review. `services/analytics/edge_cadence.py` and
    `scripts/check_edge_cadence.py` add a read-only checker over stored
    funding/open-interest/basis snapshot timestamps. Defaults use 12h slow-family
    thresholds to measure collector snapshot freshness without assuming venue
    funding updates hourly; quote/order-book checks remain opt-in. The checker
    fails closed on missing/unparseable snapshots, treats a newly created empty
    store as missing families rather than a store error, and tests that `--alert`
    is best-effort/never-raise. Remaining proof is operational: verify the
    collector schedule on the host, show recent OKX snapshot timestamps, and
    wire/schedule the checker if accepted. 2026-07-11: scheduling-unit slice is
    ready for independent review. `packaging/systemd/cbp-edge-cadence.service`
    and `.timer` run the read-only checker hourly with `--alert`, carry no live
    arming tokens, and mirror the existing dead-man hardening pattern. Remaining
    proof is host-side: install/enable the timer, verify the collector's actual
    schedule, and show recent OKX snapshot timestamps.
    2026-07-22: executable OKX source-decision guard is ready for independent
    review. `tests/test_crypto_edge_source_decision_guard.py` pins the
    read-only research scope, evidence basis, unresolved host/data unknowns,
    hard boundaries, default collector-plan venues, and backlog/structural-doc
    links. This is docs/test only and does not change collectors, strategy
    context, promotion qualification, live routing, or execution behavior.
    2026-07-18 read-only Hetzner check recorded in
    `docs/checkpoints/hetzner_crypto_edge_runtime_gap_2026_07_18.md`:
    paper campaign status is healthy, but repo-local crypto-edge collection is
    not started or scheduled on the host, the host checkout is stale
    (`b86105b` on `review-stabilized` while local master is `65d3ce125`), the
    accepted cost/cadence checker tooling is absent there, and the remote live
    collector plan is still Binance-based rather than the accepted OKX source
    decision. Do not start the host crypto-edge collector from the stale
    checkout; first perform a reviewed host sync/deploy step to the accepted
    master boundary and OKX plan, then run the cadence checker and enable the
    read-only timer. 2026-07-18 follow-up: a read-only remote runtime status
    wrapper is ready for independent review. `make status-hetzner-edge-runtime`
    runs a bounded Tailscale SSH probe and fails closed unless the remote
    checkout is on the expected branch/commit, required cost/cadence/collector
    tooling is present, the derivatives plan uses the accepted OKX source, the
    collector loop is running, and collector/cadence schedules are visible. It
    does not deploy, start, stop, or mutate collectors; remaining proof is still
    operational: reviewed host sync/deploy, then enabling the accepted read-only
    collector/cadence schedule and showing recent OKX snapshot timestamps.
    2026-07-18 repo-side scheduler follow-up is ready for independent review:
    `packaging/systemd/cbp-crypto-edge-collector.service` adds the missing
    read-only collector loop service for the accepted OKX plan,
    `scripts/install_systemd_units.py` now verifies/installs all shipped
    long-running, oneshot, and timer units, and
    `report_hetzner_crypto_edge_runtime_status.py` accepts either system-level
    or user-level systemd evidence for collector/cadence schedules. No host
    unit was installed, enabled, started, or stopped by this patch; host-side
    operational proof remains open. 2026-07-18 path-rendering follow-up is
    ready for independent review: remote dry-run after the host sync exposed
    that the shipped unit templates point at `/opt/crypto-bot-pro` while the
    Hetzner checkout is `/srv/cryptkeep/app`. `install_systemd_units.py` now
    supports `--repo-dir` and renders `WorkingDirectory=`/`ExecStart=` into a
    temporary unit set before dry-run/install, so Hetzner can verify/install
    units for `/srv/cryptkeep/app` without editing templates. No host unit was
    installed, enabled, started, or stopped by this patch. 2026-07-18
    post-sync host check: Hetzner is clean at `3a7b4cbba` on `master`, the
    paper campaign remains healthy, and
    `install_systemd_units.py --repo-dir /srv/cryptkeep/app` dry-run verifies
    all nine units on-host. Remaining blockers are operational bootstrap plus
    one repo integration fix: the host has no `cbp` user, no `/etc/cbp/cbp.env`,
    no installed `cbp-*` units/timers, and the readiness wrapper still probes
    collector status without the packaged service `CBP_STATE_DIR`. Follow-up is
    ready for independent review: add a `--remote-state-dir` probe option
    defaulting to `/var/lib/cbp`, pass it into the remote collector status
    command as `CBP_STATE_DIR`, and align `cbp.env.example`/deployment docs
    with the packaged units' `/var/lib/cbp` state root. No host unit was
    installed, enabled, started, or stopped by this patch. 2026-07-18 host
    bootstrap was approved and executed: `/var/lib/cbp`, `/etc/cbp/cbp.env`,
    the `cbp` service identity, rendered units, and only the read-only
    `cbp-crypto-edge-collector.service` plus `cbp-edge-cadence.timer` were
    installed/enabled. Runtime readiness is green at `5a798801b`, and the
    paper campaign remains healthy. Follow-up finding: the collector fetched
    OKX open interest successfully, but `collect_once()` persisted only
    funding/basis/quotes and ignored `open_interest_rows` and
    `order_book_rows`; the cadence checker therefore remained correctly red
    with `missing: open_interest`. A persistence fix is ready for independent
    review; after merge/sync, restart the read-only collector and rerun
    `check_edge_cadence.py --json` to show fresh funding/open-interest/basis.
    2026-07-18 final host proof recorded in
    `docs/checkpoints/hetzner_crypto_edge_runtime_ready_2026_07_18.md`: PR
    #346 was merged and synced to Hetzner at `370c8122d`, only the read-only
    crypto-edge collector was restarted, `make status-hetzner-edge-runtime`
    reports `ok=True` with zero blockers, and `check_edge_cadence.py --json`
    under `CBP_STATE_DIR=/var/lib/cbp` reports fresh OKX funding,
    open-interest, and basis snapshots with `missing=[]`, `stale=[]`, exit
    code 0. The paper campaign remains healthy. This closes the host-side
    crypto-edge schedule/cadence proof; it does not authorize live routing,
    live trading, derivatives execution, or crypto-edge paper qualification.
    2026-07-21 read-only refresh recorded in
    `docs/checkpoints/runtime_check_2026_07_21.md`: local paper campaigns
    remain `2/2` running, Hetzner `ema_cross_default` remains `1/1` running,
    `es_daily_trend_v1` remains at `3/10` qualified round trips, and
    host-side `check_edge_cadence.py --json` under `CBP_STATE_DIR=/var/lib/cbp`
    reports OKX funding/open-interest/basis all fresh at
    `2026-07-21T21:10:42+00:00` with `missing=[]` and `stale=[]`.
    2026-08-13 read-only refresh recorded in
    `docs/checkpoints/runtime_check_2026_08_13.md`: Hetzner
    `ema_cross_default` remains `1/1` running and idle for the next UTC day,
    remote crypto-edge runtime is ready on `master` at `5eb36cbb5`, and
    host-side `check_edge_cadence.py --json` under `CBP_STATE_DIR=/var/lib/cbp`
    reports OKX funding/open-interest/basis all fresh at
    `2026-08-13T23:35:51+00:00` with `missing=[]` and `stale=[]`.
    2026-08-14 read-only refresh recorded in
    `docs/checkpoints/runtime_check_2026_08_14.md`: laptop paper campaigns
    remain `2/2` running, Hetzner `ema_cross_default` remains `1/1` running,
    canonical paper gate remains not ready at `3/5` qualified round trips with
    `2` remaining, remote crypto-edge runtime is ready on `master` at
    `5eb36cbb5`, and host-side `check_edge_cadence.py --json` under
    `CBP_STATE_DIR=/var/lib/cbp` reports OKX funding/open-interest/basis all
    fresh at `2026-08-14T05:03:59+00:00` with `missing=[]` and `stale=[]`.
    2026-08-23: the Hetzner crypto-edge runtime wrapper is updated to include
    the read-only `scripts/check_edge_cadence.py --json` result inside
    `make status-hetzner-edge-runtime`; the wrapper now blocks on missing or
    stale funding/open-interest/basis snapshots instead of only recommending a
    separate manual cadence command. This changes reporting only and does not
    deploy, start, stop, or mutate collectors.
    2026-09-01: local laptop-reset recovery exposed a repo-local collector
    compatibility failure with `ccxt` OKX `load_markets()`: OKX returned
    public market rows with `id=None`, and `ccxt.okx` raised a TypeError while
    sorting mixed `None` and string market IDs. A read-only collector fix is
    ready for independent review: for that exact TypeError shape only,
    `_open_public_exchange("okx")` falls back to `fetch_markets()`, drops rows
    with missing IDs, and calls `set_markets()` so accepted OKX
    funding/open-interest/basis collection can continue. Runtime proof showed
    `4541` raw OKX markets with `3` missing IDs, a one-shot collector run with
    `errors=0`, and `check_edge_cadence.py --json` returning `ok=true` with
    `missing=[]` and `stale=[]`; the persistent local research-only collector
    loop was restarted. This does not authorize live routing, derivatives
    execution, strategy promotion evidence, or live trading. Hetzner status was
    not refreshed because Tailscale SSH required an interactive auth check.
    2026-09-01 follow-up: after Tailscale browser approval cleared, regular SSH
    over the Tailscale IP showed Hetzner crypto-edge cadence fresh under
    `CBP_STATE_DIR=/var/lib/cbp` with `missing=[]`, `stale=[]`, and OKX
    funding/open-interest/basis snapshots from `2026-09-01T04:05:10+00:00`.
    `cbp-crypto-edge-collector.service` was active/running and
    `cbp-edge-cadence.timer` was active/waiting. The wrapper path that uses
    Tailscale SSH still reported a strict host-key failure, so direct SSH was
    used for this read-only proof. No host service was restarted.
15. Continue the derivatives/intraday roadmap as read-only data collection and
   replay only until compliance, margin, liquidation, reduce-only, and risk
   controls are proven.
   2026-07-25: executable derivatives/intraday roadmap guard is ready for
   independent review. `docs/research/derivatives_intraday_roadmap.md`
   records the read-only/replay boundary, blocked execution surfaces, required
   proof packet, and links to crypto-edge source, price-action, Databento, and
   websocket boundary docs. `tests/test_derivatives_intraday_roadmap_guard.py`
   pins that no derivatives execution, shorting, margin/leverage, live
   intraday routing, strategy promotion, Databento ingestion, or campaign/gate
   behavior is authorized by the roadmap. This is docs/test only and does not
   change collectors, campaigns, gates, data ingestion, live routing, or
   execution behavior.
16. Complete Hetzner host follow-through before any canonical `.cbp_state`
    migration: reviewed Hetzner canonical campaign manifest, reviewed
    stop-copy-verify-start procedure, fresh current-host runtime payload
    capture, and any required host scheduler/external-alert policy proof.
    Manifest-level single-owner proof is accepted and merged by PR #145.
    Runtime duplicate-process proof tooling is accepted and merged by PR #147,
    and the dated isolated-challenger deployment record shows accepted
    single-owner, first UTC-cycle, controlled-stop recovery, and backup restore
    rehearsal proof for `ema_cross_default`. Storage-health preflight tooling
    is independently accepted. The read-only host-health alerting wrapper is
    independently accepted. Canonical `.cbp_state` migration remains blocked.
    Use `docs/deployment_records/hetzner_canonical_state_migration_TEMPLATE.md`
    for the future migration packet. Before any server setup or migration
    command is treated as actionable, verify the host has the required
    privilege path (`sudo`/root), `python3.12-venv` or equivalent installed,
    and the expected app path. Runbook commands must use the Tailscale host or
    actual server address, not placeholders, and must distinguish laptop
    commands from server commands.
17. Keep `scripts/SCRIPTS.md`, `docs/GOLDEN_PATH.md`, and this file aligned
    whenever operator commands or workflow change.
    2026-07-22: LOW-risk alignment guard accepted for the script/operator map.
    `make archive-walk-forward` and `make archive-parameter-sweep` now wrap the
    existing research-only archive runners, `scripts/SCRIPTS.md` lists both
    wrappers and points to `tests/test_script_index_alignment_guard.py`, and the
    Makefile `script-index` target points operators to `docs/GOLDEN_PATH.md`
    plus `scripts/SCRIPTS.md` instead of the stale `ls scripts/*.py` hint. The
    new guard pins the daily-path/full-map boundary, item #17 backlog link,
    root paper-collector authority, accepted research wrapper links, and key
    canonical paper commands.
18. Maintain the retired-family regression guard. `services/paper`,
    `services/marketdata`, `services/strategy`, `services/strategy_runner`, and
    `services/storage` are retired. Do not reintroduce those packages without a
    new accepted architecture decision.
19. [DONE — accepted 2026-07-03] Classify candidate-advisor strategy coverage
    against the registry.
    `services/signals/candidate_advisor.py` allows only a subset of
    `services/strategies/strategy_registry.py::SUPPORTED`; the excluded set
    (`breakout_volume`, `gap_fill`, `sma_200_trend`, `volatility_reversal`) is
    now explicit with rationale via `ADVISOR_EXCLUDED_STRATEGIES`, and a
    test that fails whenever a registered strategy is neither advisor-allowed
    nor deliberately excluded. This prevents future discovery wiring from
    silently omitting strategies. Implementation proof was independently
    reviewed and accepted by the human operator on 2026-07-03: the advisor now
    has an explicit exclusion-rationale map, and the test suite fails if any
    registry strategy is not classified as allowed or excluded.
20. Harden the strategy-runner single-instance lock. `_acquire_lock()` in
    `services/execution/strategy_runner.py` is check-then-write and has no
    stale-PID recovery. Replace it with an atomic create path and a stale-lock
    reclamation proof: dead PID lock is reclaimed, and concurrent acquire
    attempts allow exactly one winner. A 2026-07-03 audit found
    `services/runtime/managed_component.py::clean_stale_lock_file()` already
    exists and is used by the intent consumers; prefer adopting that helper in
    the runner before building a second stale-lock mechanism. 2026-07-05:
    implementation proof is ready for independent review: `_acquire_lock()`
    now uses atomic `O_CREAT|O_EXCL`, reclaims only dead-PID locks through the
    shared `clean_stale_lock_file()` helper, treats malformed locks as held,
    and targeted tests cover live PID refusal, dead PID reclaim, release/reacquire,
    malformed-lock fail-closed behavior, and a simulated race.
21. Make sample-mode provenance agree with the actual data source. Current
    paper evidence stamps `ohlcv_sample_mode` from `CBP_USE_SAMPLE_OHLCV`; the
    promotion gate then treats that label as authoritative. Derive the sample
    label from the data source/path used, and make mismatched env/source labels
    fail closed or record explicit sample provenance. 2026-07-05:
    implementation proof is ready for independent review:
    `strategy_runner._fetch_public_ohlcv()` now returns the actual source
    alongside rows (`sample_ohlcv` with file path, `public_ohlcv`, or `none`;
    the defensively retained sample-fallback branch is tagged
    `sample_fallback`), `_public_ohlcv_evidence_extra()` derives
    `market_data_source`/`ohlcv_sample_mode` from that source with
    `ohlcv_sample_mode_origin="source"`, records the env claim as
    `ohlcv_sample_mode_env`, and sets `ohlcv_source_mismatch` on any
    disagreement; the runner loop holds the signal fail-closed on mismatch
    (operator-visible `sample_mode_provenance_mismatch` status, no signal, no
    intent). Env-only stampers (`evidence_logger._sample_provenance_stamp`,
    collector `_campaign_provenance_extra`, `es_daily_trend`
    `_default_evidence_extra`, `_executor_submit` shadow fill stamp) now mark
    labels `ohlcv_sample_mode_origin="env"`, and the executor-submit stamp no
    longer hardcodes `ohlcv_sample_mode=False`. Gate provenance bucketing is
    proven unchanged for both new-field and legacy records. Remaining work
    (2026-07-05 audit finding): the local OHLCV snapshot store
    (`local_data_reader.write_local_ohlcv_snapshot`) persists rows without
    source metadata, sample-mode runs persist sample rows into that shared
    store, and downstream stampers label snapshot reads `local_snapshot`,
    which the gate counts as public — so sample data can still launder into
    public provenance through the snapshot store. Closing that requires
    snapshot-schema source metadata or skipping snapshot persistence in
    sample mode; treat as a separate reviewed change. 2026-07-06:
    implementation proof for that remaining work is ready for independent
    review: `write_local_ohlcv_snapshot` (single production writer, called
    only via the runner persist helper) now writes a versioned envelope
    `{version: 2, source, written_ts, candles}` with the source threaded
    from the fetch branch that actually produced the rows
    (sample/public); idempotent rewrites compare candles+source so
    `written_ts` does not churn; the legacy bare-list format still reads
    everywhere (scanner, correlation inputs, signal quality, dashboards) and
    legacy/corrupt/missing snapshots report `source="unknown"` fail-closed
    via the new read-only `load_local_ohlcv_snapshot_provenance()` inspector;
    a caller omitting `source` mints `unknown`, never public.
    `signal_quality` provenance now carries `snapshot_source`/
    `snapshot_source_legacy` for both local-snapshot and explicit-file loads,
    so sample ancestry is visible in the campaign-planner artifact chain.
    Deliberate scope boundaries: `symbol_scanner` and `correlation_inputs`
    remain unlabeled research readers (inspectable via the provenance
    reader); the market-ticker snapshot store (`market_*.json`, written by
    the live poller/WS feed) is not sample-fed and was left untouched. This
    adds the provenance substrate, but no gate logic changed; if future
    promotion evidence accepts `market_data_source=local_snapshot`, add a
    separate reviewed gate assertion requiring non-legacy
    `snapshot_source=public_ohlcv` before treating this laundering path as
    closed end-to-end.
22. Add per-strategy governance configs before promoting additional
    challenger strategies. `configs/strategies/es_daily_trend_v1.yaml` is the
    only full strategy YAML contract today; challenger campaigns currently
    rely heavily on presets/defaults. Before `ema_cross`, `breakout_donchian`,
    `pullback_recovery`, or future context strategies become promotion
    candidates, add strategy-specific config files with backtest expectations,
    risk settings, evidence contract, no-trade filter settings, and
    manual-review criteria. Explicitly verify that each strategy's documented
    no-trade filters are enabled or consciously waived in its campaign config;
    documented discipline that is off in runtime config does not count as
    governed discipline. 2026-07-04: governance-only configs are added for
    `ema_cross_default`, `breakout_default`, and
    `pullback_recovery_default`. They are not campaign manifests, keep
    `trade_enabled=false`, require archive-backed baselines and manual review,
    and are guarded by a test that verifies inactive activation state,
    registry-backed strategy names, null baseline placeholders, net-fee manual
    review, and explicit no-trade filter contracts. Remaining work: populate
    accepted archive baselines and create separately reviewed campaign
    manifests before any challenger is promoted.
23. Wire paper/gate event alerting into the existing alert dispatcher. The
    dispatcher is now used for Hetzner host-health alerts, but paper events
    still depend on manual polling. Add trigger-based alerts for qualified
    round-trip changes, gate-ready transitions, campaign stop/failure,
    evidence-write failure thresholds, and strategy decision changes. Keep the
    first implementation read-only/notification-only. 2026-07-10: the first
    notification-only slice is ready for independent review —
    `services/alerts/paper_gate_events.py` wires two event families through
    the existing dispatcher: (a) evidence-writer status TRANSITIONS
    (ok->degraded warning, ->refusing critical, ->ok info recovery),
    alerting once per transition never per failure, hooked into
    `evidence_logger` after status persistence and wrapped never-raise so
    an alerting problem cannot affect an evidence write; this closes the
    alert-dispatch hook that substrate #9 deferred here; (b) promotion-gate
    flips: `check_promotion_gates.py --alert` compares against a persisted
    per-gate snapshot (`runtime/health/promotion_gates.last.json`, written
    on every run so a first `--alert` run has a baseline) and dispatches
    ready-lost critical / gate-flipped-fail warning / ready-recovered info;
    first run is a silent baseline; a raising channel is contained so the
    snapshot always advances (a frozen snapshot would re-alert forever and
    break recovery detection — caught by the batch's own never-raise test).
    2026-07-10: the second notification-only slice is ready for
    independent review: `check_promotion_gates.py` now emits an additive
    `paper_progress` object for paper-stage checks with the structured
    qualified round-trip count the machine gate already uses
    (`round_trips_recorded`, `round_trips_required`,
    `round_trips_remaining`, `round_trips_ready`, source, and diagnostic
    all-history count), and `paper_gate_events` persists that progress in
    the existing `promotion_gates.last.json` snapshot. With `--alert`,
    qualified round-trip count changes dispatch exactly once per change:
    increases are info, decreases are warning because they usually mean
    requalification/provenance recalculation invalidated history. First run
    remains a silent baseline; unchanged counts do not re-alert; a raising
    alert channel is contained so the snapshot still advances. 2026-07-11:
    Batch A for the remaining alert lane is accepted:
    `services/alerts/campaign_events.py` alerts once per campaign status
    transition into stop/failure states (`failed`/`error`/`aborted` critical,
    `stopped` warning), keeps first observation as a silent baseline, does not
    alert on normal `completed`, and never raises. The hook is in
    `paper_strategy_evidence_service._write_status()` after the status file
    write succeeds, so notification failure cannot block campaign status
    advancement. 2026-07-11: Batch B for the remaining alert lane is accepted:
    `services/alerts/strategy_decision_events.py` alerts
    when the persisted strategy evidence comparison shows strategy decision
    changes versus the previous latest artifact. First persisted evidence is a
    silent baseline, rank/score-only movement stays silent, new/improved
    decisions alert at info level, degraded decisions alert at warning level,
    and retire decisions alert at critical level. The hook is in
    `services.backtest.evidence_cycle.persist_strategy_evidence()` after the
    latest/history JSON artifacts are written, so notification failure cannot
    block evidence persistence. Boundary: the dormant duplicate
    `services/backtest/evidence_persist.py` was not widened because no active
    caller imports it; active callers use `evidence_cycle.persist_strategy_evidence`.
24. Write explicit stop and retirement criteria before any strategy advances
    beyond paper. Define, in a decision record, what evidence retires a
    strategy, freezes it, keeps it in paper, or stops the broader project.
    Include thresholds for losing qualified round trips, drawdown, negative
    expectancy versus baseline, repeated evidence/provenance failures, and
    operator time/cost limits. Include a project-level thesis gate with a
    dated review window: if the flagship profitability hypothesis does not show
    positive walk-forward expectancy after measured costs by that date, the
    operator must revise the thesis, change strategy family/horizon, or wind
    the project down. This decision should be written before a drawdown or
    gate-green event so the system is not judged emotionally while under
    pressure. 2026-07-03: baseline policy is written in
    `docs/STRATEGY_STOP_AND_RETIREMENT_POLICY.md`; future strategy promotion
    still requires a dated per-strategy decision record using fresh gate output.
    2026-07-22: executable stop/retirement policy guard is ready for
    independent review as part of the operator runbook guard batch.
    `tests/test_operator_runbook_policy_guards.py` pins the decision table,
    retirement triggers, project thesis gate, and non-negotiable rules. This
    is docs/test only and does not change runtime behavior.
25. Write and rehearse the first-hour paper-to-shadow runbook before the paper
    gate turns green. The runbook should start from fresh gate output, confirm
    baseline/manual-review status, confirm `observe_only` and no live routing,
    promote the stage, start the shadow session, verify shadow signal and
    would-be-fill evidence is being written, verify zero venue orders, and
    record rollback/recovery steps. This is separate from the later launch
    evidence packet; it is the operator checklist for the first shadow hour.
    2026-07-03: runbook is written in
    `docs/PAPER_TO_SHADOW_FIRST_HOUR_RUNBOOK.md`; rehearsal remains open until
    a future checkpoint records command output, stage before/after, shadow
    evidence, and zero venue orders.
    2026-07-22: executable first-hour runbook guard is ready for independent
    review as part of the operator runbook guard batch.
    `tests/test_operator_runbook_policy_guards.py` pins preconditions,
    first-hour safety checks, abort conditions, rollback proof, and
    not-rehearsed status. This is docs/test only and does not change runtime
    behavior; rehearsal evidence remains open.
26. Decide whether to widen the paper universe to accelerate qualified evidence.
    The current canonical paper gate is slow because daily strategies on a
    narrow symbol set produce few qualified round trips. Before changing the
    campaign, write a decision record covering candidate symbols, venue/source
    support, provenance qualification, correlation/non-independence caveats,
    per-symbol risk caps, and whether cross-symbol round trips count toward the
    same strategy gate. If cross-symbol round trips can count, first replace
    the current `scripts/check_promotion_gates.py::_count_round_trips`
    `min(buys, sells)` helper with symbol-aware, chronological entry/exit
    pairing or explicitly document the gate as single-symbol-only. Do not
    retroactively count unqualified history or widen the universe without
    preserving the evidence contract. 2026-07-04: decision record written in
    `docs/strategies/paper_universe_widening_decision_2026-07-04.md`; do not
    widen the canonical campaign yet. Reconsider only after fresh gate output,
    symbol-aware round-trip counting or explicit single-symbol gate policy,
    per-symbol provenance/risk proof, and correlation/non-independence
    acceptance.
    2026-07-15: symbol-aware fallback counter proof is ready for independent
    review. `scripts/check_promotion_gates.py::_count_round_trips()` no longer
    uses `min(total_buys,total_sells)`; it sorts fills chronologically and
    counts only same-symbol long cycles that return open quantity to zero.
    Tests pin no bridge across symbols, sell-before-buy refusal, multi-symbol
    chronological pairing, and legacy side-only rows. This does not widen the
    canonical campaign; fresh gate output, per-symbol risk/provenance proof,
    and correlation/non-independence acceptance remain required before any
    paper-universe change.
    2026-07-22: executable paper-universe widening decision guard is ready for
    independent review. `tests/test_paper_universe_widening_decision.py` pins
    the do-not-widen status, reconsideration requirements, packet fields, and
    no-runtime-change outcome. This is docs/test only and does not change
    campaign, manifest, strategy config, gate threshold, or runtime behavior.
    2026-08-25: backlog scope added for Hetzner Binance/Gate.io paper-research
    venue expansion. Binance and Gate.io are already visible supported venue
    surfaces (`docs/EXCHANGES.md`, preflight exchange support, symbol router,
    and CCXT availability), but the current Hetzner paper manifest runs only
    Coinbase `ema_cross_default`. Next implementation should add a proposed
    Hetzner paper/research manifest or planner output for `gateio` and
    separately guarded `binance`, require OHLCV reachability preflight for each
    venue/symbol/timeframe, record provenance expectations per row, keep
    evidence isolated from the canonical `es_daily_trend_v1` state directory
    and gate count, and keep Binance behind `CBP_VENUE=binance*` plus
    `CBP_ALLOW_BINANCE=1`. Explicit exclusions: no exchange credentials, no
    live routing, no order submission, no canonical paper-gate widening, and no
    Hetzner package/service mutation in the same change.
    2026-08-25: implementation artifact added:
    `configs/paper_evidence_campaigns.hetzner.multi_venue_proposed.json`
    records disabled Gate.io and Binance `ema_cross` BTC/USDT paper/research
    candidate rows with isolated `.cbp_state_challengers` state directories.
    `docs/strategies/hetzner_multi_venue_paper_research_proposals.md` records
    the required OHLCV preflight commands and boundaries. This does not modify
    the active Hetzner manifest; rows remain disabled and must not count toward
    the canonical `es_daily_trend_v1` gate.
27. Write a single-operator continuity and absence runbook before shadow or
    server migration becomes the primary operating mode. The system currently
    depends on one operator knowing which checks, hosts, branches, campaigns,
    and recovery procedures matter. Document what continues running if the
    operator is unreachable for a week or a month, what alerts must fire, what
    automatically degrades or stops, who can access the host/repo if needed,
    how to restore from backup, and which actions are explicitly forbidden
    without the operator. This is not a staffing fix; it is the minimum proof
    that the system fails safe without constant human attention. 2026-07-03:
    baseline runbook is written in `docs/SINGLE_OPERATOR_CONTINUITY.md`;
    backup restore, dead-man alert, and stopped-campaign recovery drills remain
    open proof.
    2026-07-22: executable continuity/absence runbook guard is ready for
    independent review as part of the operator runbook guard batch.
    `tests/test_operator_runbook_policy_guards.py` pins absence horizons,
    fail-toward-no-new-risk behavior, emergency delegate permissions/forbidden
    actions, and open-drill proof list. This is docs/test only and does not
    change runtime behavior; host drills remain open.
28. Correct paper fee/PnL semantics before treating expectancy gates as
    profitability evidence. `storage/paper_trading_sqlite.py::apply_fill()`
    currently subtracts buy fees from cash and sell fees from proceeds, but the
    returned/stored `realized_pnl_usd` is gross of both legs:
    `(sell_price - avg_price) * qty`. `services/execution/paper_engine.py`
    writes that value to fill evidence as `pnl_usd`, and
    `scripts/check_promotion_gates.py::_check_expectancy()` gates on that field.
    Also verify the active campaign config uses realistic `paper_fee_bps` and
    slippage, because `services/execution/paper_fees.py` defaults ad hoc paper
    fee lookups to `0.0`. Smallest acceptable path: make evidence PnL net of
    buy/sell fees or add a versioned net field that gates consume, preserve
    historical comparability explicitly, and add a golden round-trip test where
    flat price plus fees yields negative `pnl_usd` and fails expectancy. Land
    this before activating dormant sizing, setup-quality thresholds,
    confirmation gates, or parameter sweeps; otherwise those systems optimize
    gross-of-fee PnL and can amplify a measurement error. 2026-07-04:
    implementation proof is independently accepted: paper buy fees are
    folded into cost basis, sell fees reduce realized proceeds, new fill
    evidence carries `pnl_usd_semantics=net_of_fees`, and targeted tests prove
    a flat round trip with 10 bps fees records negative `pnl_usd` and fails the
    expectancy helper. Acceptance is with risk. Remaining operational proof:
    verify the active campaign config uses realistic fee/slippage values, and
    segment old
    gross/unknown-semantics evidence during future analysis. 2026-07-05:
    implementation proof is ready for independent review: the promotion gate
    now reports `expectancy_pnl_semantics`, `expectancy_mixed_semantics`, and
    `expectancy_semantics_warning` on both JSONL and paper-history metric paths
    without changing expectancy pass/fail behavior. Remaining operational proof:
    verify host fee/slippage values and use the report fields to segment old
    gross/unknown-semantics evidence. 2026-07-12: implementation proof is ready
    for independent review for the host cost-assumption validator.
    `scripts/check_cost_assumptions.py` now reads `user.yaml` strictly and
    reports the paper-fill, evidence-scoring, dormant `paper_fees`, and
    backtest/walk-forward cost surfaces without mutating config or trading
    state. It fails on explicit invalid/non-finite/negative paper fee/slippage
    values, fails when modeled round-trip cost is below the declared
    `CBP_MIN_PLAUSIBLE_ROUND_TRIP_BPS` policy floor, warns on code defaults,
    zero modeled fee/slippage, dormant lookup ambiguity, and independently
    sourced backtest costs. Audit-invariant tests pin the traced structural
    claims so the report must be revised if `paper_fees` gains production
    callers, backtests start reading `user.yaml`, or cost defaults drift.
    Local laptop run returned `overall=warning`: paper engine uses code defaults
    `7.5/5.0`, modeled round-trip is plausible at `25.0` bps, and
    evidence/backtest defaults are separately sourced at `10.0/5.0`. Remaining
    operational proof: run the validator on the Hetzner host and record/segment
    evidence by the reported cost assumptions.
29. Make market-quality guard defaults fail closed before shadow evidence is
    treated as cost/slippage proof. `services/risk/market_quality_guard.py`
    currently defaults to `block_when_unknown=false`, `require_bid_ask=false`,
    and `max_spread_bps=500`, so missing quote data can pass with
    `reason=no_quote_data`. Start with campaign-config opt-in
    (`block_when_unknown: true`, `require_bid_ask: true`, realistic spread
    caps), then flip code defaults after one observed cycle proves the stricter
    settings do not create false-block storms. Proof: missing-quote fixture
    holds the signal/order with an operator-visible reason, while fresh quoted
    paths remain unaffected. 2026-07-04: partial implementation proof is ready
    for independent review: the canonical paper engine no longer falls back to
    `60000.0` when market quality returns `ok=true` without a usable
    `price_used`/`last`; the order is held with
    `market_quality:no_reference_price`. 2026-07-04: human/operator
    independent review accepted this partial implementation with risk.
    Remaining work: committed or operator-applied strict market-quality config,
    one observed no-storm cycle, and later default flip if the stricter
    settings prove stable. 2026-07-05: implementation proof is ready for
    independent review: `config/templates/market_quality_strict.yaml` documents
    the fail-closed operator config and targeted tests prove missing quotes hold
    with a visible reason, fresh quotes pass, wide spreads are blocked, and code
    defaults remain permissive until an accepted no-storm cycle supports the
    default flip. Remaining work: apply the template to the host config and
    observe one no-storm cycle.
30. Govern activation of dormant risk-based sizing before it influences paper
    or shadow evidence. `services/strategies/es_daily_trend.py::decide()` and
    `compute_position_size()` implement ATR-stop, regime-aware,
    capital-at-risk sizing, but repo usage currently shows production campaign
    orders using the runner's fixed `cfg["qty"]` path while `decide()` is only
    imported by tests. Treat activation as a strategy/evidence change, not a
    cleanup. Prerequisites: net-fee paper PnL semantics are fixed, archive
    walk-forward evidence shows the sizing policy improves risk-adjusted
    expectancy after costs, and a config flag can keep the canonical campaign
    on fixed size. Proof: fixed-size behavior unchanged by default; flagged
    sizing path emits size provenance, respects stage caps, and cannot increase
    exposure beyond configured notional/risk limits. 2026-07-04: default
    fixed-size behavior is now guarded by a runner regression: `sma_200_trend`
    with risk-sizing fields present still emits the configured fixed `qty`.
    Remaining work: actual risk-based sizing activation remains deferred behind
    archive/walk-forward proof, explicit config, size provenance, and exposure
    cap tests.

## Deferred Live-Money Substrate Backlog
These items are not blockers for the current paper/research campaign, but they
must be resolved or explicitly accepted before any capped-live capital exposure.

1. Convert order qty/price/fee/PnL math to `Decimal` with per-venue step size,
   lot size, and min-notional quantization. Start with the order-construction
   boundary quantizer before a full end-to-end migration, and write venue
   golden tests before changing behavior. Blocks capped live.
   2026-07-13 order-boundary quantized-validation slice is proof-ready for
   independent review: `services/execution/place_order.py` now applies the
   existing exchange precision helpers before local notional, funding, and
   market-rule validation, then submits those same normalized amount/price
   values to `create_order()`. This preserves the existing guard order: risk
   sink/system health/basic parse/kill switch/arming/config gates still run
   before precision normalization. Tests prove sync and async order paths
   validate and record the normalized notional, block if precision normalizes
   amount to zero, and do not run precision normalization before a kill-switch
   block. Remaining substrate #1 work: full Decimal migration across qty,
   price, fee, and PnL math, plus per-venue step-size/lot-size/min-notional
   golden tests before any capped-live exposure.
   2026-07-13 market-rule Decimal validation slice is proof-ready for
   independent review: `services/markets/math_utils.py` now exposes finite
   Decimal parsing/product/step helpers, and `services/markets/rules.py`
   validates min-notional, min-qty, and qty-step with Decimal values instead
   of float comparison/tolerance math. Poisoned non-finite venue rules now
   fail closed with `INVALID_MARKET_RULES` instead of flowing into live order
   validation. New venue-style golden tests pin Coinbase-style
   `0.00000001` quantity steps, Binance-style `0.001` quantity steps,
   min-notional boundaries, and non-finite cached rule rejection. Remaining
   substrate #1 work: full Decimal migration across order qty/price, fee, and
   PnL math, plus broader per-venue golden fixtures before capped-live
   exposure.
   2026-07-14 order-notional Decimal slice is proof-ready for independent
   review: `services/execution/place_order.py` now estimates normalized order
   notional with Decimal multiplication before max-order and max-daily-notional
   comparisons, while preserving the existing float `notional` value passed to
   downstream recording APIs. Tests pin exact boundary cases that binary float
   math can misclassify (`0.1 * 0.2 == 0.02`; `0.1 + 0.2 == 0.3`) and prove a
   non-finite daily-notional snapshot blocks with
   `CBP_ORDER_BLOCKED:invalid_notional_input:daily_notional`. Remaining
   substrate #1 work: full Decimal migration across fee and PnL math plus
   broader end-to-end Decimal value transport before capped-live exposure.
   2026-07-14 live-risk-gate notional Decimal slice is proof-ready for
   independent review: `services/risk/live_risk_gates.py` now estimates
   `notional_usd` with finite Decimal parsing/multiplication before the
   `MAX_NOTIONAL_PER_TRADE` comparison. Exact boundary cases such as
   `0.1 * 0.2 == 0.02` now pass, explicit `notional_usd="0.02"` remains
   accepted, and poisoned `notional_usd=NaN` now blocks with
   `CANNOT_ESTIMATE_NOTIONAL_USD` instead of bypassing the cap through
   `NaN > cap == false`. Remaining substrate #1 work: full Decimal migration
   across fee/PnL/storage paths and broader end-to-end Decimal value transport.
   2026-07-14 live-risk-gate daily-loss PnL Decimal slice is proof-ready for
   independent review: `LiveRiskGates.check_live()` now parses
   `realized_pnl_usd` through finite Decimal validation before the daily-loss
   comparison. Poisoned `realized_pnl_usd=NaN` now blocks with
   `CANNOT_ESTIMATE_REALIZED_PNL_USD` instead of bypassing the loss cap through
   `NaN <= limit == false`, while numeric string PnL still follows the existing
   `MAX_DAILY_LOSS_EXCEEDED` policy. Remaining substrate #1 work: full Decimal
   migration across fee/PnL/storage paths and broader end-to-end Decimal value
   transport.
   2026-07-14 live-risk-limit config finite-validation slice is proof-ready
   for independent review: `LiveRiskLimits.from_dict()` now parses
   `max_daily_loss_usd`, `max_notional_per_trade_usd`, and
   `max_position_notional_usd` through finite Decimal validation, and rejects
   fractional/non-finite `max_trades_per_day`. This prevents `NaN`/`inf` live
   risk limits from being accepted as configured caps before the gate runs.
   Remaining substrate #1 work: full Decimal migration across fee/PnL/storage
   paths and broader end-to-end Decimal value transport.
   2026-07-14 risk-daily finite-write slice is proof-ready for independent
   review: `services/risk/risk_daily.py` now validates live daily ledger write
   inputs through finite Decimal parsing before mutating `realized_pnl_usd`,
   `fees_usd`, or `notional_usd`. `add_pnl()` raises before mutation on
   non-finite PnL/fee, `apply_fill_once()` rolls back the fill-dedupe insert
   and returns `False`, and `record_order_attempt()` preserves its best-effort
   never-raise contract while ignoring non-finite notional without incrementing
   trades/notional. Remaining substrate #1 work: full Decimal transport through
   storage schemas and position/PnL accounting semantics.
   2026-07-14 funding-gate required-balance Decimal slice is proof-ready for
   independent review: `services/execution/place_order.py` now estimates the
   buy-side required spendable balance with Decimal multiplication, including
   the funding fee buffer, before comparing against the venue balance. Exact
   buffered boundary cases such as `0.1 * 0.2 * 1.1 == 0.022` now pass instead
   of being blocked by binary float over-estimation. The legacy
   `CBP_FUNDING_FEE_BUFFER_FRACTION` fallback contract is preserved: blank,
   invalid, non-finite, or negative values still fall back to `0.005`.
   Remaining substrate #1 work: full Decimal transport through storage schemas
   and position/PnL accounting semantics.
   2026-07-14 live-intent atomic risk-claim Decimal slice is proof-ready for
   independent review: `storage/live_intent_queue_sqlite.py::atomic_risk_claim`
   now parses the max-notional cap, notional estimate, and stored
   `risk:notional` accumulator through finite Decimal validation before the
   atomic cap comparison and accumulator update. Exact boundaries such as
   stored `0.1` plus estimate `0.2` against cap `0.3` now pass, while existing
   `risk:invalid_cap`, `risk:invalid_notional_est`, and `risk:corrupt_state`
   contracts are preserved. Remaining substrate #1 work: broader Decimal
   storage transport and position/PnL accounting semantics.
   2026-07-14 live-intent consumer notional-estimate Decimal slice is
   proof-ready for independent review: both
   `services/execution/live_intent_consumer.py` and the compat
   `services/execution/intent_consumer.py` now estimate intent notional with
   Decimal before the min-order-notional check and atomic risk claim. Exact
   boundaries such as `0.1 * 0.7 == 0.07` now pass the min-order threshold
   instead of being rejected by binary float under-estimation. Remaining
   substrate #1 work: broader Decimal storage transport and position/PnL
   accounting semantics.
   2026-07-14 live-intent queue finite-ingestion slice is proof-ready for
   independent review: `storage/live_intent_queue_sqlite.py::upsert_intent`
   now validates `qty` and optional `limit_price` through finite Decimal
   parsing before writing the live intent row. Non-finite queue numeric inputs
   such as `qty=NaN` or `limit_price=inf` raise before mutation, while existing
   insert-only queue semantics and `REAL` storage are preserved. Remaining
   substrate #1 work: broader Decimal storage transport and position/PnL
   accounting semantics.
   2026-07-14 live-trading store finite-ingestion slice is proof-ready for
   independent review: `storage/live_trading_sqlite.py` now validates live
   order `qty`/optional `limit_price` and live fill `qty`/`price`/optional
   `fee` through finite Decimal parsing before writing `REAL` columns.
   Non-finite numeric inputs such as `qty=NaN`, `price=inf`, or `fee=-inf`
   raise before mutation, while existing schema and read/list shapes are
   preserved. Remaining substrate #1 work: broader Decimal storage transport
   and position/PnL accounting semantics.
   2026-07-14 order-manager store finite-ingestion slice is proof-ready for
   independent review: `storage/order_manager_store_sqlite.py` now validates
   idempotency `qty`/`price` and order snapshot `qty`/`price`/`filled`/
   `average` through finite Decimal parsing before writing `REAL` columns.
   Non-finite numeric inputs such as `qty=NaN`, `price=inf`, or
   `filled=-inf` raise before mutation, while missing snapshot numeric fields
   retain the existing zero-default behavior. Remaining substrate #1 work:
   broader Decimal storage transport and position/PnL accounting semantics.
   2026-07-14 live-position store finite-ingestion slice is proof-ready for
   independent review: `storage/live_position_store_sqlite.py` now validates
   fill `qty`/`price` through finite Decimal parsing before live position or
   fill rows can be mutated, and read-only reconciliation rejects non-finite
   `exchange_qty`/`tolerance` inputs with an explicit failed result instead
   of computing `NaN` drift. The existing weighted-average accounting and
   gross realized-PnL semantics are unchanged. Remaining substrate #1 work:
   broader Decimal storage transport and position/PnL accounting semantics.
   2026-07-14 follow-up proof is ready for independent review:
   `scripts/reconcile_positions.py` now treats invalid drift-threshold config
   as a command error before exchange access and can write the halt flag for
   invalid reconciliation results whose `drift` is `None` without crashing.
   This preserves the read-only reconciliation contract while preventing a
   poisoned exchange quantity or tolerance from bypassing the operator-visible
   failure artifact.
   2026-08-13: implementation slices accepted after independent review. This
   closes the review/acceptance tracking status for the Decimal and
   finite-validation slices above without changing runtime behavior; the
   remaining substrate #1 work is the explicitly named broader Decimal storage,
   fee, and PnL transport/accounting migration before capped-live exposure.
2. Make trading config fail closed. Unparseable or corrupt runtime trading
   config must halt with an alert instead of defaulting to `{}`. Sweep only
   trading-critical broad exception handlers first. Blocks live; paper-adjacent
   because bad config can poison evidence context.
   2026-07-03: first implementation slice is proof-ready on the strategy-runner
   dispatch path: existing corrupt `user.yaml` now stops the runner with
   `config_load_failed` before intents/orders/fills can be produced. Remaining:
   sweep other runtime trading-config consumers before capped live, especially
   bot startup, live executor/consumer/reconciler, and risk-gate config reads.
   2026-07-03 follow-through: active paper evidence path proof is ready:
   strategy-runner in-loop user-config reloads and paper evidence service
   evidence persistence now use strict config loading. Corrupt mid-session
   config writes `config_load_failed`, emits no runner intent, and prevents
   leaderboard/decision-record persistence from `{}` defaults. Remaining
   capped-live blocker: safety/load-gates and live executor/consumer/reconciler
   config consumers still require their own fail-closed sweep. Include
   admin/live enable-disable wizards in that sweep so operator-facing live
   controls do not read corrupt config through a permissive path. 2026-07-05:
   implementation proof is ready for independent review for the live-router
   order decision boundary: missing/invalid reference prices now fail closed
   before safety gates run, and safety-gate exceptions now block with
   `safety_check_error_fail_closed:*` instead of allowing the order. Remaining
   capped-live blocker: continue the fail-closed sweep across live executor,
   consumer, reconciler, risk-gate config reads, and admin live controls.
   2026-07-10: risk-gate/router slice is ready for independent review.
   Shared bug class: NaN/inf survives `float()` and makes threshold/cap
   comparisons silently false. Covered surfaces: (a)
   `market_quality_guard.check` fails closed with
   `invalid_threshold:<name>` for non-numeric, non-finite, or non-positive
   base/per-symbol thresholds instead of passing stale ticks or wide
   spreads; (b) `order_router` retry knobs are bounded
   (`max_order_retries` 0..10, base delay 0.05..60s, max delay
   0.05..300s; garbage -> defaults) so corrupt config cannot hang or
   disable backoff; (c) `live_arming._float_value` skips non-finite cap
   candidates and falls through to the next/default value; (d)
   `atomic_risk_claim` rejects non-finite caps (`risk:invalid_cap`),
   bad estimates (`risk:invalid_notional_est`), and poisoned stored
   accumulators (`risk:corrupt_state`) while preserving the cap<=0
   no-cap contract. 2026-07-10 follow-up: `risk_daily.snapshot` now
   marks corrupt/non-finite fields with `risk_daily_corrupt`,
   `risk_daily_corrupt_fields`, and `risk_daily_corrupt_reason`; direct
   `place_order` blocks with `CBP_ORDER_BLOCKED:risk_daily_corrupt`;
   `RiskDailyDB.realized_today_usd()` raises on corrupt snapshots; and
   the ops telemetry/risk-gate path surfaces the marker and classifies it
   as `FULL_STOP`. Remaining sweep: live executor, consumer/reconciler
   config reads, admin live controls. 2026-07-15: ops raw-signal
   fail-closed proof is ready for independent review. `RawSignalSnapshot`
   now rejects non-finite or domain-invalid telemetry numerics before storage
   (`order_reject_rate`, websocket lag, venue latency, realized volatility,
   exposure, and leverage must be finite/non-negative; PnL and drawdown must
   be finite), `RiskGateSignal` rejects invalid `system_stress`, and
   `process_latest_raw_signal()` converts already-persisted corrupt raw
   snapshots into a `FULL_STOP` gate with hazard `ops_raw_signal_invalid`
   instead of letting `NaN` bypass threshold comparisons or crash the service.
   2026-07-15 follow-up: live executor market-quality exception fail-closed
   slice is ready for independent review. `_executor_submit.submit_pending_live()`
   no longer treats `market_quality_guard` exceptions as pass-through; a guard
   exception now keeps the intent pending with
   `market_quality_block:guard_error:<ExceptionType>` and no exchange submit is
   attempted. Normal market-quality block behavior is unchanged. Remaining
   sweep: consumer/reconciler config reads and admin live controls. 2026-07-15
   follow-up: live intent consumer market-quality exception fail-closed slice
   is ready for independent review. `live_intent_consumer.run_forever()` now
   catches `mq_check()` exceptions after an intent is claimed and routes them
   into the existing rejection/escalation path as
   `mq_blocked:guard_error:<ExceptionType>`, so no router decision or venue
   adapter submit occurs when the guard fails. Remaining sweep:
   reconciler config reads and admin live controls.
   2026-07-12 blueprint audit follow-up: `risk_daily.snapshot()` exposes
   both gross realized PnL (`realized_pnl`) and net PnL (`pnl =
   realized_pnl - fees`), but `RiskDailyDB.realized_today_usd()` returns
   the gross field and `_executor_submit.py` feeds that value into the
   PHASE82 live risk gates. Before capped-live, choose and implement the
   intended daily-loss policy (gross vs net). At the audited revision, gross
   daily-loss evaluation permitted true net loss to exceed a configured loss
   cap by fees paid on a losing day; the audit branch documented and pinned
   that behavior but did not change live gate semantics.
   2026-07-13 halt-authority slice is proof-ready for independent review:
   `services/admin/master_read_only.py` now uses strict runtime config loading
   and fails closed on unreadable/corrupt config. Missing config remains
   not-read-only (fresh-install contract unchanged); explicit
   `safety.read_only_mode=true` remains read-only; corrupt or otherwise
   unreadable config returns read-only with `reason=config_unreadable`. This
   changes paper-engine/live-router behavior under corrupt `user.yaml` from
   proceed to refuse with `master_read_only`. Remaining sweep: live executor,
   consumer/reconciler config reads, admin live controls, and daily-loss
   gross-vs-net policy.
   2026-07-13 safety-gate slice is proof-ready for independent review:
   `services/execution/safety.py::load_gates()` now uses strict runtime
   config loading instead of treating corrupt config as `{}`. Paper-engine
   pre-submit now fails closed with `safety:safety_check_error_fail_closed:*`
   instead of proceeding with `safety_check_error_ignored` when safety gates
   raise. Live router already had the fail-closed exception path and now
   receives strict safety-gate loading through the shared function. Remaining
   sweep: live executor/consumer/reconciler config reads, admin live controls,
   and daily-loss gross-vs-net policy.
   2026-07-13 live-enable controls slice is proof-ready for independent review:
   both token-based `services/execution/live_enable.py::enable_live()` and
   admin wizard `services/admin/live_enable_wizard.py::enable_live()` now load
   `user.yaml` with `strict=True` before writing `execution.live_enabled=true`.
   Unreadable/corrupt config returns `config_load_failed` and performs no save,
   no `CBP_EXECUTION_ARMED` mutation, no persisted live-arm state write, and no
   system-guard RUNNING transition. Token ceremony ordering is otherwise
   preserved: checklist/preflight/token verification still happen before the
   strict config load. Disable paths remain intentionally outside this slice so
   operator halt behavior is not tightened accidentally. Remaining sweep: live
   executor/consumer/reconciler config reads and daily-loss gross-vs-net policy.
   2026-07-13 live risk-claim config slice is proof-ready for independent
   review: `live_risk_cfg(strict=True)` is now available, and both
   `services/execution/live_intent_consumer.py::_risk_check_and_claim()` and
   compat `services/execution/intent_consumer.py::_risk_check_and_claim()` use
   it before reading or resetting risk counters. `ConfigLoadError` returns
   `risk:config_load_failed` with no risk-state read/reset and no
   `atomic_risk_claim()` call, so corrupt `user.yaml` can no longer turn
   configured live caps into default/no-cap values before the enforcement layer
   sees them. Non-strict `live_risk_cfg()` default behavior is preserved for
   non-critical callers. Remaining sweep: live executor/reconciler config reads
   and daily-loss gross-vs-net policy.
   2026-07-13 live executor risk-gate config slice is proof-ready for
   independent review: `services/execution/_executor_submit.py` now loads
   PHASE82 live risk-gate config with `load_runtime_trading_config(strict=True)`.
   `ConfigLoadError` returns a blocked submit result
   (`LIVE blocked: config_load_failed:ConfigLoadError`, `submitted=0`,
   `safety_blocked=1`) before `LiveGateDB`, `ExecutionStore`, or
   `ExchangeClient` are constructed, so corrupt runtime config cannot fall back
   to defaults while building live gates. Remaining sweep: reconciler/compat
   sandbox config reads and daily-loss gross-vs-net policy.
   2026-07-13 reconciler/consumer sandbox config slice is proof-ready for
   independent review: `services/execution/live_reconciler.py`,
   `services/execution/live_intent_consumer.py`, and compat
   `services/execution/intent_consumer.py` now load sandbox-mode runtime config
   with `load_runtime_trading_config(strict=True)` before constructing live
   adapters. Corrupt runtime config writes an operator-visible
   `config_load_failed` blocked status and creates no adapter; the canonical
   live consumer now reads sandbox config before `claim_next_queued()`, so
   corrupt config cannot mutate queued intents to `submitting`. Stale
   submitting recovery leaves rows untouched on config-load failure. Remaining
   sweep: daily-loss gross-vs-net policy.
   2026-07-13 daily-loss policy slice is proof-ready for independent review:
   the chosen policy is fee-inclusive net PnL for capped-live daily loss.
   `RiskDailyDB.realized_today_usd()` now returns the snapshot `pnl` field
   (`realized_pnl - fees`) instead of gross `realized_pnl`, and the live
   executor's existing PHASE82 gate path continues to consume
   `realized_today_usd()`. Tests pin that a `-100.0` gross day with `5.0` fees
   evaluates as `-105.0` for daily-loss purposes. Substrate #2 config
   fail-closed sweep is now code-complete pending independent review/CI for
   this high-risk live-risk policy change.
   2026-07-15 admin live-disable runtime-halt follow-up is ready for
   independent review: `services/admin/live_disable_wizard.py::disable_live_now()`
   and `services/admin/live_enable_wizard.py::disable_live()` now treat disable
   persistence as best-effort and runtime halt as mandatory. Disable config
   reads use `strict=True`; corrupt config skips the config write instead of
   overwriting `user.yaml` as `{}`, and config read/save failure no longer
   returns before clearing execution env flags, disarming persisted live-arm
   state, arming the kill switch / setting the system guard `HALTED`, and
   returning an operator-visible `config_load_failed_runtime_halted` or
   `config_save_failed_runtime_halted` reason.
   2026-08-13: implementation slices accepted after independent review. This
   closes the review/acceptance tracking status for the fail-closed
   config and daily-loss policy slices above without changing runtime behavior;
   remaining work stays limited to separately named capped-live proof or future
   config surfaces discovered by audit.
3. Replace string-match order retry classification with typed `ccxt` exception
   handling. Ambiguous submit timeouts must verify by `clientOrderId` before any
   retry. Add a kill-between-writes submit-path test. Blocks live.
   2026-07-03 audit update: `services/execution/live_reconciler.py` already has
   a verify-before-retry path for `submit_unknown` intents through
   client-order-id lookup. Remaining work is typed exception classification,
   fault-injection proof around crash-between-writes, and explicit policy for
   the venue-lookup-not-found case. 2026-07-06: the typed-classification slice
   is ready for independent review: `services/execution/retry_policy.py`
   `is_retryable_exception()` now classifies by exception type only —
   ccxt `NetworkError` and subclasses (RequestTimeout, ExchangeNotAvailable,
   OnMaintenance, DDoSProtection, RateLimitExceeded) plus builtin
   `ConnectionError`/`TimeoutError` and an exact-type-name fallback are
   retryable; `InsufficientFunds`/`InvalidOrder`(incl. OrderNotFound)/
   `AuthenticationError`/`BadRequest`/`ArgumentsRequired`/`NotSupported`/
   `InvalidNonce` are definitive; generic `ExchangeError`/`BaseError` and all
   unknown exceptions fail closed to non-retryable (the router's
   verify-before-retry reconcile lane owns ambiguity). Message text is never
   consulted, removing the legacy hazards where an order id containing `429`
   flipped an exception retryable or venue phrasing containing `account`
   blocked a legitimate transient retry. Deliberate precedence for review:
   ccxt classes `InvalidNonce` under `NetworkError` (transient), but the
   stricter legacy non-retryable stance is preserved. 2026-07-09: the
   venue-lookup-not-found terminal policy is proof-ready for independent
   review: `submit_unknown` intents now track clean venue not-found
   observations in queue state and only transition to `error` when both
   thresholds pass (`CBP_SUBMIT_UNKNOWN_NOT_FOUND_MIN_OBS` default 3 and
   `CBP_SUBMIT_UNKNOWN_NOT_FOUND_TERMINAL_MS` default 900000ms). Lookup
   exceptions do not count, successful recovery clears the observation record,
   corrupt records restart the window, and the terminal reason includes
   observation count and age. Remaining risk: a live-but-persistently-invisible
   venue order could still be disposed after the bounded window; review the
   default window before live capital.
   2026-08-13: implementation slice accepted after independent review. This
   closes the review/acceptance tracking status for the venue-lookup-not-found
   terminal policy implementation without changing runtime behavior; the
   stated bounded-window risk remains a capped-live policy review point before
   real capital.
4. Add crash-consistency/fault-injection tests for submit, fill, reconcile, and
   restart. Kill between each side effect and assert reconciler convergence.
   This is a launch-packet companion, not a replacement for restart evidence.
   2026-07-06: implementation proof is ready for independent review:
   `tests/test_crash_consistency_fault_injection.py` (7 scenarios, real
   sqlite stores, SystemExit as the process-death mechanism so consumer
   error-recovery paths cannot soften the crash) kills inside the venue
   submit, before the dedupe mark, before the queue status write, before the
   order-store upsert, inside canonical fill accounting, and before the
   `filled` transition, plus the ambiguous-submit `submit_unknown` lane.
   Exactly-once venue submission held in every scenario, and fill accounting
   held exactly-once per fill_id at both the trading store and the canonical
   journal. Two findings from the injection runs, filed here for decision:
   (a) documented-safe stranding — a crash between the dedupe claim/venue
   submit and the queue status write leaves the intent at `submitting`
   permanently (the dedupe guard prevents resubmission and the reconciler
   does not scan `submitting`); safety holds but the intent needs operator
   attention; consider a reconciler or consumer sweep for aged `submitting`
   rows with dedupe-informed recovery; 2026-07-09: closure proof ready for
   independent review — the consumer now runs a startup
   stale-`submitting` recovery sweep (`_recover_stale_submitting`,
   threshold `CBP_SUBMITTING_STALE_RECOVERY_MS` default 120000ms,
   fail-closed env parsing) that never submits: venue-found rows converge
   to `submitted` (with an idempotent dedupe claim-then-mark so a crash
   before the original dedupe claim is also covered), venue-absent rows
   move to `submit_unknown` for the reconciler's single ambiguity lane,
   lookup errors and young rows are left untouched, and corrupted
   timestamps are treated as aged (safe: read-then-classify). The three
   fault-injection stranding pins were converted to convergence proofs; (b) convergence-by-design confirmed —
   a crash after fill accounting but before the `filled` transition
   converges on the next pass via the reconciler's 60s cursor overlap
   re-fetch (`CBP_RECONCILER_CURSOR_OVERLAP_MS`) plus INSERT OR IGNORE
   idempotence; the residual edge is a later trade advancing the cursor more
   than the overlap window past an earlier fill whose transition never
   landed — multi-fill lookback would close it. 2026-07-09: lookback closure
   proof ready for independent review — the reconciler's deferred branch now
   consults the canonical journal by (venue, order_id/client_order_id) via
   read-only `_accounted_fills_for_order` (fail-closed: any read problem
   returns 0 and keeps the deferred behavior); a closed order with zero
   re-fetched fills but existing accounted fills transitions to `filled` via
   lookback, and the fault-injection suite proves the multi-fill edge
   converges with exactly-once accounting and an honest cursor (no replay
   past the overlap window). Genuinely unaccounted closed-with-zero-trades
   anomalies still defer, unchanged.
   2026-07-13 temporal-authority closure proof is ready for independent
   review: `ExecutionStore.set_intent_status()` now enforces legal
   predecessor status inside the SQLite `UPDATE` and returns `True` only
   when the transition applies. This closes the read-check-write race where
   submit and reconcile writers could both validate against a stale status
   and the loser could overwrite a terminal state/reason. Added real-sqlite
   thread tests for exactly-one-winner, terminal resurrection refusal,
   reason preservation for refused writers, and same-status reason rewrites.
   Added a state-machine contract pin so downstream tests deriving from
   `EXECUTION_STORE_STATUS_TRANSITIONS` cannot silently follow a changed
   terminal map.
5. Ship server deployment units or retire the stale deployment story. Provide
   systemd units for collector, trader, reconciler, and dashboard, and either
   make Docker compose runnable from this repo or move it behind a documented
   companion-repo pointer. Prefer boring host infrastructure (`systemd`,
   `journald`, bounded status commands, and external dead-man checks) over
   expanding custom supervisor code unless a repo-specific need is shown.
   Blocks server shadow quality and live.
   2026-07-12: systemd deployment unit slice is ready for independent review.
   `packaging/systemd/` now includes hardened units for collector, intent
   consumer, reconciler, and dashboard, plus `cbp.env.example`. Units use
   journald logging, `Restart=on-failure`, bounded start limits in `[Unit]`,
   `NoNewPrivileges`, `ProtectSystem=strict`, and
   `ReadWritePaths=/var/lib/cbp`. Authority boundary is explicit and tested:
   unit/env files carry no `CBP_EXECUTION_ARMED` or live-enable token, and
   `scripts/install_systemd_units.py` verifies that boundary in dry-run mode
   before any install. `docs/DEPLOYMENT.md` documents host prerequisites,
   per-unit enable policy, and keeps the intent-consumer enable decision as an
   operator action. Host-side installation remains open.
   2026-08-14: read-only Hetzner inventory is recorded in
   `docs/checkpoints/host_proof_inventory_2026_08_14.md`. Hetzner checkout
   `5eb36cbb5` has `cbp-crypto-edge-collector.service` active and
   `cbp-edge-cadence.timer` active, but the broader core units
   (`cbp-collector`, `cbp-dashboard`, `cbp-dead-man`, `cbp-intent-consumer`,
   `cbp-reconciler`) were not observed as loaded/running. This is partial
   evidence only; the deployment installation proof remains open.
   2026-08-14: Hetzner systemd installer dry run is recorded in
   `docs/checkpoints/host_systemd_dry_run_2026_08_14.md`. The host checkout
   rendered and statically verified `cbp-collector`, `cbp-crypto-edge-collector`,
   `cbp-intent-consumer`, `cbp-reconciler`, `cbp-dashboard`, `cbp-dead-man`,
   `cbp-edge-cadence`, and both timers. No units were installed or restarted;
   installation/post-install evidence remains open.
   2026-08-19: Hetzner checkout sync is recorded in
   `docs/checkpoints/host_sync_backup_drill_followup_2026_08_19.md`. The host
   fast-forwarded from `5eb36cbb5` to `a10aca01f` without service restart;
   `cbp-crypto-edge-collector.service` and `cbp-edge-cadence.timer` remained
   active. The broader deployment installation/post-install proof still remains
   open.
   2026-08-21: read-only runtime check-in is recorded in
   `docs/checkpoints/host_runtime_checkin_2026_08_21.md`. Laptop paper
   campaigns are `2/2` running and idle after the 2026-08-21 daily cycle;
   Hetzner paper campaign is `1/1` running and idle; Hetzner edge runtime is
   ready on master `a10aca01f`; OKX funding/open-interest/basis cadence is
   fresh at `2026-08-21T03:08:42+00:00`. This is status evidence only; it does
   not close deployment installation/post-install, backup/restore, or launch
   proof items.
   2026-08-23: fresh read-only runtime status is recorded in
   `docs/checkpoints/runtime_check_2026_08_23.md`. Laptop paper campaigns are
   `2/2` running and idle after the 2026-08-23 daily cycle; Hetzner
   `ema_cross_default` is `1/1` running and idle; Hetzner edge runtime is ready
   on master `a10aca01f`; host OKX funding/open-interest/basis cadence is fresh
   at `2026-08-23T04:56:02+00:00`; pullback Stage 0 verification passes with
   zero blockers; funding Stage 0 remains blocked by expected-commit mismatch
   (`expected=fd7f11e9c`, `actual=1920d13b0`). This is status evidence only; it
   does not close deployment installation/post-install, backup/restore, or
   launch proof items.
   2026-08-23: fresh Hetzner systemd dry-run and loaded-unit inventory are
   recorded in `docs/checkpoints/host_systemd_dry_run_2026_08_23.md`. Host
   checkout `a10aca01` statically verifies the full packaged unit set in dry-run
   mode; currently loaded `cbp-*` units remain limited to
   `cbp-crypto-edge-collector.service`, `cbp-edge-cadence.service`, and
   `cbp-edge-cadence.timer`. No units were installed, enabled, reloaded, or
   restarted; deployment installation/post-install proof remains open.
   2026-08-24: read-only runtime check-in is recorded in
   `docs/checkpoints/runtime_check_2026_08_24.md`. PR #529 is merged on
   `master` (`db8bd11d3`), local paper campaigns are `2/2` running and idle
   after the 2026-08-24 daily cycle, the local paper gate remains `3/5`
   qualified round trips with `2` remaining and qualified bars complete at
   `63/60`, roadmap tracking is clean, the passive local operator queue is
   empty, Hetzner `ema_cross_default` is `1/1` running and idle after the
   2026-08-24 daily cycle, and the merged Hetzner crypto-edge runtime wrapper
   reports `hetzner_crypto_edge_runtime_ready` with zero blockers against remote
   `master` at `a10aca01f`. This is status evidence only; it does not close
   deployment installation/post-install, host dependency alignment,
   backup/restore, or launch proof items.
   2026-08-24: Docker-compose disposition proof is recorded in
   `docs/checkpoints/docker_compose_disposition_2026_08_24.md`. Default Compose
   config renders only `dashboard`; `COMPOSE_PROFILES=phase1-companion` renders
   `dashboard` plus `backend`; and `tests/test_companion_repo_dependency.py`
   passes. This closes the Docker companion-disposition slice. Server
   deployment installation/post-install evidence remains open under the
   existing proof marker above.
6. Add trading-loop metrics and dead-man alerting. Host health checks are not
   enough; each managed trading loop needs heartbeat metrics and alert-on-absence
   within a defined time window. Include a watchdog proof that each loop checks
   kill/stop signals within a bounded interval and a synthetic alert-delivery
   test so dead email/Slack credentials are detected. Prefer a simple external
   dead-man and push channel such as healthchecks-style pings plus ntfy,
   Telegram, or another operator-visible channel before writing more custom
   alert infrastructure. A 2026-07-03 audit found
   `services/process/heartbeat.py::write_heartbeat()` has no callers while
   `services/process/watchdog.py` reads heartbeat state and can arm the kill
   switch / set `HALTING` on staleness. Add heartbeat writes in every managed
   loop that matters for unattended operation: strategy runner, evidence
   service, collectors, live intent consumer, and reconciler. Also wire alert
   dispatch on watchdog trigger and `bot_not_running`, prove host scheduling,
   and fold the status-only `services/admin/watchdog.py` surface into the
   process watchdog or document why both remain. Blocks shadow/live quality.
   2026-07-10: the heartbeat/dead-man slice is ready for independent review,
   built by extending the audited-existing module rather than twinning it:
   `services/process/heartbeat.py` gains named per-loop beats
   (`write_named_heartbeat` — atomic tmp+rename, sequenced, rate-limited via
   `CBP_HEARTBEAT_MIN_INTERVAL_S` default 5.0s, and never-raising so a
   heartbeat cannot break a trading loop) while the legacy single-file
   bot-runner path stays byte-identical for the watchdog/crash-snapshot
   readers (pinned by test). Both live loops now beat every iteration.
   External dead-man: `scripts/check_dead_man.py` (exit 0 ok / 1 stale /
   2 missing; empty heartbeat-name configuration also fails closed as
   missing; `CBP_DEAD_MAN_MAX_AGE_S` default 180s; `--json`; `--alert`
   dispatches best-effort through the existing alert stack) driven by
   `packaging/systemd/cbp-dead-man.timer` every 60s. The systemd oneshot
   pins `CBP_STATE_DIR=/var/lib/cbp` and uses `StateDirectory=cbp` so the
   hardened service has a writable state root. Item-mandated proofs
   included: loops honor the stop signal within one iteration of the
   request, and synthetic alert delivery lands the local fallback with no
   configured channels. Boundaries: the watchdog's auto-stop wiring for
   named beats and per-loop watchdog policy remain follow-ups (the item
   prefers the external dead-man first); healthchecks/ntfy push channels
   remain operator choices layered on the checker's exit codes.
   2026-08-23: host dead-man status is recorded in
   `docs/checkpoints/host_systemd_dry_run_2026_08_23.md`. The checker and
   packaged `cbp-dead-man` service/timer files are present on Hetzner, and the
   checker fails closed with `overall=missing` under `CBP_STATE_DIR=/var/lib/cbp`
   for the packaged default heartbeat names (`intent_consumer`,
   `live_reconciler`) and explicit edge names (`crypto_edge_collector`,
   `edge_cadence`). The `cbp-dead-man` service/timer is not currently loaded;
   heartbeat production/scheduling proof remains open.
7. Write a state-store consolidation decision record before implementation.
   Decide how fills, positions, PnL, intents, and ledgers should move toward one
   transactional schema or explicitly accept the current reconciler-dependent
   multi-store risk. Blocks live. 2026-07-04: decision record is written in
   `docs/architecture/state_store_consolidation_decision.md`. It freezes current
   store ownership during the paper campaign, names current accounting/evidence
   authorities, sets the long-term transactional boundary target, and explicitly
   accepts the current multi-store design for paper/research only. Remaining
   capped-live work: caller/migration audit for unwired stores, crash-consistency
   tests, backup/restore drill, and either transactional migration proof or an
   explicit accepted split-store risk decision.
   2026-07-22: executable state-store consolidation decision guard is ready
   for independent review. `tests/test_state_store_consolidation_decision_guard.py`
   pins the no-migration boundary, current store authorities, long-term
   transactional target, implementation consequences, capped-live accepted-risk
   boundary, and follow-up requirements. This is docs/test only and does not
   change storage schemas, migrations, runtime stores, or execution behavior.
   2026-07-13: position-truth resolution authority decision record is written
   in `docs/decisions/position_truth_resolution_authority.md`. It separates
   order truth (`_executor_reconcile`: what happened to an order) from
   position truth (what the venue says we actually hold), pins that
   `services/reconciliation/exchange_reconciler.py` is currently dormant with
   zero production importers, and records the capped-live stage gate:
   scheduled position reconciliation must exist, with a defined resolution
   authority, trust policy/hysteresis, and `CRITICAL` drift bound to a named
   halt authority before capped-live exposure.
8. Add a full-state backup/restore drill to the launch evidence packet. Script
   backup of all state DBs and record one executed restore-and-resume rehearsal.
   Blocks live. 2026-07-04: drill policy is documented in
   `docs/FULL_STATE_BACKUP_RESTORE_DRILL.md` and linked from the launch
   checklist. Remaining proof: execute the drill against the future capped-live
   state bundle, record manifests/hashes, prove read-only restored status,
   prove idempotent paper/sandbox resume, and scan the backup for secrets.
   2026-07-10: the durable data-state tooling half is ready for independent review —
   `scripts/backup_state.py` backup/verify/restore with drill-grade
   guarantees proven by `tests/test_state_backup_restore.py`: sqlite
   backup-API snapshots pass integrity_check under an active concurrent
   writer (the property plain file copies lack) while excluding SQLite
   sidecars (`-wal`, `-shm`, `-journal`) from the manifest; checksummed
   manifest detects tamper, missing files, and invalid relative paths;
   restore fail-closed guard order is verify-completely-first, refuse on
   any *.lock (live writers), require --force on a non-empty target and
   then move the old data aside (data.pre-restore-<stamp>, never
   deleted), restore only manifest-listed files, and re-checksum
   everything post-restore; round trip recovers exactly backup-time state.
   `docs/FULL_STATE_BACKUP_RESTORE_DRILL.md` gained a Tooling section
   mapping the tool to procedure steps 3-5; runtime/config/snapshot
   families outside `data_dir()`, the secrets scan, and
   resume/idempotence proofs stay drill-time operator steps by design.
   Remaining: execute the drill on the host and file the evidence.
   2026-08-14: Hetzner inventory confirms `scripts/backup_state.py` is
   present on the Hetzner checkout and exposes `backup`, `verify`, and
   `restore` subcommands. No backup or restore was executed; the drill remains
   open.
   2026-08-14: a read-only/scratch Hetzner drill attempt is recorded in
   `docs/checkpoints/host_backup_restore_drill_blocker_2026_08_14.md` and is
   blocked, not passed. The host checkout is still `5eb36cbb5`, which lacks
   `scripts/check_backup_artifact_secrets.py`; `/var/lib/cbp/data` is owned by
   `cbp:cbp`; the current `cryptkeep` Tailscale login cannot run
   `sudo -n -u cbp`; and `backup_state.py backup` against
   `CBP_STATE_DIR=/var/lib/cbp` failed during SQLite snapshot with
   `sqlite3.OperationalError: attempt to write a readonly database`. Remaining
   proof: sync the host checkout to an approved current master, run the drill
   with effective access to the `cbp` state data, verify the manifest, restore
   into scratch state, run the backup-artifact secret scan, and then record the
   checkpoint.
   2026-08-14: backup tooling follow-up is ready for review. `create_backup()`
   now converts SQLite snapshot and file-copy exceptions into structured JSON
   failures (`snapshot_failed:<rel>:<Exception>` /
   `copy_failed:<rel>:<Exception>`) instead of letting tracebacks escape before
   operator-event recording. This does not execute or close the host drill; it
   makes the next host attempt machine-readable when a source file cannot be
   snapshotted or copied.
   2026-08-19: host follow-up is recorded in
   `docs/checkpoints/host_sync_backup_drill_followup_2026_08_19.md`. The host
   is now at `a10aca01f` and contains both `scripts/backup_state.py` and
   `scripts/check_backup_artifact_secrets.py`; edge cadence and Hetzner paper
   status are healthy after sync. The drill remains blocked because running
   `backup_state.py backup` as `cryptkeep` against `CBP_STATE_DIR=/var/lib/cbp`
   returns structured failure
   `snapshot_failed:market_raw.sqlite:OperationalError` with
   `attempt to write a readonly database`, and operator-event recording returns
   `operator_event_write_failed:OperatorEventJournalError`. Remaining proof:
   rerun backup/verify/scratch-restore/backup-secret-scan with effective access
   to the `cbp` state data and operator-event journal.
   2026-08-27: backup snapshot source-access fix is ready for independent
   review. `scripts/backup_state.py::_snapshot_sqlite()` now opens source
   databases with SQLite URI `mode=ro` before invoking the backup API, matching
   the host blocker where `cryptkeep` could read but not write `cbp`-owned
   SQLite files. A regression test pins the read-only source connection. This
   does not execute or close the host drill; remaining proof is to sync the
   accepted patch to Hetzner and rerun backup/verify/scratch-restore plus the
   backup-artifact secret scan against `/var/lib/cbp`.
   2026-07-22: executable full-state restore-drill contract guard is ready for
   review. `tests/test_full_state_restore_drill_contract.py` pins that
   `docs/FULL_STATE_BACKUP_RESTORE_DRILL.md` does not claim an executed host
   drill, preserves required state-family coverage, documents
   `backup_state.py` tooling guarantees, keeps secrets scan and
   resume/idempotence as drill-time steps, preserves pass criteria, and links
   the capped-live gate to `docs/LAUNCH_CHECKLIST.md`. This is docs/test only
   and does not run backup/restore, mutate state, change tooling, or close the
   required host drill evidence.
9. Surface evidence-write failures in session status. If signal/fill evidence
   writes fail repeatedly while a campaign keeps running, operators should see a
   failure counter and the session should refuse after a bounded threshold
   rather than silently starving the promotion gate. 2026-07-04: status policy
   is documented in `docs/EVIDENCE_WRITE_FAILURE_STATUS_POLICY.md`. 2026-07-04:
   implementation proof is accepted: the central
   `EvidenceLogger` persists `runtime/health/evidence_writer.status.json` with
   total/consecutive failures, last error/success timestamps, and
   `ok`/`degraded`/`refusing` status; targeted tests prove repeated injected
   write failures become `refusing` and recovery resets consecutive failures.
   2026-07-04: gate/status integration proof is accepted:
   `check_promotion_gates.py` now includes
   `evidence_writer` status, adds an `Evidence writer accepting records` gate,
   fails that gate when persisted status is `refusing`, and supervised soak
   status surfaces the writer and recommends `investigate_evidence_writer`.
   Remaining: any future alert-dispatch hook belongs under paper/gate event
   alerting. 2026-07-10: that hook is implemented in the paper/gate event
   alerting slice (Active #23) — evidence-writer status transitions now
   dispatch through the alert stack, notification-only and never-raise.
10. Consolidate config authority before live expansion. The repo still has
    legacy/default `config/` surfaces, strategy/campaign `configs/` surfaces,
    and compatibility normalization between `live.enabled` and
    `execution.live_enabled`. Decide the canonical schema, migrate readers, and
    retire or document compatibility shims so the most dangerous live flag has
    one authority. 2026-07-04: policy is documented in
    `docs/CONFIG_AUTHORITY_DECISION.md`. Remaining capped-live proof:
    live/risk/dashboard/preflight/executor reader inventory, corrupt-config
    fail-closed tests for trading-critical readers, one startup from the
    documented config bundle, and accepted rationale for any remaining
    compatibility shims.
    2026-07-22: executable config-authority decision guard is ready for
    independent review. `tests/test_config_authority_decision_guard.py` pins
    canonical live-enable rules, strategy/campaign config rules, compatibility
    policy, capped-live proof requirements, and launch-checklist link. This is
    docs/test only and does not change config parsing, config files, startup,
    or runtime behavior.
11. Add clock/venue-time sanity checks before capped live. Funding age,
    candle boundaries, order timestamps, and reconciliation windows assume UTC
    clock correctness. Add a host/venue skew check and operator-visible status
    before relying on timestamp-sensitive shadow/live evidence. 2026-07-04:
    policy is documented in `docs/CLOCK_VENUE_TIME_SANITY_POLICY.md`.
    2026-08-13 host proof recorded in
    `docs/checkpoints/clock_venue_time_host_proof_2026_08_13.md`: Hetzner
    `host_utc=2026-08-13T23:56:27.797371+00:00`, `ntp_status=timedatectl: yes`,
    `threshold_ms=5000`, Coinbase `status=OK skew_ms=-409 rtt_ms=190`, and OKX
    `status=OK skew_ms=42 rtt_ms=326`. This closes the host/venue-time evidence
    refresh for the checked venues at that timestamp; future launch packets
    should refresh the proof close to any shadow/capped-live transition.
    2026-07-10: the
    implementation slice is ready for independent review —
    `services/execution/clock_sanity.py` measures venue skew against the
    round-trip midpoint (`measure_venue_skew`, rtt recorded as measurement
    quality) and gates the live consumer per intent via `check_venue_clock`:
    an affirmative measured skew beyond `CBP_MAX_CLOCK_SKEW_MS` (default
    5000ms, fail-closed parsed) rejects the intent with
    `clock_skew_blocked:*` mirroring the market-quality block pattern; OK
    results are cached for `CBP_CLOCK_SKEW_CHECK_INTERVAL_S` (default 300s)
    while exceeded/failed measurements are never cached so blips clear in
    about one loop. Deliberate v1 boundaries flagged for review: venues
    without a server-time endpoint are a recorded limitation and never
    block, and measurement errors never block — only affirmative excess
    does. Operator-visible status: consumer status notes plus
    `scripts/check_clock_sanity.py` (host UTC, best-effort NTP status,
    per-venue skew, verdict; exit codes 0/1/2) as the launch-evidence
    artifact tool. Host-side NTP enforcement remains an operator/server
    task per `docs/CLOCK_VENUE_TIME_SANITY_POLICY.md`.
    2026-07-22: executable clock/venue-time policy guard is ready for
    independent review. `tests/test_clock_venue_time_policy_guard.py` pins
    timestamp-sensitive evidence scope, required shadow cost-evidence checks,
    capped-live launch-packet checks, and launch-checklist linkage. This is
    docs/test only and does not change clock checking, live gating, status
    output, or runtime behavior.
12. Define the server secrets and rotation model before capped live. Current
    keyring/env handling is adequate for desktop/paper, but server operation
    needs a documented injection path, rotation procedure, and proof that
    secrets are not written to deployment records, logs, or evidence artifacts.
    2026-07-04: policy is documented in
    `docs/SERVER_SECRETS_ROTATION_MODEL.md` and linked from the launch
    checklist/authority matrix. Remaining capped-live proof: execute a server
    injection and rotation drill, verify redacted status/preflight output,
    confirm old credential revocation, and scan deployment/evidence artifacts
    for secret leakage.
13. Add supply-chain verification to release/CI policy. Requirements are
    pinned, but hash pinning and dependency-audit evidence are not yet a
    visible release gate. Decide whether to add `pip-audit`/hash checks or
    explicitly accept the risk for paper-only operation. 2026-07-04: policy is
    documented in `docs/SUPPLY_CHAIN_RELEASE_POLICY.md` and linked from CI and
    launch docs. Remaining capped-live proof: run or explicitly waive a
    dependency vulnerability audit, record artifact hashes/provenance for the
    deployed SHA, and decide whether hash-locked installs or SBOMs become
    release gates.
    2026-07-12: supply-chain verification tooling is ready for independent
    review. `scripts/check_supply_chain.py` verifies exact-pin integrity,
    installed environment drift against pinned requirements, optional
    best-effort `pip-audit`, and `--evidence-dest` provenance JSON containing
    Git SHA, dirty flag, requirement-file hashes, and verdicts. The policy doc
    is updated; hash-locked installs, SBOMs, and CI-gate decisions remain
    operator decisions.
    2026-07-22: executable supply-chain release-policy guard is ready for
    independent review. `tests/test_supply_chain_release_policy_guard.py` pins
    the current paper/research boundary, capped-live launch-packet
    requirements, accepted waiver fields, future gate options, and launch/CI
    policy links. This is docs/test only and does not change CI, dependency
    installation, release workflows, or branch protection.
    2026-08-14: local `pip-audit` vulnerability evidence is now recorded at
    `.cbp_state/data/supply_chain/supply-chain-evidence-20260814T000731Z.json`.
    Pin integrity and installed pinned-environment checks passed for commit
    `9daac50a305c3b5f0f0c8c01616acefe0c1d87c4`; the vulnerability audit ran
    and reported `vulnerable_count=10` across pinned packages. Remaining
    capped-live proof is no longer "run the audit" for this local artifact; it
    is review/remediate or explicitly waive the recorded findings, decide
    whether hash-locked installs or SBOMs become release gates, and repeat the
    audit for the final deployed SHA.
    2026-08-14: supply-chain vulnerability remediation branch updates the
    vulnerable pinned packages found by local `pip-audit`: `aiohttp` 3.14.3,
    `click` 8.3.3, `cryptography` 50.0.0, `GitPython` 3.1.58, `idna` 3.15,
    `pillow` 12.3.0, `starlette` 1.3.1, `tornado` 6.5.7, and `urllib3` 2.7.0;
    it also explicitly pins `setuptools` 83.0.0 because the audit found the
    installed version vulnerable even though it was not previously listed in
    the pinned requirement files. Local `scripts/check_supply_chain.py --audit`
    reports pin integrity OK, environment OK, and `vulnerable_count=0` on the
    modified working tree. Remaining capped-live proof after merge is to repeat
    the audit for the final deployed SHA and decide whether hash-locked installs
    or SBOMs become release gates.
    2026-08-14: post-merge local supply-chain audit is recorded in
    `docs/checkpoints/supply_chain_post_merge_audit_2026_08_14.md` for master
    commit `77a3a5294`: git state was clean, pin integrity OK, installed
    environment OK, audit ran, and `vulnerable_count=0`. Remaining capped-live
    release-policy decision: whether SBOM and hash-locked install evidence are
    required for future deployed SHAs.
    2026-08-23: updated supply-chain status is recorded in
    `docs/checkpoints/supply_chain_status_2026_08_23.md`. Local checkout
    `cc6c69f` has pin integrity OK and environment OK, but `pip-audit` reports
    one vulnerability in `pip 26.1.2` (`PYSEC-2026-3721` /
    `CVE-2026-13346`, fixed in `pip 26.2`). Hetzner checkout `a10aca01f` has
    pin integrity OK but environment mismatch against current pins for 10
    packages (`aiohttp`, `click`, `cryptography`, `gitpython`, `idna`,
    `pillow`, `setuptools`, `starlette`, `tornado`, `urllib3`). Host
    vulnerability audit was not run because it may disclose host package
    inventory externally and needs explicit operator approval or waiver.
    Later 2026-08-28/2026-08-29 follow-ups closed the local `pip` remediation
    and deployed-environment pin alignment pieces. Remaining capped-live
    release-policy proof is to run or waive host vulnerability audit for the
    final deployed SHA and decide whether hash-locked installs or SBOMs become
    release gates.
    2026-08-23: local `pip` remediation is recorded in
    `docs/checkpoints/supply_chain_local_remediation_2026_08_23.md`.
    The project virtualenv was upgraded from `pip 26.1.2` to `pip 26.2`;
    subsequent local `scripts/check_supply_chain.py --audit --json` on
    `a4a555d` reports pin integrity OK, environment OK, and
    `vulnerable_count=0`. Audited evidence artifact:
    `.cbp_state/data/supply_chain/supply-chain-evidence-20260824T011230Z.json`.
    Later 2026-08-28/2026-08-29 follow-ups closed the deployed Hetzner
    environment pin alignment piece. Remaining capped-live release-policy proof
    is to run or waive host vulnerability audit for the final deployed SHA and
    decide whether hash-locked installs or SBOMs become release gates.
    2026-08-31: local supply-chain evidence was recorded for clean master
    commit `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`. SHOWN:
    `make check-supply-chain-json` reported pin integrity OK, installed
    environment OK, 83 checked pins, no mismatches, no missing packages, and
    `vulnerability_audit.ran=false` with reason `not_requested`.
    `make record-supply-chain` wrote
    `.cbp_state/data/supply_chain/supply-chain-evidence-20260831T053704Z.json`.
    Checkpoint:
    `docs/checkpoints/supply_chain_local_evidence_2026_08_31.md`. This narrows
    local latest-SHA evidence only; host vulnerability audit/waiver,
    SBOM policy, and hash-locked install policy remain open capped-live
    release decisions.
    2026-08-31 follow-up: Hetzner checkout drift was corrected by a
    no-restart fast-forward-only sync from
    `d3b46e3c2f0541c20897f78739ce071c637d9647` to current master
    `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`. SHOWN: remote status is clean
    `master...origin/master`; dependency alignment is ready with no blockers,
    pin integrity OK, environment OK, and pip dry-run no changes; crypto-edge
    runtime is ready; Hetzner paper host is healthy; `ema_cross_default` remains
    `1/1` running and idle `waiting_for_next_day`. Checkpoint:
    `docs/checkpoints/hetzner_checkout_sync_2026_08_31.md`. This does not close
    host vulnerability audit/waiver, SBOM policy, hash-locked install policy,
    or capped-live launch packet proof.
    2026-08-31 follow-up: full-state backup artifact secret scanning produced
    six false-positive `sensitive_key_unredacted` findings for the explicit
    sentinel value `"none"` under `capital_authority`. The scanner now treats
    `"none"` as a safely redacted sentinel while leaving sensitive-key
    classification and byte-pattern scanning unchanged. SHOWN: the real backup
    artifact scan now reports `ok=true`, `finding_count=0`, `files_scanned=664`.
    Checkpoint:
    `docs/checkpoints/backup_artifact_secret_scan_false_positive_2026_08_31.md`.
    Acceptance state: `READY_FOR_INDEPENDENT_REVIEW` because security-sensitive
    scanner behavior changed.
    2026-08-31 host audit attempt: approved out-of-sandbox read-only
    `scripts/check_supply_chain.py --audit --json` on Hetzner reported
    pin integrity OK, environment OK, `83` checked packages, no mismatches,
    and no missing packages at host SHA
    `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`; vulnerability audit remained
    open with `vulnerability_audit.ran=false`,
    `reason=pip_audit_unavailable`. Checkpoint:
    `docs/checkpoints/hetzner_supply_chain_audit_attempt_2026_08_31.md`.
    Remaining capped-live release-policy proof is still to install/enable
    host `pip-audit` and rerun, or explicitly waive the vulnerability audit,
    plus decide SBOM/hash-lock requirements.
    2026-08-24: Hetzner dependency alignment runbook is recorded in
    `docs/checkpoints/hetzner_dependency_alignment_runbook_2026_08_24.md`.
    A read-only host `pip install --dry-run -r requirements-pinned.txt` exited
    `0` and showed the same 10 package updates would be installed
    (`aiohttp`, `click`, `cryptography`, `GitPython`, `idna`, `pillow`,
    `setuptools`, `starlette`, `tornado`, `urllib3`), with host `pip` also
    upgradeable from `26.1.2` to the locally remediated `26.2`. The runbook
    records the no-restart maintenance boundary, pre-change `pip freeze`
    rollback artifact, post-change supply-chain verification, and the exact
    operator approval text required before mutating the host virtualenv.
    2026-08-24: read-only host refresh is recorded in
    `docs/checkpoints/hetzner_readonly_status_2026_08_24.md`. Hetzner
    crypto-edge runtime remains ready (`blocking_checks=0`), Hetzner
    `ema_cross_default` paper remains `1/1` running and idle, and the
    supply-chain check still reports the same 10 dependency mismatches with
    pin integrity OK and vulnerability audit not requested. This refresh did
    not mutate the host; Hetzner dependency alignment, host audit/waiver, and
    SBOM/hash-lock release-policy decisions remain open.
    2026-08-25: no-restart Hetzner checkout sync recorded in
    `docs/checkpoints/hetzner_checkout_sync_2026_08_25.md`.
    `/srv/cryptkeep/app` fast-forwarded from `a10aca01` to current master
    `eb2749a28`; post-sync paper campaign status remained `1/1` running and
    crypto-edge runtime remained ready with `blocking_checks=0`. Dependency
    alignment remains open: read-only dry-run still reports the same 10 pinned
    package updates would be installed, and the host virtualenv was not
    modified without the explicit runbook approval.
    2026-08-25 follow-up: the same checkpoint records a second no-restart
    fast-forward after docs/checkpoint PRs moved master to `6c0903d31`.
    Hetzner `/srv/cryptkeep/app` fast-forwarded from `eb2749a28` to
    `6c0903d31`; post-sync paper campaign status remained `1/1` running,
    crypto-edge runtime returned ready with `blocking_checks=0`, and direct
    edge cadence remained fresh. Dependency alignment remains blocked only by
    the same 10 virtualenv package mismatches; no package install was run.
    2026-08-25: read-only host refresh is recorded in
    `docs/checkpoints/hetzner_readonly_status_2026_08_25.md`. Hetzner
    `ema_cross_default` remains `1/1` running and idle after recording
    2026-08-25 session evidence, crypto-edge runtime remains ready, and
    edge cadence reports fresh `funding`, `open_interest`, and `basis`
    snapshots. Supply-chain pin integrity remains OK, but the same 10
    dependency mismatches remain; no host package install or vulnerability
    audit was run.
    2026-08-28: read-only host refresh is recorded in
    `docs/checkpoints/hetzner_laptop_readonly_status_2026_08_28.md`. Hetzner
    `ema_cross_default` remains `1/1` running and idle after recording
    2026-08-28 session evidence; crypto-edge runtime remains ready with
    `blocking_checks=0`; dependency alignment remains open because the host
    checkout is behind current master and the same 10 pinned-package mismatches
    remain. No host package install, deploy, or service restart was run.
    2026-08-28 follow-up: the approved no-restart dependency-alignment runbook
    was executed and recorded in
    `docs/checkpoints/hetzner_dependency_alignment_proof_2026_08_28.md`.
    Host `pip` was upgraded to `26.2`, the 10 pinned-package mismatches were
    installed, and post-change supply-chain JSON reported pin integrity OK and
    environment OK with no mismatches or missing packages. The post-change
    dependency status was still blocked only by host checkout drift
    (`6c0903d318756d27eb6414a01abbfc8c8e879ae5` behind current master);
    no deploy or service restart was run. The 2026-08-29 checkout-sync
    follow-up closed that drift; remaining capped-live release-policy proof is
    to run or waive host vulnerability audit and decide SBOM/hash-lock
    requirements.
    2026-08-29 follow-up: no-restart checkout sync is recorded in
    `docs/checkpoints/hetzner_checkout_sync_2026_08_29.md`. Hetzner
    `/srv/cryptkeep/app` fast-forwarded to
    `0018c1213214f74033a70c59949e9ed86e3cfbad`; post-sync dependency status
    returned `hetzner_dependency_alignment_ready` with environment aligned,
    `mismatches=[]`, and `pip_dry_run.status=no_changes`; crypto-edge runtime
    remained ready; Hetzner paper campaign remained `1/1` running; and
    `check-hetzner-paper-host-health` returned `hetzner_paper_host_healthy`.
    Remaining capped-live proof: run or waive host vulnerability audit and
    decide SBOM/hash-lock release-policy requirements.
14. Audit operator/action event coverage. Event stores, journals, and fill
    logs exist, but it is not yet shown that every material operator action
    and state transition has a who/what/when trail sufficient for live
    incident review. 2026-07-04: coverage policy is documented in
    `docs/OPERATOR_ACTION_AUDIT_COVERAGE.md`. Remaining capped-live proof:
    dashboard/CLI/system/automation coverage matrix, audit-log replay of at
    least one live-arm-to-halt drill, no-secret audit payload scan, and
    fail-closed behavior for critical audit-write failures.
    2026-08-23: current Hetzner operator-event journal status is recorded in
    `docs/checkpoints/host_operator_event_status_2026_08_23.md`. Host
    no-required-events secret scan reports no findings but also
    `exists=false` and `event_count=0`; `--require-events` fails with
    `operator_event_journal_missing`; arm-to-halt replay also fails with
    `operator_event_journal_missing`. This is useful negative evidence only:
    host-side no-secret launch proof and arm-to-halt replay remain open until
    real operator-event records exist.
    2026-08-25: read-only host refresh is recorded in
    `docs/checkpoints/hetzner_readonly_status_2026_08_25.md`. The same
    operator-event status remains: required event scan and arm-to-halt replay
    fail with `operator_event_journal_missing` because the journal is absent
    under the current paper-only host posture. Platform event checks are clean
    for an empty/missing journal (`event_count=0`, no secret findings), but do
    not close action-specific platform event payload proofs.
    2026-08-26: read-only host refresh is recorded in
    `docs/checkpoints/hetzner_readonly_status_2026_08_26.md`. Hetzner paper and
    crypto-edge runtime remain healthy; dependency alignment remains open
    pending the explicit runbook approval; baseline operator/platform no-secret
    checks are clean for empty/missing journals; action-specific AI and
    capped-live event proofs remain open until real host events exist.
    2026-07-12: executable audit-coverage matrix tooling is ready for
    independent review. `scripts/audit_coverage_matrix.py` classifies policy
    families as SHOWN/PARTIAL/MISSING with store pointers and runtime probes,
    supports JSON/Markdown/evidence output, and `--strict` fails unless all
    families are SHOWN. Current honest verdict remains intentionally not-green:
    the matrix shows no dedicated unified append-only operator event journal
    yet, so replay drill, no-secret scan, and audit-write fail-closed behavior
    remain open.
    2026-07-15: operator-event journal substrate is ready for independent
    review. `services.audit.operator_event_journal` provides an append-only
    JSONL store under `data/operator_events/operator_events.jsonl` with the
    required who/what/when fields, explicit write failures, and redaction for
    secret-like payload keys; `scripts/record_operator_event.py` can append
    manual drill events; and `scripts/audit_coverage_matrix.py` now probes the
    substrate as `substrate_available_unhooked`. The matrix remains not-green:
    material action families are not hooked to this journal yet, so the
    remaining capped-live proof is still action hooks, arm-to-halt replay,
    no-secret scan over real events, and fail-closed audit-write policy for
    critical live actions.
    2026-07-16: audit-matrix journal-status honesty correction is ready for
    independent review. The shared operator-event journal is no longer
    unhooked; multiple material families now have partial hooks. The matrix
    now reports the substrate status as `substrate_available_partial_hooks`
    while keeping all action-family rows `PARTIAL` until host proofs and
    remaining hooks close.
    2026-07-15: operator-event no-secret scan tooling is ready for independent
    review. `scripts/check_operator_event_secrets.py` scans the operator event
    JSONL journal for unredacted secret-like payload fields, reports only
    field paths plus value type/length (never the leaked value), supports
    `--require-events` for launch-packet posture, and writes evidence JSON via
    `--evidence-dest`. Remaining capped-live proof: run it against the real
    launch-packet journal after action hooks and the arm-to-halt drill produce
    events; hook critical action families; define fail-closed behavior for
    critical audit-write failures.
    2026-07-15: live-disable/halt operator-event hook is ready for
    independent review. `services.admin.live_disable_wizard.disable_live_now`
    and `services.admin.live_enable_wizard.disable_live` append best-effort
    `live_disable` events through the unified journal after safety-increasing
    disable/kill-switch/system-guard mutations, and surface audit-write
    failures in the returned payload without blocking the halt path. Remaining
    capped-live proof: live-enable/resume hooks and policy, arm-to-halt replay
    from real audit records, host-side no-secret scan, and fail-closed
    audit-write policy for enabling/risk-increasing critical actions.
    2026-07-15: arm-to-halt replay tooling is ready for independent review.
    `scripts/check_operator_arm_to_halt_replay.py` replays operator-event
    journal records and passes only when a `live_enable`/`live_resume` event
    for `live_trading` is followed by a `live_disable`/`live_halt` event with
    halted/kill-switch evidence; it writes launch-packet JSON via
    `--evidence-dest`. This does not close the proof by itself: current
    enable/resume paths are not hooked to the journal, so a real host-side
    replay will report `missing_live_arm_event` until the risk-increasing
    action policy and hooks are implemented.
    2026-07-15: live-enable/resume audit fail-closed slice is ready for
    independent review. `services.execution.live_enable.enable_live`,
    `services.admin.live_enable_wizard.enable_live`, and
    `services.admin.resume_gate.resume_if_safe` now append required
    `live_enable`/`live_resume` operator events for risk-increasing live
    transitions. If the operator-event write fails, these paths roll back the
    live-enabled config/armed state/system guard/kill-switch/env state they
    mutated where applicable and return
    `operator_event_write_failed_live_*_rolled_back` instead of reporting a
    successful enable/resume. Remaining capped-live proof: real host-side
    arm-to-halt replay using the unified journal, no-secret scan over the
    launch-packet journal, and hooks/classification for the other material
    operator-action families.
    2026-07-15: manual safe-reconciliation audit hook is ready for
    independent review. `services.admin.reconcile_safe_steps.run_all_safe_steps`
    now appends a best-effort `manual_reconcile` operator event containing the
    requested venue/symbols/mode and read-only journal/position reconciliation
    step outcomes. This narrows the manual-reconciliation family but does not
    classify deeper one-off reconcile scripts or any future mutating override
    path.
    2026-07-16: direct position-drift flag audit hook is ready for independent
    review. `scripts/reconcile_positions.py` now appends a best-effort
    `manual_reconcile` / `position_drift_flag` operator event after writing
    `risk_sink_failed.flag`. Because the flag is safety-increasing, operator
    event failure is surfaced to stderr but does not block the flag write.
    This narrows the direct drift-reconcile script gap; deeper one-off
    reconcile scripts and future mutating override paths remain unclassified.
    2026-07-16: first-run guided setup patch/risk-preset save fail-closed slice is
    ready for independent review. `services.admin.first_run_wizard`
    `guided_setup_apply()` and `guided_setup_apply_preset()` now inspect the
    central audited `save_user_yaml()` result and return `config_save_failed`
    before review/preflight if the save fails or rolls back. The
    `services.admin.first_run_wizard.guided_setup_apply_state()` and
    `services.app.preflight_wizard` bridges preserve that failure
    instead of refreshing over it. Direct file edits, env live-risk caps, and
    non-user.yaml risk changes remain unclassified.
    2026-07-15: dashboard alert-settings audit hook is ready for independent
    review. `dashboard.services.views.settings_view.update_settings_view` now
    treats `dashboard_ui.settings.notifications` changes as material alert
    routing changes: after the local config save and before API sync it appends
    a required `alert_routing_change` operator event, and if that audit write
    fails it rolls the local config save back and skips API sync with
    `operator_event_write_failed_alert_routing_rolled_back`. The coverage
    matrix moves this family from MISSING to PARTIAL; CLI/runtime config edits
    and dispatcher/env channel changes remain unclassified.
    2026-07-15: dashboard risk-limit audit hook is ready for independent
    review. `dashboard.services.views.settings_view.update_settings_view` now
    treats dashboard Settings paper-trading risk-limit changes as material
    `risk_limit_change` events: after local config save and before API sync it
    appends a required operator event, and if that audit write fails it rolls
    the local config save back and skips API sync with
    `operator_event_write_failed_risk_limit_rolled_back`. The coverage matrix
    moves the risk-limit family from MISSING to PARTIAL; direct CLI/runtime
    config edits, environment live-risk caps, and non-dashboard risk changes
    remain unclassified.
    2026-07-16: backup/restore operator-event hook is ready for independent
    review. `scripts/backup_state.py` now appends best-effort unified operator
    events for `backup`, `verify`, blocked `restore`, and successful `restore`
    command results while preserving its existing JSON verdicts and exit-code
    contracts. This narrows the backup/restore family but does not close it:
    restore audit-write fail-closed policy remains open because the unified
    journal is stored under the data directory that restore replaces, and
    migrations/rollbacks beyond git/work-log evidence remain unclassified.
    2026-07-16: audit matrix intent-history runtime honesty slice is ready for
    independent review. `scripts/audit_coverage_matrix.py` now separates
    source-declared `live_trade_intent_events` support from the current runtime
    SQLite store actually having that table. An old/unmigrated
    `live_intent_queue.sqlite` no longer gets `history(per-transition runtime
    table)` in `fields_present`; it reports
    `history(runtime table absent in current store)` until the schema is
    initialized/migrated. This is an audit-reporting correction, not a runtime
    queue behavior change.
    2026-07-16: CLI restore audit-write fail-closed slice is ready for
    independent review. `scripts/backup_state.py restore` now runs backup
    verification plus lock/force guards first, then requires a pre-mutation
    `state_restore` operator event with result `started`; if that audit write
    fails, restore returns `operator_event_write_failed_state_restore_not_started`
    with `touched: false` before moving or copying state. Successful restores
    still record a best-effort completion event after restore, and the JSON
    verdict reports `path_after_restore` for the pre-restore event when the old
    data directory is moved aside. Remaining proof: host-side restore drill and
    migrations/rollbacks beyond this script.
    2026-07-16: AI copilot external-provider audit hook is ready for
    independent review. `services.ai_copilot.providers.call_llm` now appends
    best-effort `ai_copilot_external_provider_call` operator events for
    provider attempts, recording provider/model, prompt character counts,
    result, and error metadata without logging system prompts, user prompts,
    incident context, or report content. The coverage matrix moves the AI
    copilot external-provider family from MISSING to PARTIAL. 2026-07-16:
    provider-governance policy slice is ready for independent review.
    `services.ai_copilot.providers.call_llm` now enforces
    `CBP_COPILOT_ALLOWED_PROVIDERS` before any SDK import or API-key lookup.
    Missing allow-list preserves the current supported-provider set
    (`anthropic`, `openai`, `google`); `none` blocks all external-provider calls;
    unknown or malformed allow-list entries fail closed with an audited provider
    failure. 2026-07-16 follow-up invariant is ready for independent review:
    `tests/test_ai_copilot_provider_boundary.py` rejects future
    `services/ai_copilot` Python modules that import external provider SDKs,
    read provider API-key environment variables, or call provider APIs outside
    `call_llm`. Remaining coverage: host-side no-secret scan over real
    provider events.
    2026-08-19: synced-host read-only scan recorded in
    `docs/checkpoints/host_sync_backup_drill_followup_2026_08_19.md` reports
    `ok=true`, `finding_count=0`, and `event_count=0` for the host operator
    event journal path. This is a clean scan of an absent/empty journal, not
    closure for provider-event coverage requiring real provider events.
    2026-08-11: action-specific operator-event secret-scan proof command is
    ready for independent review. `make record-ai-provider-event-secrets`
    requires at least one real `ai_copilot_external_provider_call` event and
    scans the operator-event journal without printing secret values. This does
    not close the host-side proof until run against the real host journal.
    2026-07-16: AI copilot local report-write audit hook is ready for
    independent review. Central `services.ai_copilot` report writers now append
    best-effort metadata-only `ai_copilot_report_write` operator events after
    persisted report artifacts are written, recording report type,
    status/severity, and artifact names/count without logging report payloads,
    stdout/stderr, prompts, recommendations, summaries, or artifact contents.
    Remaining coverage: host-side no-secret scan over real report events.
    2026-08-19: synced-host read-only scan recorded in
    `docs/checkpoints/host_sync_backup_drill_followup_2026_08_19.md` reports
    `ok=true`, `finding_count=0`, and `event_count=0` for the host operator
    event journal path. This is a clean scan of an absent/empty journal, not
    closure for report-event coverage requiring real report events.
    2026-08-11: action-specific operator-event secret-scan proof command is
    ready for independent review. `make record-ai-report-event-secrets`
    requires at least one real `ai_copilot_report_write` event and scans the
    operator-event journal without printing secret values. This does not close
    the host-side proof until run against the real host journal.
    2026-07-16: dashboard strategy-config audit hook is ready for independent
    review. Operations-page strategy parameter saves and preset applies now
    append required `strategy_config_change` operator events after the local
    `user.yaml` save; if the audit write fails, the page attempts to roll back
    to the prior config and reports the failure. The coverage matrix moves the
    strategy/campaign manifest family from MISSING to PARTIAL. Remaining
    coverage: direct manifest file edits, CLI/runtime config edits, and
    campaign manifest changes.
    2026-07-16: dashboard auth operator-event hook is ready for independent
    review. `dashboard.auth_gate` now appends best-effort metadata-only
    `dashboard_login`, `dashboard_logout`, `dashboard_mfa_change`, and
    `dashboard_mfa_challenge` events for session and MFA transitions without
    logging passwords, MFA codes, TOTP secrets, OTP URIs, or backup code
    values. The coverage matrix moves the dashboard login/logout/MFA/role
    family from MISSING to PARTIAL; user/role mutation coverage is narrowed by
    the central auth-store hook below.
    2026-08-11: dashboard login-success session transition audit persistence
    is ready for independent review. `_mark_login_success()` now requires the
    metadata-only `dashboard_login` operator event before the session remains
    authenticated; if the audit write fails, the tentative session is cleared,
    lockout counters are not reset, and callers stay in the sign-in flow.
    Logout and failed auth/MFA challenge events remain best-effort because they
    do not open an authenticated session.
    2026-07-16: central auth-store mutation audit hook is ready for
    independent review. `services.security.user_auth_store` now appends
    best-effort metadata-only `dashboard_user_auth_store_change` events for
    central user upsert/bootstrap, MFA enrollment/confirmation/disablement,
    backup-code consumption, and login-hash upgrades. Events record only user
    identity and state shape (role/enabled/MFA booleans and backup-code
    counts), without logging passwords, hashes, MFA codes, TOTP secrets, OTP
    URIs, or backup code values. Follow-up fail-closed/current-source coverage
    is recorded in the notes below.
    2026-07-16: central auth-store mutation audit-write fail-closed slice is
    ready for independent review. `services.security.user_auth_store` now
    captures raw keyring user/index records before central user upsert/bootstrap,
    MFA enrollment/confirmation/disablement, and backup-code consumption. If the
    required metadata-only `dashboard_user_auth_store_change` event cannot be
    written after mutation, the helper restores those raw records and returns
    `operator_event_write_failed_user_auth_store_rolled_back`. Login-hash
    upgrades roll back the unaudited rehash but allow the already-verified login
    to proceed. Current-source boundary coverage is recorded in the note below.
    2026-08-11: current-source user/role storage boundary invariant is ready
    for independent review. `tests/test_user_auth_store_boundary.py` scans
    `dashboard/`, `scripts/`, and `services/` and fails if any source file outside
    `services/security/user_auth_store.py` starts using the dashboard-auth
    keyring service name, users index account, or private auth-record write
    helpers.
    2026-07-16: central runtime config-save operator-event hook is ready for
    independent review. `services.admin.config_editor.save_user_yaml()` now
    appends best-effort metadata-only `runtime_config_save` operator events
    after successful non-dry-run `user.yaml` writes, recording file existence,
    parse status, top-level section names/count, and result without logging
    config payloads or values. This narrows direct CLI/runtime config coverage
    for strategy, risk, and alert-routing families. Follow-up fail-closed and
    manifest-boundary coverage is recorded in the notes below.
    2026-07-16: central runtime config-save audit-write fail-closed slice is
    ready for independent review. `save_user_yaml()` now treats
    `runtime_config_save` audit persistence as required for non-dry-run writes:
    if the operator-event write fails, it restores the previous file bytes (or
    removes the newly created file for first-write attempts) and returns
    `operator_event_write_failed_runtime_config_rolled_back`. Remaining
    coverage: direct file edits, environment overrides, and campaign manifest
    files.
    2026-08-11: current-source runtime `user.yaml` write boundary invariant is
    ready for independent review. `tests/test_runtime_config_write_boundary.py`
    scans `dashboard/`, `scripts/`, and `services/` and fails if source outside
    `services/admin/config_editor.py` writes, unlinks, or backs up the runtime
    config path directly. This narrows in-repo runtime config bypass coverage;
    manual file edits, environment overrides, server injection, and campaign
    manifest files remain unclassified.
    2026-07-16: API credential-rotation operator-event hook is ready for
    independent review. `services.security.credential_store` now appends
    best-effort metadata-only `api_credential_rotation` operator events after
    central keyring set/delete calls, recording exchange, operation, result,
    and stored field names without logging API keys, API secrets, or
    passphrases. The coverage matrix moves API credential rotation from
    MISSING to PARTIAL. Follow-up fail-closed/current-source coverage is
    recorded in the notes below.
    2026-07-16: API credential-rotation audit-write fail-closed slice is ready
    for independent review. Central `set_exchange_credentials()` and
    `delete_exchange_credentials()` now treat `api_credential_rotation` audit
    persistence as required: if the operator-event write fails, the helper
    restores the previous keyring JSON or removes a newly created entry and
    returns `operator_event_write_failed_api_credential_rotation_rolled_back`.
    If the previous credential cannot be read, the mutation is refused before
    writing. Remaining coverage: direct keyring edits, environment-based
    credential changes, and server injection/rotation drills.
    2026-08-11: current-source API credential keyring boundary invariant is
    ready for independent review. `tests/test_api_credential_store_boundary.py`
    scans `dashboard/`, `scripts/`, and `services/` and fails if source outside
    `services/security/credential_store.py` combines direct keyring mutation
    calls with exchange credential payload fields. Still open:
    direct/manual keyring edits, environment-based credential changes, and
    server injection/rotation drills.
    2026-08-11: exchange credential-source posture command is ready for
    independent review. `make credential-source-posture-json` reports
    keyring/env/missing source per venue without printing credential values;
    the CLI also supports `--fail-on-env` for stricter manual checks. This
    makes environment-backed credential usage explicit, but does not close
    direct/manual keyring edits or server injection/rotation drills.
    2026-07-16: strategy stage-transition operator-event hook is ready for
    independent review. `services.control.deployment_stage` now appends
    best-effort `strategy_stage_transition` events for central promote, demote,
    and safe-degraded transitions, carrying actor, strategy id, from/to stage,
    reason, timestamp, and transition result. The coverage matrix moves
    strategy stage promotion/demotion from MISSING to PARTIAL. Remaining proof:
    promotion audit-write fail-closed policy and host-side promotion proof.
    2026-07-16: promotion audit-write fail-closed slice is ready for
    independent review. `deployment_stage.promote()` now treats
    `strategy_stage_transition` audit persistence as required: if the operator
    event write fails, the stage record is rolled back and the caller receives
    `operator_event_write_failed_stage_promotion_rolled_back`; the
    `show_control_kernel_status --promote` CLI returns nonzero for that
    failure. Demotion and safe-degraded safety moves remain best-effort so
    audit storage cannot block risk-reducing transitions. Remaining proof:
    host-side promotion proof.
    2026-07-16: live intent transition-history hook is ready for independent
    review. `storage.live_intent_queue_sqlite` now creates append-only
    `live_trade_intent_events` rows for successful intent insert, queued-claim,
    and status-transition mutations, recording intent id, timestamp, actor,
    action, pre/post status, reason, source, last error, and order identifiers.
    Duplicate insert attempts, invalid backward transitions, and terminal
    overwrite attempts do not create history rows. This narrows the order
    intent lifecycle family; follow-up source-boundary and venue/fill event
    labeling coverage is recorded in the notes below.
    2026-08-11: current-source live-intent mutation boundary invariant is ready
    for independent review. `tests/test_live_intent_queue_boundary.py` scans
    `dashboard/`, `scripts/`, `services/`, and `storage/` and fails if source
    outside `storage/live_intent_queue_sqlite.py` mutates `live_trade_intents`,
    `live_trade_intent_events`, or `live_consumer_state` directly.
    2026-08-11: live reconciler venue/fill intent-history labeling is ready for
    independent review. `LiveIntentQueueSQLite.update_status()` now accepts
    optional event actor/action/reason/meta fields, and the state-authority
    wrappers pass origin/authority metadata to intent-history rows. The live
    reconciler labels submit-unknown recovery/disposition, venue order
    canceled/rejected/stale/error transitions, fill-accounted transitions,
    lookback fill transitions, and zero-accounted-fill deferrals with specific
    `live_trade_intent_events.action` values. This unifies reconciler and fill
    status provenance in the queue history without changing the state machine,
    submit/retry decisions, or canonical fill accounting. Fill payloads remain
    stored in the existing fill/journal stores; any future lifecycle mutation
    path that bypasses `LiveIntentQueueSQLite` remains blocked by the boundary
    invariant.
    2026-07-17: live-intent history schema preflight is ready for independent
    review. `scripts/check_live_intent_history_schema.py` reports whether the
    current runtime `live_intent_queue.sqlite` has the declared
    `live_trade_intent_events` table. It is read-only by default and exits
    nonzero when the table is missing; `--init` explicitly runs the existing
    `LiveIntentQueueSQLite()` initializer to create/migrate the schema. Makefile
    targets: `make live-intent-history-schema` and
    `make live-intent-history-schema-init`. This does not close host proof by
    itself; run it on the operator host and preserve the JSON evidence.
    2026-08-14: read-only Hetzner schema check is recorded in
    `docs/checkpoints/host_proof_inventory_2026_08_14.md`. Hetzner reported
    `ok=false`, `status=schema_uninitialized`, and
    `reason=live_intent_queue_db_missing` for
    `/var/lib/cbp/data/live_intent_queue.sqlite`. This is consistent with
    paper-only operation and does not initialize or close the live-intent
    history schema evidence.
    2026-07-17: paper-campaign manifest change audit slice is ready for
    independent review. `scripts/update_paper_campaign_manifest.py` provides a
    governed CLI path for schema-v1 paper-campaign manifest enable/disable
    changes: it validates the post-change manifest with the runtime campaign
    loader, records a required metadata-only `campaign_manifest_change`
    operator event before writing, refuses with
    `operator_event_write_failed_campaign_manifest_not_changed` if that event
    cannot be persisted, writes the manifest atomically, and records a
    best-effort completion event. The coverage matrix now names this governed
    path while keeping direct hand edits to manifest files unclassified.
    2026-08-11: current-source paper-campaign manifest write boundary invariant
    is ready for independent review. `tests/test_campaign_manifest_write_boundary.py`
    scans `dashboard/`, `scripts/`, and `services/` and fails if source outside
    the governed manifest update helper/CLI combines active
    `paper_evidence_campaigns*.json` paths with direct write primitives. Manual
    hand edits to manifest files remain outside this proof.
15. Add execution-cost research for maker-vs-taker, fee tiers, and venue cost
    stack. This is deferred and research/shadow-only until expectancy is
    proven. Current evidence shows the paper engine supports limit orders, but
    fee modeling is a single flat rate and the shared fill model is mid-price
    plus/minus bps with no spread-crossing, queue, post-only, or maker/taker
    distinction. When activated, extend fee config to maker/taker rates per
    venue, use shadow would-be-fill records to compare modeled taker fills
    against modeled maker/resting fills, estimate limit-fill probability from
    subsequent price paths, and produce a reproducible per-venue/per-strategy
    cost-stack report in bps. Hard constraint: no live routing or canonical
    order-type policy changes from this item until strategy expectancy and
    shadow cost evidence justify a separate reviewed execution-policy change.
    A 2026-07-03 audit tightened the constraint: current paper-engine limit
    fills are crossing-style only and market fills are full fills, so maker-side
    research must come from shadow would-be-fill records or an explicit engine
    extension, not from current paper-fill behavior. 2026-07-04: research
    policy is documented in `docs/EXECUTION_COST_RESEARCH_POLICY.md`.
    2026-07-12: read-only report-consumer implementation proof is ready for
    independent review. `scripts/report_execution_cost_stack.py` consumes only
    stored `shadow_would_be_fill` evidence, excludes normal paper fills, stamps
    source artifact hashes, computes taker cost in bps from modeled shadow fill
    price plus recorded fees, and reports quote-only maker/resting metrics.
    It refuses to promote maker conclusions without enough stored
    `subsequent_price_path` records to estimate maker fill probability, so
    current shadow records without price-path data produce `research_more`.
    No live routing, order-type policy, or canonical paper-campaign behavior is
    changed.
    Remaining proof: accepted shadow-derived cost-stack report with maker/taker
    bps, limit-fill probability estimates, source artifact hash, and explicit
    `no_change` / `research_more` / `candidate_execution_policy_change`
    recommendation.
16. Quarantine or fail-close the optional `ai_engine` live-router hook before
    any capped-live exposure. `services/live_router/router.py` can enable
    `services/ai_engine` through env/config and currently records
    `ai_error_ignored` with `ok=true` unless strict mode is explicitly enabled.
    That contradicts the repo's fail-closed doctrine for order-routing paths.
    Preferred resolution: remove or hard-disable the live-router AI hook until
    any ML signal enters through the normal strategy registry, evidence
    campaign, provenance qualification, and promotion gates. Minimum acceptable
    resolution if the hook remains: AI-service/model errors block orders by
    default, docs stop describing pass-through as the default live behavior,
    and tests prove an enabled broken AI gate cannot allow an order. Include
    `services/feature_gate.py::proba_gate()` in the same quarantine class:
    it can influence order flow from `CBP_FUSED_PROBA`, tolerates missing or
    invalid values when strict mode is false, and does not enter through the
    strategy/evidence/promotion system. Blocks capped live. 2026-07-05:
    implementation proof is ready for independent review: enabled AI and proba
    gates now fail closed on evaluation/import errors regardless of strict-mode
    compatibility flags, while disabled gates remain non-blocking. Targeted
    router tests cover enabled AI error blocking, disabled AI not being
    evaluated, enabled proba error blocking, and disabled proba import/evaluation
    errors not affecting routing.
17. Restore resume-hard live governance before capped live. The dashboard
    `Resume Live Trading` button reaches `services/admin/resume_gate.py`, and
    the current resume path can set `execution.live_enabled=true`, bypass
    kill-switch/system-guard halted checks, set live armed state, set
    `CBP_EXECUTION_ARMED=YES`, disarm the kill switch, and set the system guard
    RUNNING. That is not equivalent to the one-time-token/checklist ceremony in
    `services/execution/live_enable.py`. Smallest acceptable fix:
    `resume_if_safe()` never writes `live_enabled` from a cold/absent state,
    refuses with a clear reason when no valid prior live-enable ceremony
    provenance exists, and only resumes inside a bounded accepted arming window.
    Proof must cover cold-state refusal, ceremony-armed-then-halted success,
    expired/invalid provenance refusal, and dashboard display of the refusal
    reason. Blocks capped live. 2026-07-05: implementation proof was
    independently reviewed and accepted by the human operator, merged as
    PR #226 to `review-stabilized`, and synced to `master` by PR #227:
    `resume_if_safe()` no longer imports or calls config
    save paths and cannot write `execution.live_enabled`; cold/absent live
    config refuses with `live_not_enabled_ceremony_required`; resume authority
    is anchored to the consumed live-enable ceremony token via read-only
    `live_arming.ceremony_resume_provenance()` inside a bounded window
    (`CBP_RESUME_CEREMONY_MAX_AGE_S`, default 3600s, fail-closed on
    non-finite/invalid values including JSON `NaN` timestamps and non-finite
    explicit clock inputs); targeted tests
    cover cold-state refusal, missing/unconsumed/invalid/future/expired
    provenance refusal, corrupt state file refusal, and
    ceremony-armed-then-halted resume success, with provenance included in the
    dashboard-visible payload. Two prior tests that encoded the cold-state
    re-enable bypass were deliberately rewritten to refuse; the accepted
    policy window is `3600s` with `60s` future-skew tolerance unless a future
    reviewed policy change adjusts it.
18. Add intent TTL before live/shadow consumers are trusted unattended.
    `storage/live_intent_queue_sqlite.py` dequeues and claims queued intents by
    `created_ts ASC`, while current consumers check market snapshot freshness
    but not the intent's own age. A restart after hours or days could submit an
    intent sized and justified by stale context at current prices. Add
    `max_intent_age_sec` with a fail-closed default, mark aged queued/submitting
    intents `expired` with an operator-visible reason, and make the reconciler
    treat `expired` as terminal. Proof: aged-intent fixture expires with zero
    submits; fresh-intent fixture remains eligible. 2026-07-05: implementation
    proof is ready for independent review: `services/execution/intent_ttl.py`
    adds a fail-closed age check (`CBP_MAX_INTENT_AGE_SEC`, default 300s;
    missing/unparseable/non-finite/future `created_ts`, non-finite explicit
    clock inputs, and non-finite or non-positive env overrides all fail
    closed), the canonical
    `services/execution/live_intent_consumer.py` expires age-failed intents at
    the claim boundary before market-quality/risk/dedupe/router processing
    with an operator-visible `expired` counter in consumer status, `expired`
    is a terminal status reachable only from `queued`/`submitting` in both
    `intent_lifecycle.py` and the store SQL transition guard, and the
    reconciler treats `expired` as terminal by construction because its scan
    sources remain `submitted`/`submit_unknown`. Targeted proof covers the
    fail-closed matrix, store transitions (including never re-claiming
    expired), aged/missing-ts intents expiring with zero submits, and fresh
    intents submitting. Deliberate scope notes for review: `submitted`
    intents cannot be expired (reconciler authority); the legacy
    `services/execution/intent_consumer.py` compat consumer (reached only via
    `scripts/compat/run_intent_consumer.py`) did not receive the TTL check
    and should be retired or explicitly classified before any live use; the
    paper consumer path is deliberately untouched; the 300s default and 60s
    future-skew tolerance are policy numbers open to operator adjustment.
    2026-07-11: implementation proof is ready for independent review for the
    legacy compat classification: `scripts/compat/run_intent_consumer.py` now
    fails closed in `run` mode with stable reason
    `legacy_intent_consumer_retired` and points operators to the canonical
    `scripts/run_intent_consumer_safe.py` wrapper. The compat `stop` command
    remains available for old operator stop commands, but the script no longer
    imports or calls `run_forever`. `docs/architecture/legacy_intent_consumer_retirement.md`
    records the decision and states that any revival requires a separate
    high-risk review proving parity with the canonical live consumer.
19. Remove hardcoded reference-price fallbacks from paper pre-submit safety
    checks. This is accepted for the canonical paper engine:
    `services/execution/paper_engine.py` now returns
    `market_quality:no_reference_price` when no limit price, market-quality
    `price_used`, or market-quality `last` can provide a finite positive
    reference price. Targeted proof exists in
    `tests/test_paper_engine_integration.py`. Remaining work is broader
    hardcoded-price cleanup in legacy/demo surfaces and live-router safety
    boundaries only, not the canonical paper pre-submit gate. 2026-07-05:
    implementation proof is ready for independent review for
    `services/live_router/router.py`: the router no longer falls back to a
    BTC-shaped `60000.0` reference price and instead refuses
    `no_reference_price` when no finite positive explicit reference is supplied.
    2026-07-05 CI follow-up: real strategy-runner queued intents now include
    `reference_price` and `reference_price_source` in metadata so downstream
    paper-router checks receive explicit price authority instead of relying on
    the removed fallback; paper-flow fixtures were updated to the same contract.
    Remaining hardcoded `60000.0` references are tests/fixtures or documented
    legacy dry-run stubs (`live_trader_multi` / `live_trader_fleet`) that remain
    outside the canonical paper/live promotion path unless separately revived.

## Deferred Structure And Research Hygiene
These are lower priority than the active paper/research campaign and live-money
substrate work, but they are concrete enough to keep visible.

1. Resolve `services/runtime/run_mode.py` and
   `services/runtime/bot_process.py`: implement the Phase 218/220 operator
   flow or delete the stubs with a documentation update. 2026-07-04: deleted
   both TODO-only placeholder modules after source import scan found no active
   importers; disposition is documented in
   `docs/architecture/runtime_stub_disposition.md`.
   2026-07-25: executable runtime-stub disposition guard is ready for
   independent review. `tests/test_runtime_stub_disposition_guard.py` pins that
   `services/runtime/run_mode.py` and `services/runtime/bot_process.py` remain
   absent, that production source under `services/` and `scripts/` does not
   import those deleted module names, and that `services/runtime/README.md`
   points future work at the disposition record instead of stale placeholders.
   This is docs/test only; no runtime/process behavior changed.
2. Reduce duplicate/twin modules that obscure which code guards money:
   `live_trader_fleet` versus `live_trader_multi`,
   `client_oid.py` versus `client_order_id.py`, and duplicate kill-switch /
   risk-gate modules. Start with a decision record if behavior differs.
   2026-07-03 audit map: `services/admin/kill_switch.py` appears to be the
   operational switch state used by scripts/resume/halt flows;
   `services/risk/kill_conditions.py` is the strategy-runner risk-block logic;
   `services/execution/kill_switch.py` is a thin setter wrapper used by one
   script; `services/risk/killswitch.py` was initially suspected dormant.
   2026-07-04: current source audit showed `services/risk/killswitch.py` is
   active in the live `place_order` kill-switch probe, so it is not dormant.
   Classification is documented in
   `docs/architecture/safety_surface_classification.md`: admin kill-switch is
   canonical operator state, `risk.killswitch` is the live-order safety probe,
   `kill_conditions` is strategy-runner cooldown logic,
   `live_risk_gates.py` is canonical live hard-limit enforcement,
   `ops/risk_gate_*` is telemetry gating, `client_order_id.py` is the
   governed client-order-id builder, `client_oid.py` remains legacy/compat,
   and `live_trader_multi` / `live_trader_fleet` are duplicate dry-run legacy
   stubs that should not receive new live-execution features.
   2026-07-25: executable safety-surface classification guard is ready for
   independent review. `tests/test_safety_surface_classification_guard.py`
   pins the backlog-linked classification doc, canonical client-order-id use
   on governed live paths, legacy-only `client_oid.py` import boundaries,
   dry-run/no-real-routing constraints for `live_trader_multi` and
   `live_trader_fleet`, and the separate authority roles for operator
   kill-switch, live-order safety probe, strategy cooldown, and canonical live
   risk gates. This is docs/test only; no live, order, gate, strategy, or
   runtime behavior changed.
3. [DONE - folded into Active #11] Extend archive-first backtesting proof to
   include one walk-forward run over the archive producing enough
   out-of-sample windows to demonstrate research depth, not only
   byte-identical reruns. 2026-07-15 backlog hygiene: Active #11 now records
   accepted archive-backed walk-forward and bounded parameter-sweep tooling:
   `walk_forward.run_archive_backed_walk_forward()`,
   `scripts/research/run_archive_walk_forward.py`,
   `services.backtest.parameter_sweep`, and
   `scripts/research/run_archive_parameter_sweep.py`. Remaining work is
   operational research execution over real multi-year archives and separate
   review before any strategy config or campaign changes use the results.
4. Rename or document `ws_*` / `market_ws` surfaces before intraday work assumes
   streaming exists. Current accepted direction treats intraday as read-only
   until data cadence and streaming assumptions are proven. 2026-07-04:
   classification is documented in
   `docs/architecture/websocket_surface_classification.md`: `ws_ticker_feed`
   and `user_stream_ws` are real optional ccxt.pro websocket wrappers with
   local tests, while `ws_clients`, `ws_common`, feature blacklist, and health
   logger modules are helpers/telemetry. New intraday or shadow work still must
   prove venue support, supervision, freshness, and evidence authority before
   treating websocket data as canonical. 2026-07-04: stale
   `docs/WS_AUTO_DISABLE.md` references to retired `services/marketdata/*` and
   non-present `ws_microstructure_manager.py` were corrected to the current
   `services/market_data/*` ticker-feed/blacklist surfaces. 2026-07-14:
   WebSocket status-store numeric ingestion proof is ready for independent
   review. `WSStatusSQLite.upsert_status()` now rejects invalid/non-positive
   `recv_ts_ms` and non-finite or negative `lag_ms` before writing current or
   event rows, while preserving valid zero-lag status records. This protects
   freshness/ops telemetry from poisoned lag values without making websocket
   data canonical for trading. 2026-07-14: latency metric-store ingestion
   proof is ready for independent review. `LatencyMetricsSQLite.log_latency()`
   and `SQLiteMarketWsStore.log_latency()` now reject invalid/non-positive
   timestamps and non-finite or negative latency values before mutation, while
   preserving zero-latency measurements. The slice also fixes
   `SQLiteMarketWsStore` persistence by using autocommit like the other SQLite
   telemetry stores, after the regression test showed valid rows were rolling
   back on close.
   2026-07-22: executable websocket-surface classification guard is ready for
   independent review. `tests/test_websocket_surface_classification.py` now
   verifies the documented WS/user-stream surfaces, classifies
   `services/ws/last_price_provider.py` as a tick-store quote reader rather
   than a websocket transport, blocks helper/status modules from quietly adding
   direct `ccxt.pro` / `watch_*` calls, and guards against reintroducing
   retired `services/marketdata/*` or `ws_microstructure_manager.py` paths.
   This is test/docs only; websocket data remains non-canonical until a
   separate venue/supervision/freshness proof is accepted.
5. Add a backtest-to-paper fill parity property test around the shared fill
   model so paper evidence transferability is tested directly. 2026-07-04:
   parity guard added for paper market buy/sell fills: paper engine fill price
   and fee must match `services.execution.fill_model.apply_fee_slippage()` for
   the same mid price, side, qty, fee bps, and slippage bps. 2026-07-22:
   sequence-level parity proof is ready for independent review: a deterministic
   backtest buy/sell round trip is replayed through `PaperTradingSQLite`, and
   cash, closed-trade net PnL, final equity, position quantity, and
   `pnl_usd_semantics=net_of_fees` must match. The proof exposed a paper-only
   float residue mismatch: backtest allowed all-in buys within `1e-9`, while
   paper storage rejected the same fill as insufficient cash. Paper storage now
   uses the same sub-nanodollar affordability tolerance and clamps only that
   residue to zero.
6. Investigate the `synthetic_mid_ohlcv` branch in
   `services/execution/strategy_runner.py`. During the unknown-strategy runner
   proof, the public-OHLCV branch was shown to call `compute_signal()`, while
   `_strategy_signal()` had no visible caller in the current runner. An
   implementation proof is ready for independent review: the tick/synthetic
   branch now calls `_strategy_signal()` after warmup, and the targeted runner
   regression proves a synthetic buy signal creates one queued strategy intent
   without paper orders or fills.
7. Add paper-ledger invariant tests around `PaperTradingSQLite.apply_fill`.
   The store updates order, fill, position, cash, and realized PnL in one
   transaction, which is stronger than earlier fragmented-store framing. Add a
   property or sequence test proving cash, fills, and positions reconcile after
   mixed buy/sell fills so future changes preserve that invariant. 2026-07-04:
   implementation proof is ready: direct storage-level tests cover a mixed
   buy/sell sequence and a flat-price round trip with fees, asserting cash,
   fills, positions, realized PnL, filled order status, and
   `pnl_usd_semantics=net_of_fees` stay reconciled.
8. Classify the three paper execution surfaces and retire or document
   non-canonical paths. Audits found `services/paper/main.py`,
   `services/paper_trader/main.py`, and `services/execution/paper_engine.py`
   with different responsibilities. `paper_engine.py` appears to be the
   evidence-aware path; the older runners should either delegate to it, be
   marked retired, or have an explicit supported-use label. 2026-07-03:
   current classification is documented in
   `docs/architecture/paper_execution_surfaces.md`: `paper_engine.py` is core,
   `services/paper_trader/` is compatibility, and `services/paper/` remains
   retired. 2026-07-04: follow-up for
   `services/trading_runner/run_trader.py` is closed by classifying it as a
   legacy compatibility runner: paper-only local EMA smoke coverage, not a
   canonical promotion-evidence path and not a surface for new paper execution
   features. 2026-07-22: an executable classification invariant is ready for
   independent review, proving the documented core/compatibility/retired paper
   execution surfaces still match the tracked source tree.
9. Classify dormant or partially wired signal-discovery modules.
   `signal_library`, `market_ranker`, `candidate_engine`,
   `candidate_strategy_mapper`, `trade_type_classifier`, and
   `universe_loader` contain useful discovery/ranking logic, but their active
   production path and intended operator workflow are still unclear. Include
   `services/market_data/composite_ranker.py` and
   `services/market_data/rotation_engine.py` in the same classification pass:
   they contain setup-quality / symbol-selection machinery, but the connection
   from ranking to governed paper campaigns is not yet the canonical strategy
   path. Decide which are part of the candidate pipeline, which are
   research-only, and which should be retired. If setup-quality scores are later
   used for trade/no-trade thresholds or sizing scalars, require archive
   walk-forward proof and net-fee metrics first. 2026-07-03: classification is
   documented in `docs/research/signal_discovery_classification.md`; discovery
   and ranker surfaces remain research/advisory only unless separately proven
   through archive-backed, net-fee, governed activation. 2026-07-22:
   executable hygiene proof is ready for independent review: the classification
   table is guarded against source-tree drift, discovery/ranker modules are
   blocked from direct execution/control/governance imports, the only
   candidate-advisor runtime bridge remains explicitly env-gated, and
   `open_interest_shift` is enforced as config-only/trade-disabled until it is
   registry-executable.
   2026-07-22: executable strategy-selection authority decision guard is ready
   for independent review.
   `tests/test_strategy_selection_authority_decision_guard.py` pins configured
   strategy identity as the only execution authority, advisory selector
   boundaries, synthetic evidence-label boundaries, invariants, and the backlog
   link to `docs/decisions/strategy_selection_authority_decision.md`. This is
   docs/test only and does not change strategy selection, registry behavior,
   campaign logic, or execution behavior.
10. Classify storage orphan modules before more reconciliation work.
    Prior audits flagged unused SQLite stores such as fill reconciler,
    idempotency, and order-tracker variants. Confirm whether each is truly
    unused on current master, then delete, wire, or document it as a retired
    compatibility surface. 2026-07-03: classification is documented in
    `docs/architecture/storage_surface_classification.md`; three candidate
    stores remain unwired candidates pending a deeper caller/migration audit.
    2026-07-04: targeted caller audit found no visible production source
    importers for `fill_reconciler_store_sqlite.py`,
    `order_idempotency_sqlite.py`, or `order_tracker_store_sqlite.py`; matches
    are the modules themselves and prior docs/audit artifacts. 2026-07-04:
    disposition decision is recorded in
    `docs/architecture/storage_surface_classification.md`: explicitly retain
    the three schemas as quarantined retained schemas during paper/research,
    do not wire new callers, and defer deletion/migration until the state-store
    consolidation migration packet decides whether any schema/data is needed.
    2026-07-22: executable storage-quarantine hygiene proof is ready for
    independent review. `tests/test_storage_surface_classification.py` now
    verifies the classification doc covers the three retained schemas and that
    no service/script imports `fill_reconciler_store_sqlite`,
    `order_idempotency_sqlite`, or `order_tracker_store_sqlite` as production
    callers. This is test/docs only: no schema deletion, migration, wiring, or
    runtime behavior change.
11. Extract promotion-gate logic into a library after the current paper gate is
    stable. `scripts/check_promotion_gates.py` is the canonical operator
    command today and should not be churned mid-campaign, but the money-adjacent
    gate logic should eventually live in `services/control/` with the script,
    dashboard, and monitors consuming the same implementation.
12. Triage the broader product objective explicitly. `docs/OBJECTIVE.md`
    describes learning/adaptive capability, multi-exchange support, and a
    packaged desktop app. Current operation is paper/research plus server
    monitoring. Create a decision record for each larger product surface:
    retain and schedule, defer, or retire from the near-term production path.
    Default near-term stance should be lab-mode concentration: freeze desktop
    packaging, onboarding/product polish, and non-operator-critical dashboard
    work unless it directly improves evidence collection, safety, alerting, or
    operator decision quality. 2026-07-03: triage baseline is documented in
    `docs/PRODUCT_SURFACE_TRIAGE.md`; broader product expansion remains deferred
    until expectancy is proven or a task supports the retained evidence/safety
    path.
    2026-07-22: executable product-surface triage guard is ready for
    independent review. `tests/test_product_surface_triage.py` pins the
    lab-mode concentration stance, retain/defer lists, decision-rule terms,
    project identity link, and README root-boundary summary. This is docs/test
    only and does not change product/runtime behavior.
13. Keep pattern/candlestick strategy research visible but behind the archive
    and paper-evidence gates. Existing code covers pullbacks, gap fills,
    volatility reversals, order-book imbalance, funding, and open interest.
    Missing pattern work includes candlestick confirmation, fair-value gaps,
    order-block style zones, and larger chart-pattern recognition. Treat these
    as research filters or candidate strategies only after archive-first
    backtesting and provenance-qualified paper paths are in place. 2026-07-03:
    visible backlog is documented in `docs/research/pattern_strategy_backlog.md`.
    2026-07-21: operator-requested price-action concepts are now scoped as a
    single research-only context feature pack, not separate strategy starts:
    fair-value gaps, engulfing candles, swing failures, break/retest,
    rejection wicks, opening-range state, acceptance/rejection, displacement
    versus manipulation-candidate labels, swing-trading context, and later
    volume-profile labels. Required boundary: labels must be emitted as
    dataset-hashed artifacts over archived data, joined to forward returns, and
    reviewed as context/confirmation evidence before any strategy config,
    campaign, or promotion-gate use. Databento is explicitly deferred to a
    separate read-only data-source RFC because it adds API-key, metered-cost,
    dataset/schema, symbology, and futures/equities-style governance decisions.
    2026-07-22: first OHLCV-only price-action context extractor slice is ready
    for review. `services/backtest/price_action_context.py` and
    `scripts/research/run_price_action_context_labels.py` read only the
    existing market OHLCV archive, refuse unavailable/incomplete archive data
    instead of fetching live, and emit dataset-hashed research artifacts with
    per-bar labels for engulfing candles, rejection wicks, swing failures,
    break/retest, fair-value gaps, displacement bars, opening-range state,
    acceptance/rejection context, and manipulation-candidate descriptions.
    The artifact carries explicit limitation flags:
    `research_only`, `not_strategy_config`, `not_campaign_evidence`,
    `not_promotion_evidence`, and `not_profitability_evidence`. No strategy
    config, campaign, gate, execution, or Databento path is changed. Remaining:
    join labels to forward returns after modeled costs, measure stability
    against unconditioned baselines, and require separate review before any
    label becomes a confirmation filter.
    2026-07-22: second research-only slice is ready for review.
    `services/analytics/price_action_forward_returns.py` and
    `scripts/research/run_price_action_forward_returns.py` join the archived
    OHLCV labels to unit-size long/short forward returns after explicit
    fee/slippage assumptions, produce unconditioned and per-label bucket
    summaries, and include the cost assumptions in the artifact hash. This is
    descriptive research output only: no position state, portfolio PnL,
    strategy config, campaign evidence, promotion evidence, gate, execution, or
    Databento path is changed. Remaining: run real archive reports across
    multiple windows, compare label-conditioned returns against unconditioned
    baselines for stability/sample size/false-positive rate, and require
    separate review before any label becomes a confirmation filter.
    2026-07-22: third research-only slice is ready for review.
    `services/analytics/price_action_window_stability.py` and
    `scripts/research/run_price_action_window_stability.py` compare
    label-conditioned forward returns against unconditioned baselines across
    fixed archive windows and summarize each label bucket's average delta plus
    outperform/underperform window ratios. This remains stability triage only:
    no activation, profitability, campaign, promotion, gate, execution, or
    Databento claim is made. Remaining: run the reports on real multi-window
    archives across relevant symbols/timeframes and require separate review
    before any label influences a strategy confirmation filter.
    2026-07-22: fourth research-only slice is ready for review.
    `services/analytics/price_action_candidate_triage.py` and
    `scripts/research/run_price_action_candidate_triage.py` consume the
    multi-window stability artifact and apply explicit thresholds for windows,
    sample size, average delta, outperform ratio, and underperform ratio. The
    output ranks label/side pairs as `candidate_for_manual_review` or
    `not_candidate`, carries false-positive proxy metadata, and keeps the hard
    boundary: no activation, profitability, campaign, promotion, gate,
    execution, strategy config, or Databento claim is made. Remaining: run real
    archive triage across relevant symbols/timeframes and review thresholds
    separately before any label becomes a confirmation-filter candidate.
    2026-07-22: executable price-action research-boundary guard is ready for
    independent review. `tests/test_price_action_research_boundary_guard.py`
    pins research-only status, core OHLCV label scope, non-authority artifact
    flags, data-source deferrals, acceptance-before-use requirements, and the
    backlog link to `docs/research/pattern_strategy_backlog.md`. This is
    docs/test only and does not change label generation, forward-return joins,
    stability reports, strategy configs, campaigns, promotion gates, or
    execution behavior.
    2026-07-22: Databento read-only data-source RFC is ready for independent
    review in `docs/research/databento_data_source_rfc.md`.
    `tests/test_databento_data_source_rfc.py` pins the no-implementation
    authorization, research-only scope, required decisions, hard boundaries,
    acceptance criteria, and pattern/backlog links. This is docs/test only and
    does not add credentials, dependencies, data fetches, campaign inputs,
    promotion evidence, or execution behavior.
    2026-07-25: read-only price-action research pipeline wrapper is ready for
    independent review. `scripts/research/run_price_action_research_pipeline.py`
    runs the accepted labels, forward-returns, window-stability, and
    candidate-triage reports in sequence, writes each report plus a summary
    manifest, and stops fail-closed when any step cannot produce an `ok=true`
    artifact. `make price-action-research-pipeline` and `scripts/SCRIPTS.md`
    expose the wrapper. This is research orchestration only; it does not change
    labels, scoring, strategy config, campaigns, gates, data ingestion, live
    routing, execution, or promotion evidence.
    2026-07-25: read-only research pipeline status report is ready for
    independent review. `services.analytics.research_pipeline_status` and
    `scripts/research/report_research_pipeline_status.py` inventory the
    accepted funding-threshold and price-action pipeline wrappers, verify
    script/Makefile/SCRIPTS wiring, and report latest `pipeline_summary.json`
    status/hash when present. Missing latest artifacts are reported as
    `not_run`, not as failures. This is status/observability only; it does not
    run pipelines, fetch data, or change research artifacts, strategy config,
    campaigns, gates, data ingestion, live routing, execution, or promotion
    evidence.
    2026-08-25: local research refresh recorded in
    `docs/checkpoints/research_pipeline_refresh_2026_08_25.md`. `make
    price-action-research-pipeline` returned `ok=true` and wrote four
    research-only artifacts under
    `.cbp_state/data/research/price_action_pipeline/20260825T050434Z` for
    Coinbase `BTC/USDT` `1h`. Candidate triage produced `15` label/side pairs
    for manual review, led by `opening_range_state:inside` long,
    `break_and_retest:bearish_hold` long, and `fair_value_gap:bearish` long.
    These remain descriptive research candidates only and do not authorize a
    confirmation filter, strategy config, campaign, gate, promotion, or
    execution change.
    2026-08-27: local research refresh recorded in
    `docs/checkpoints/research_pipeline_refresh_2026_08_27.md`. `make
    price-action-research-pipeline` returned `ok=true` and wrote four
    research-only artifacts under
    `.cbp_state/data/research/price_action_pipeline/20260827T070741Z` for
    Coinbase `BTC/USDT` `1h`. Candidate triage again produced `15` label/side
    pairs for manual review, led by `opening_range_state:inside` long,
    `break_and_retest:bearish_hold` long, and `fair_value_gap:bearish` long.
    `make funding-threshold-research-pipeline` also returned `ok=true` under
    `.cbp_state/data/research/funding_threshold_pipeline/20260827T070741Z`,
    but both funding candidate triage artifacts produced `0` review
    candidates from `412` input rows. These remain descriptive research
    artifacts only and do not authorize a confirmation filter, strategy config,
    campaign, gate, promotion, or execution change.
    2026-08-27: multi-market local price-action research checkpoint recorded
    in `docs/checkpoints/price_action_multi_market_research_2026_08_27.md`.
    Four read-only archive-backed variants returned `ok=true`: Coinbase
    `BTC/USD` `1d`, Coinbase `BTC/USDT` `5m`, OKX `BTC/USDT` `5m`, and OKX
    `ETH/USDT` `5m`. Manual-review candidate counts were `18`, `13`, `13`,
    and `15`. Repeated candidates across multiple runs were concentrated in
    opening-range acceptance/rejection labels, with `fair_value_gap` and
    `swing_failure` labels appearing in fewer runs. These remain descriptive
    research artifacts only and do not authorize a confirmation filter,
    strategy config, campaign, gate, promotion, or execution change.
    2026-07-28: research pipeline status filtering is ready for independent
    review. The report now supports `--pipeline <pipeline_id>` and the Make
    override `RESEARCH_PIPELINE_STATUS_PIPELINE`; filtered JSON keeps
    `source_pipeline_count` and source summary counts so one-pipeline views
    remain auditable against the full accepted pipeline set. This remains
    status/observability only; it does not run pipelines, fetch data, or change
    research artifacts, strategy config, campaigns, gates, data ingestion, live
    routing, execution, or promotion evidence.
    2026-07-28: research pipeline status action hints are ready for independent
    review. Each pipeline row now includes `action_required`,
    `blocking_reason`, and `next_action`, distinguishing wiring drift from
    missing/latest-not-ok artifacts and naming the Make target to run or repair.
    The report remains read-only and still does not run pipelines, fetch data,
    generate artifacts, or change research artifacts, strategy config,
    campaigns, gates, data ingestion, live routing, execution, or promotion
    evidence.
    2026-07-29: research pipeline filter fail-closed behavior is ready for
    independent review. Unknown `--pipeline` /
    `RESEARCH_PIPELINE_STATUS_PIPELINE` values now return `ok=false`,
    `reason=invalid_pipeline`, zero rows, and the accepted
    `available_pipeline_ids`; operator-status and operator-next-actions
    propagate the source reason when the same bad filter is forwarded. Valid
    one-pipeline views still preserve source counts and latest artifact hashes.
    This remains read-only status/reporting only and does not run research
    jobs, fetch data, generate artifacts, or change research artifacts,
    strategy config, campaigns, gates, data ingestion, live routing,
    execution, or promotion evidence.
    2026-07-28: read-only research command status report is ready for
    independent review. `services.analytics.research_command_status` and
    `scripts/research/report_research_command_status.py` inventory accepted
    research commands by lane/input class and verify script/SCRIPTS/Makefile
    wiring where a Make target is part of the command contract. This is
    status/observability only; it does not run research jobs, fetch data,
    generate artifacts, or change research artifacts, strategy config,
    campaigns, gates, data ingestion, live routing, execution, or promotion
    evidence.
    2026-07-28: research command status is now wired into the operator status
    bundle and exposed via `make research-command-status`. The added wiring is
    still status-only: it does not run research jobs, fetch data, generate
    artifacts, or change research artifacts, strategy config, campaigns,
    gates, data ingestion, live routing, execution, or promotion evidence.
    2026-07-28: research command status lane/input filters are ready for
    independent review. `build_research_command_status`, the CLI, and Make
    targets now support focused views by command `lane` and `input_class`
    while preserving source-count summaries over the full command registry.
    This remains read-only status/reporting only and does not run research
    jobs, fetch data, generate artifacts, or change research artifacts,
    strategy config, campaigns, gates, data ingestion, live routing,
    execution, or promotion evidence.
    2026-07-28: research command status action hints are ready for
    independent review. Each command row now includes `action_required`,
    `blocking_reason`, and `next_action` for script/SCRIPTS/Makefile wiring
    drift; `operator_status_bundle` and `operator_next_actions` surface those
    rows as a `research_command` action lane. Current repo output shows all
    19 accepted research commands wired and zero research-command actions
    required. This remains read-only status/reporting only and does not run
    research jobs, fetch data, generate artifacts, or change research
    artifacts, strategy config, campaigns, gates, data ingestion, live
    routing, execution, or promotion evidence.
    2026-07-29: research command exact-ID filtering is ready for independent
    review. `research-command-status`, `operator-status`, and
    `operator-next-actions` now accept a `command_id`/Make override to focus a
    single accepted research command while preserving source counts and
    fail-closing unknown command IDs as `invalid_command_id`. This remains
    read-only status/reporting only and does not run research jobs, fetch data,
    generate artifacts, or change research artifacts, strategy config,
    campaigns, gates, data ingestion, live routing, execution, or promotion
    evidence.
    2026-07-29: research artifact inventory is ready for independent review.
    `services.analytics.research_artifact_inventory` and
    `scripts/research/report_research_artifact_inventory.py` inventory accepted
    archive, funding-threshold, and price-action research artifacts by lane,
    latest path, marker, hash, status, and next action. Missing artifacts are
    action rows, unreadable or marker-mismatched artifacts fail closed, and
    unknown artifact IDs return `invalid_artifact_id`. `make
    research-artifact-inventory[-json]` exposes the report and
    `research_command_status` registers it as a status command. Local output
    shows existing funding/price-action artifacts present and three archive
    research artifacts missing (`archive_walk_forward`,
    `archive_parameter_sweep`, `archive_parameter_sweep_triage`) with Make
    targets named for the next operator runs. This remains read-only
    status/reporting only and does not run research jobs, fetch data, generate
    artifacts, or change research artifacts, strategy config, campaigns,
    gates, data ingestion, live routing, execution, or promotion evidence.
    2026-07-29: research artifact producer-plan metadata is ready for
    independent review. `research_artifact_inventory` now includes a
    `producer_plan` for each accepted artifact with the Make target, Make args
    variable, required accepted inputs, and a command hint. Missing artifact
    `next_action` text now distinguishes a bare Make target from an artifact
    that first needs accepted input selection (for example strategy config,
    grid, archive row window, and output path). The report remains read-only:
    it does not run producer commands, create artifacts, fetch market data,
    choose research inputs, change strategy/campaign/gate state, or mutate
    runtime state.
    2026-07-29: research status filter hardening is ready for independent
    review. `research_artifact_inventory` now fail-closes unknown lane filters
    as `invalid_lane` with accepted `available_lanes`; `research_command_status`
    now fail-closes unknown `lane` and `input_class` filters as
    `invalid_lane` / `invalid_input_class` with accepted filter values. Exact
    command/artifact ID fail-closed behavior remains intact. This is
    read-only status/reporting only and does not run research jobs, fetch
    data, generate artifacts, or change research artifacts, strategy config,
    campaigns, gates, data ingestion, live routing, execution, or promotion
    evidence.
    2026-07-30: archive artifact input recipe documentation is ready for
    independent review. `docs/research/archive_artifact_input_recipes.md`
    records the accepted-input contract for `archive_walk_forward`,
    `archive_parameter_sweep`, and `archive_parameter_sweep_triage`: each
    producer requires explicit args via its Make args variable and has no
    accepted checked-in default recipe, grid, or archive window. The guard test
    pins the doc against the accepted archive artifact registry. This is
    docs/tests only; it does not run research jobs, fetch market data,
    generate artifacts, choose research inputs, change strategy/campaign/gate
    state, or mutate runtime state.
14. Triage dashboard/data-page wiring as a product backlog, not a trading gate.
    Several dashboard pages have UI surfaces without confirmed live service
    data behind them. Prioritize operator-critical pages first: gate status,
    paper reconciliation, campaign health, market movers, and copilot reports.
    2026-07-03: priority policy is documented in
    `docs/dashboard/DATA_PAGE_BACKLOG.md`; state-mutating pages still require
    role guards and cannot bypass accepted ceremonies.
    2026-07-22: executable dashboard data-page triage guard is ready for
    independent review. `docs/dashboard/DATA_PAGE_BACKLOG.md` now maps each
    operator-critical category to concrete page/service paths, and
    `tests/test_dashboard_data_page_backlog.py` pins both the path map and the
    mutation-boundary rule. This is docs/test only and does not change
    dashboard behavior.
15. Vendor, explicitly integrate, or excise the companion-repo dependency.
    `phase1_research_copilot` has appeared in compose/docs/skip-test context
    during audits. Split-brain repos rot deployment stories. Decide whether the
    companion is a vendored dependency, an external documented prerequisite, or
    retired from the canonical path, then update compose, docs, and tests to
    match. 2026-07-03: `docs/COMPANION_REPO_DEPENDENCY.md` classifies it as a
    sidecar/archived companion, not a required root runtime dependency; future
    active use must vendor it or document it as an explicit external
    prerequisite.
    2026-07-22: Compose-side companion dependency hardening is ready for
    independent review. `docker/docker-compose.yml` now gates the
    `phase1_research_copilot` backend behind the explicit
    `phase1-companion` profile and removes the dashboard's hard dependency on
    that backend. `tests/test_companion_repo_dependency.py` pins the default
    root Docker startup as sidecar-optional. This touches Docker startup
    behavior, so review as deploy/runtime scope.
16. Add risk-tiered governance lanes to the operator workflow. Keep full
    ceremony for high-risk changes touching gates, dispatch, execution,
    secrets, deployment, and live-risk surfaces. Allow a lighter documented
    lane for low-risk docs/tests/reporting changes with clear PR labeling,
    targeted verification, and work-log coverage. The goal is to preserve
    rigor where it protects money while reducing process tax where it only
    delays low-risk cleanup. 2026-07-03: baseline lane policy is written in
    `docs/OPERATOR_GOVERNANCE_LANES.md`; future work should apply the lane
    label in PRs without weakening AGENTS.md high-risk review rules.
    2026-07-22: executable governance-lane scope guard is ready for
    independent review. `tests/test_operator_governance_lanes.py` pins the
    low/medium/high lane boundaries, high-risk examples, operator attention
    cap, PR label convention, and AGENTS.md override. This is docs/test only
    and does not change runtime behavior.
17. Define the operational core and quarantine policy. Add a `CORE.md` or
    equivalent decision record that names the modules required for the current
    paper/research/shadow path, plus a quarantine/attic policy for surfaces not
    in that core. Do not move broad directories in one sweep; first classify,
    then retire, delegate, or document. 2026-07-03: baseline is documented in
    `docs/CORE.md`. 2026-07-04: `docs/CORE.md`, `docs/ARCHITECTURE.md`, and
    `docs/REPO_LAYOUT.md` now link the paper execution, safety, storage,
    websocket, and signal-discovery classification records so the quarantine
    policy points at concrete disposition docs.
    2026-07-22: executable operational-core scope guard is ready for
    independent review. `tests/test_operational_core_scope.py` pins the core
    surface list, quarantine states, priority rule, and classification-record
    links from `docs/CORE.md`. This is docs/test only and does not change
    runtime behavior.
18. Protect operator attention as a managed resource. Add a decision record or
    runbook rule that caps open audit loops, limits low-value review churn, and
    forces each proactive task to tie back to one of: evidence velocity,
    profitability discovery, cost measurement, safety, recovery, or operator
    wake-up quality. 2026-07-03: this rule is captured in
    `docs/OPERATOR_GOVERNANCE_LANES.md` as the operator attention cap.
    2026-07-04: `docs/BACKLOG_EXECUTION_LANES.md` classifies the remaining
    backlog into passive/operator evidence, low-risk docs/tests, medium-risk
    read-only runtime work, and high-risk gate/execution/deploy work so
    same-lane batching is explicit and high-risk work is not mixed into
    cleanup passes.
    2026-07-21: `docs/BACKLOG_EXECUTION_LANES.md` is refreshed against current
    `master` after many prior coding candidates landed. It now distinguishes
    completed/proof-ready implementation text from remaining operator evidence,
    read-only research/reporting, and the small set of genuinely high-risk
    capped-live coding objectives.
    2026-07-22: executable backlog execution-lanes guard is ready for review.
    `tests/test_backlog_execution_lanes_guard.py` pins
    `REMAINING_TASKS.md` as the backlog source of truth, the four lane
    definitions, the warning not to rebuild completed/proof-ready work,
    high-risk no-mixed-batch boundaries, the same-lane batching rule, and the
    current practical order. This is docs/test only and does not decide any
    backlog item, authorize implementation, or change runtime behavior.
    2026-07-25: read-only backlog lane status report is ready for independent
    review. `services.analytics.backlog_lane_status` and
    `scripts/report_backlog_lane_status.py` summarize the lane counts from
    `docs/BACKLOG_EXECUTION_LANES.md`, include source/backlog hashes, and
    expose `make backlog-lane-status`. The report is planning/status only: it
    does not decide backlog items, authorize implementation, or change runtime
    behavior.
    2026-07-28: backlog lane status filtering is ready for independent review.
    `build_backlog_lane_status`, the CLI, and Make targets now support focused
    views by canonical lane key while preserving full source lane/item counts
    and source summaries. Invalid lane names fail closed as `invalid_lane`.
    This remains planning/status only and does not decide backlog items,
    authorize implementation, run campaigns, fetch market data, close proof, or
    mutate runtime state.
    2026-07-28: read-only operator proof status report is ready for
    independent review. `services.analytics.operator_proof_status` and
    `scripts/report_operator_proof_status.py` summarize the
    passive/operator-evidence lane and surface proof/coverage markers from
    `REMAINING_TASKS.md` with line references and source hashes. It exposes
    `make operator-proof-status` and is planning/status only: it does not run
    campaigns, fetch market data, close proof, authorize implementation, or
    mutate runtime state.
    2026-07-28: operator proof status action hints are ready for independent
    review. Passive lane rows and proof/coverage markers now carry
    `action_required`/`next_action`, and text output prints the action next to
    the passive item or backlog line reference. This is presentation/JSON
    status only and does not run campaigns, fetch market data, close proof,
    authorize implementation, or mutate runtime state.
    2026-07-28: operator proof status category filtering is ready for
    independent review. `build_operator_proof_status()` now accepts optional
    `category`, `scripts/report_operator_proof_status.py` exposes `--category`,
    and Make exposes `OPERATOR_PROOF_STATUS_CATEGORY` for text/JSON targets.
    Filtered reports keep the original source marker count and source category
    counts for auditability while narrowing returned proof markers to the
    requested category. This is presentation/JSON status only and does not run
    campaigns, fetch market data, close proof, authorize implementation, or
    mutate runtime state.
    2026-07-30: operator proof status passive-ordinal filtering is ready for
    independent review. `build_operator_proof_status()`, the CLI, Make targets,
    `operator-status`, and `operator-next-actions` now support a 1-based
    passive operator-evidence ordinal filter. Invalid passive ordinals fail
    closed as `invalid_passive_operator_ordinal`; valid filters preserve source
    passive counts while returning one passive action row. This remains
    presentation/JSON status only and does not run campaigns, fetch market
    data, close proof, authorize implementation, or mutate runtime state.
    2026-07-30: operator proof status category filtering now fails closed for
    unknown categories and reports `available_categories`. Previously an
    unknown category returned an empty successful report; now the source report
    returns `ok=false`, `reason=invalid_category`, and the operator-status
    bundle propagates that source reason. This remains presentation/JSON
    status only and does not run campaigns, fetch market data, close proof,
    authorize implementation, or mutate runtime state.
    2026-07-28: read-only operator status bundle is ready for independent
    review. `services.analytics.operator_status_bundle` and
    `scripts/report_operator_status_bundle.py` combine backlog lane status,
    research pipeline status, and operator proof status behind
    `make operator-status`. The bundle is check-in/status only: it does not
    run pipelines or campaigns, fetch market data, close proof, authorize
    implementation, or mutate runtime state.
    2026-07-28: operator status now surfaces unresolved research pipeline
    actions from the underlying research pipeline report, including the
    `blocking_reason` and `next_action` per pipeline. This is presentation and
    JSON-status wiring only; it does not run pipelines or campaigns, fetch
    market data, close proof, authorize implementation, or mutate runtime
    state.
    2026-07-28: operator status now also carries a bounded operator-proof
    action list from the underlying proof-status report and summarizes total
    proof actions required. This is still status-only and does not run
    campaigns, fetch market data, close proof, authorize implementation, or
    mutate runtime state.
    2026-07-28: operator status section filtering is ready for independent
    review. `build_operator_status_bundle`, the CLI, and Make targets now
    support `backlog`, `research_pipeline`, `research_command`, and
    `operator_proof` focused views while still deriving all underlying status
    reports read-only. Invalid section names fail closed as `invalid_section`.
    This remains presentation/JSON status only and does not run pipelines or
    campaigns, fetch market data, close proof, authorize implementation, or
    mutate runtime state.
    2026-07-28: operator status underlying-report filter pass-through is ready
    for independent review. The bundle, CLI, and Make targets can now forward
    accepted filters to backlog lane status, research command status, and
    operator proof status while preserving the bundle's read-only boundary.
    This remains presentation/JSON status only and does not run pipelines or
    campaigns, fetch market data, close proof, authorize implementation, or
    mutate runtime state.
    2026-07-28: operator status research-pipeline filter pass-through is ready
    for independent review. The bundle, CLI, and Make targets can now forward
    the accepted research pipeline `pipeline_id` filter as well, so focused
    operator-status views can select one research pipeline without running it
    or changing underlying status sources. This remains presentation/JSON
    status only and does not run pipelines or campaigns, fetch market data,
    close proof, authorize implementation, or mutate runtime state.
    2026-07-28: compact operator next-actions report is ready for independent
    review. `services.analytics.operator_next_actions` and
    `scripts/report_operator_next_actions.py` derive a bounded action list from
    the existing operator status bundle, exposed as `make operator-next-actions`
    and `make operator-next-actions-json`. This is read-only planning/status
    only; it does not run research pipelines or campaigns, fetch market data,
    close proof, authorize implementation, or mutate runtime state.
    2026-07-28: operator next-actions filtering is ready for independent
    review. The report supports `--lane research_pipeline|operator_proof` and
    Make overrides `OPERATOR_NEXT_ACTIONS_MAX` / `OPERATOR_NEXT_ACTIONS_LANE`
    so check-ins can focus on research or proof blockers without changing the
    underlying status sources. This remains read-only planning/status only.
    2026-07-28: operator next-actions summary buckets are ready for
    independent review. The report now includes additive `summary` fields for
    available actions grouped by lane and blocking reason, and the text output
    prints those buckets before the detailed action list. This remains
    read-only planning/status only and does not change status sources or
    runtime behavior.
    2026-07-28: operator next-actions reason filtering is ready for independent
    review. The report now supports `--reason <blocking_reason>` and the Make
    override `OPERATOR_NEXT_ACTIONS_REASON`, allowing focused checks such as
    host-side-only or remaining-proof-only actions without changing underlying
    status sources. This remains read-only planning/status only.
    2026-07-28: operator next-actions source-filter pass-through is ready for
    independent review. The compact report, CLI, and Make targets can now
    forward the accepted source-report filters for backlog lane, research
    pipeline, research command lane/input class, and operator proof category to
    the underlying operator status bundle. Action-producing source filters
    (`research_pipeline`, `operator_proof_category`) narrow the compact action
    list to their matching action lane unless an explicit lane filter is set.
    This remains read-only planning/status only and does not run research,
    campaigns, market-data fetches, proof closure, authorization, or runtime
    mutation.
    2026-07-28: JSON Make targets for read-only operator/status reports are
    ready for independent review: `backlog-lane-status-json`,
    `operator-proof-status-json`, `operator-status-json`,
    `research-pipeline-status-json`, and `research-command-status-json`. These
    are CLI wiring only and preserve the same no-campaign, no-market-fetch,
    no-proof-closure, and no-runtime-mutation boundaries as the underlying
    scripts.
    2026-07-28: operator proof line filtering is ready for independent review.
    `operator-proof-status`, `operator-status`, and `operator-next-actions`
    can now focus proof markers by exact `REMAINING_TASKS.md` line via
    `--line`, `--operator-proof-line`, or the matching Make overrides. Invalid
    line filters fail closed as `invalid_line`. This remains read-only
    planning/status only and does not run research, campaigns, market-data
    fetches, proof closure, authorization, or runtime mutation.
    2026-07-28: operator next-actions final source filtering is ready for
    independent review. The compact report now supports `--action-source` and
    `OPERATOR_NEXT_ACTIONS_SOURCE`, filtering final action rows by their
    normalized `source` field after source reports are built. This remains
    read-only planning/status only and does not change underlying status
    sources, run research/campaigns, fetch market data, close proof, authorize
    implementation, or mutate runtime state.
    2026-07-28: passive operator-evidence next actions are ready for
    independent review. The operator status bundle now exposes
    `passive_operator_evidence` action rows from the passive evidence lane, and
    the compact `operator-next-actions` report includes/filter-supports that
    lane alongside research pipeline and proof-marker actions. This remains
    read-only planning/status only and does not run research, campaigns,
    market-data fetches, proof closure, authorization, or runtime mutation.
    2026-07-28: backlog-lane action hints are ready for independent review.
    When a backlog lane filter is supplied, the operator status bundle exposes
    each lane-map item as a `backlog_lanes` action row and
    `operator-next-actions` surfaces them through the `backlog_lane` action
    lane. Unfiltered default next-actions do not emit backlog-lane rows, so the
    compact report is not flooded with all lane-map categories. This remains
    read-only planning/status only; it does not decide backlog items, run
    research/campaigns, fetch market data, close proof, authorize
    implementation, or mutate runtime state.
    2026-07-29: backlog-lane actionable item parsing is ready for independent
    review. `backlog_lane_status` now separates `Recent examples:` bullets
    from actionable lane items, reports example counts separately, and keeps
    `operator-next-actions` from presenting already-completed examples (for
    example backtest-to-paper parity) as next work. Current low-risk lane
    output now shows 7 actionable items and 6 examples instead of 13 action
    rows. This remains read-only planning/status only; it does not decide
    backlog items, run research/campaigns, fetch market data, close proof,
    authorize implementation, or mutate runtime state.
    2026-07-29: operator next-actions function-level lane validation is ready
    for independent review. The CLI already restricted `--lane`, but direct
    Python callers could pass an unknown lane and receive an empty `ok=true`
    result. `build_operator_next_actions()` now exposes
    `available_action_lanes` and returns `ok=false`,
    `reason=invalid_action_lane`, zero rows, and zero total actions for
    unknown lane filters; valid lane filters are unchanged. This remains
    read-only planning/status only and does not decide backlog items, run
    research/campaigns, fetch market data, close proof, authorize
    implementation, or mutate runtime state.
    2026-07-29: exact backlog-lane actionable item filtering is ready for
    independent review. `operator-status` and `operator-next-actions` now
    accept a 1-based backlog lane ordinal (`OPERATOR_STATUS_BACKLOG_LANE_ORDINAL`
    / `OPERATOR_NEXT_ACTIONS_BACKLOG_LANE_ORDINAL`) to return exactly one
    actionable item from a filtered lane. The filter fails closed with
    `reason=invalid_backlog_lane_ordinal` when no lane is provided, the ordinal
    is non-positive/non-numeric, or the item does not exist; valid lane-only
    behavior is unchanged. This remains read-only planning/status only and
    does not decide backlog items, run research/campaigns, fetch market data,
    close proof, authorize implementation, or mutate runtime state.
    2026-07-29: backlog lane-map selector refresh is ready for independent
    review. `docs/BACKLOG_EXECUTION_LANES.md` now instructs local coding passes
    to name an exact lane item with `OPERATOR_NEXT_ACTIONS_BACKLOG_LANE` plus
    `OPERATOR_NEXT_ACTIONS_BACKLOG_LANE_ORDINAL` before opening another batch,
    and records that invalid selectors fail closed instead of returning an
    empty successful plan. This is docs/test only and does not decide backlog
    items, run research/campaigns, fetch market data, close proof, authorize
    implementation, or mutate runtime state.
    2026-07-29: read-only batch checklist refinement is ready for independent
    review. `docs/OPERATOR_GOVERNANCE_LANES.md` now includes a concise
    read-only batch checklist: name the exact backlog item/report, verify the
    diff avoids campaigns/gates/execution/auth/secrets/migrations/background
    jobs, confirm read-only/planning-only behavior, run narrow tests plus
    `git diff --check`, and record the work-log entry. The guard test pins the
    checklist and the stricter AGENTS.md fallback. This is docs/test only and
    does not decide backlog items, run research/campaigns, fetch market data,
    close proof, authorize implementation, or mutate runtime state.
    2026-07-29: operator reporting read-only contract regression guard is ready
    for independent review. `tests/test_operator_reporting_read_only_contract.py`
    pins that backlog/proof/bundle/next-action planning reports remain
    read-only/planning-only/non-mutating, and that research status reports are
    not campaign evidence, execution inputs, or promotion evidence. This is
    tests-only and does not change runtime code, decide backlog items, run
    research/campaigns, fetch market data, close proof, authorize
    implementation, or mutate runtime state.
    2026-07-29: operator reporting backlog/work-log synchronization guard is
    ready for independent review. `tests/test_operator_reporting_backlog_worklog_sync.py`
    now pins that the recent operator-reporting backlog notes have matching
    work-log entries, including this synchronization guard itself. This is
    tests-only plus backlog/work-log text and does not change runtime code,
    decide backlog items, run research/campaigns, fetch market data, close
    proof, authorize implementation, or mutate runtime state.
    2026-08-11: operator check-in and GitHub auth alignment is ready for
    independent review. `docs/ROADMAP_TRACKING_CHECKLIST.md` now defines the
    generic read-only check-in sequence (`git status --short --branch`,
    `make operator-status-json`, optional bounded `operator-next-actions`) and
    `docs/GITHUB_AUTH_RUNBOOK.md` documents the local GitHub CLI HTTPS/browser
    recovery path, token-handling boundary, and separation from the ChatGPT
    Codex Connector/GitHub app auth surface. Tests pin roadmap linkage,
    source-doc counts, token boundaries, and the no-campaign/no-market/no-auth
    repair boundary unless explicitly requested. This is docs/test/status
    alignment only and does not change command behavior, credentials, remotes,
    branch protection, campaigns, proof closure, market-data fetches,
    authorization, or runtime state.
    2026-07-29: medium-lane read-only command status is ready for independent
    review. `services.analytics.operator_read_only_command_status` and
    `scripts/report_operator_read_only_command_status.py` inventory the
    existing campaign planners, gate diagnostics, optional operator reports,
    host diagnostics, and host status wrappers without running them. The report
    is wired into `operator-status` and `operator-next-actions` through a new
    `operator_read_only` section / `operator_read_only_command` action lane,
    with focused filters for medium-lane item and command id. This remains
    planning/status only: it does not run commands, campaigns, market-data
    fetches, proof closure, authorization, or runtime mutation.
    2026-07-29: operator-reporting lane-map refresh is ready for independent
    review. `docs/BACKLOG_EXECUTION_LANES.md` now records that the
    operator-reporting selector stack is already covered by dedicated
    read-only contract and backlog/work-log synchronization guards, and tells
    future batches not to rebuild that stack unless current source lacks it.
    This is docs/test only and does not change runtime code, decide backlog
    items, run research/campaigns, fetch market data, close proof, authorize
    implementation, or mutate runtime state.
    2026-07-29: operator research-artifact action surfacing is ready for
    independent review. `operator-status` now includes a
    `research_artifact` section backed by the accepted research artifact
    inventory, and `operator-next-actions` exposes missing/malformed research
    artifacts through a `research_artifact` action lane. Make/CLI filters
    allow focused views by artifact lane or artifact id
    (`OPERATOR_STATUS_RESEARCH_ARTIFACT_LANE`,
    `OPERATOR_STATUS_RESEARCH_ARTIFACT_ID`,
    `OPERATOR_NEXT_ACTIONS_RESEARCH_ARTIFACT_LANE`,
    `OPERATOR_NEXT_ACTIONS_RESEARCH_ARTIFACT_ID`). This remains read-only
    planning/status only: it does not run research jobs, generate artifacts,
    fetch market data, change strategy/campaign/gate state, close proof,
    authorize implementation, or mutate runtime state.
    2026-07-29: explicit single-symbol paper-gate policy documentation is
    ready for independent review. `docs/strategies/paper_universe_widening_decision_2026-07-04.md`
    now states that canonical promotion evidence is single-symbol-only until a
    reviewed reconsideration packet changes that policy; multi-symbol paper
    runs may be separate research/challenger evidence, but must not contribute
    round trips to the canonical `es_daily_trend_v1` promotion gate. This is
    docs/test only and does not change runtime code, decide backlog items, run
    research/campaigns, fetch market data, close proof, authorize
    implementation, or mutate runtime state.
19. Clarify repo identity in public/operator docs. Until live expectancy is
    proven, describe CryptKeep as a profit-measurement and evidence-generation
    lab, not a profitable trading bot. This keeps strategy discovery,
    archive-backed research, shadow cost measurement, and stop criteria ahead
    of dashboard/product polish. 2026-07-03: `docs/PROJECT_IDENTITY_AND_SCOPE.md`
    defines the current identity, and `docs/GOLDEN_PATH.md` /
    `docs/OBJECTIVE.md` now link that scope.
    2026-07-21: public `README.md` now states the same boundary directly and
    links `docs/PROJECT_IDENTITY_AND_SCOPE.md`, so the repository entry point
    no longer relies on operator docs alone for this identity warning.
    2026-07-22: executable project-identity scope guard is ready for
    independent review. `tests/test_project_identity_scope.py` pins the
    evidence-lab identity, unproven-capability list, near-term priorities,
    public description, and cross-links from README, GOLDEN_PATH, OBJECTIVE,
    and product-surface triage docs. This is docs/test only and does not
    change runtime behavior.
20. Harden AI-copilot context access and provider-data governance before
    enabling external LLM summaries as a normal operator path.
    `services/ai_copilot/context_collector.py::_safe_sqlite_query` currently
    accepts caller-provided SQL on a normal SQLite connection; today's callers
    are hardcoded reads, but the read-only assumption is not enforced. Open
    SQLite databases in read-only mode, keep the query surface allowlisted or
    internal-only, and add a small regression proving write SQL cannot mutate
    the source DB. Also document what runtime fields may be sent to external
    LLM providers when `use_ai=true`, and keep `services/ai_copilot/pr_reviewer`
    advisory/non-blocking unless a separate prompt-injection-resistant review
    design is accepted. 2026-07-04: provider-data disclosure boundary is
    documented in `docs/AI_COPILOT_OPERATING_RULES.md`, including allowed
    summary fields, forbidden secret/account/config payloads, and advisory-only
    constraints. 2026-07-04: SQLite context-access implementation proof is
    accepted: AI-copilot incident context queries now use SQLite read-only URI
    connections, reject non-`SELECT` SQL, do not create missing DB files, and
    include a regression proving rejected write SQL does not mutate the source
    DB. Remaining work: any future provider expansion must stay within the
    documented payload boundary.
    2026-07-21: current local implementation gap is closed. Remaining scope is
    future-change governance only: new external providers, provider payload
    fields, or prompt-injection-resistant review authority need separate
    accepted design before becoming normal operator paths.
    2026-07-22: executable AI-copilot operating-rules guard is ready for
    independent review. `tests/test_ai_copilot_operating_rules_guard.py` pins
    deterministic-core authority, provider allow-list governance,
    allowed/forbidden provider payload families, advisory-only provider
    summaries, and the accepted data-disclosure decision requirement. This is
    docs/test only and does not change AI provider behavior or runtime access.
21. Add a Jarvis-like Operator Briefing and Guidance Agent as an advisory-only
    AI layer. The goal is to reduce operator interaction by producing a regular
    evidence-backed brief over campaign health, gate progress, host/data
    freshness, CI/PR state, cost/PnL warnings, research-artifact changes, and
    recommended next actions. Scope boundaries: the assistant may summarize,
    rank, recommend, draft PRs/runbooks, and ask for approval; it must not move
    capital, change live risk, promote strategies, start/stop campaigns, mutate
    manifests/configs, or alter execution/routing policy without explicit
    operator approval and the existing deterministic gates. Acceptance criteria:
    define the briefing schema, evidence sources, recommendation confidence
    labels, alert/escalation thresholds, audit logging, and a read-only command
    that emits a daily/operator-on-demand brief from existing status reports.
    Keep this as "autonomous analyst/operator assistant," not "autonomous
    trader." Any future capital-authority expansion requires a separate
    high-risk design review.
    2026-08-28: current implementation status is accepted for the first
    read-only slice. `services/ai_copilot/operator_briefing.py`,
    `scripts/report_operator_briefing.py`, `make operator-briefing`,
    `make operator-briefing-json`, and `make record-operator-briefing`
    aggregate existing operator status,
    next-action, paper-gate velocity, paper-campaign, and cost-assumption
    reports into an advisory briefing. The payload carries `schema_version`,
    source-status rows, campaign/gate/cost/action summaries, recommendation
    priority/confidence labels, and explicit boundary flags for report mode:
    `read_only=true`, `advisory_only=true`, `capital_authority=none`,
    `does_not_mutate_state=true`, `does_not_run_campaigns=true`,
    `does_not_start_or_stop_campaigns=true`, `does_not_fetch_market_data=true`,
    `does_not_change_config=true`, and `does_not_promote_strategies=true`.
    SHOWN verification in the work log: targeted operator-briefing/script-index/
    AI-copilot guard tests passed, and `make operator-briefing-json` executed
    successfully against `configs/paper_evidence_campaigns.laptop.json`.
    The recording target writes latest and timestamped JSON/Markdown artifacts
    under `.cbp_state/data/operator_briefing/` for daily/on-demand checkpoints
    and reports `artifact_write_requested=true`,
    `does_not_mutate_runtime_state=true`, and
    `mutates_only_operator_briefing_artifacts=true`; it does not change
    campaigns, gates, configs, strategy promotion, execution, or routing.
    The briefing recommendation logic treats scheduled daily `idle` /
    `waiting_for_next_day` campaigns as non-attention state so the assistant
    does not invent a restore action after a normal daily evidence run.
    Remaining future scope: scheduling/notification cadence, richer host/CI/
    research-artifact ingestion, and any PR/runbook drafting workflow remain
    advisory-only follow-ups; no capital authority is granted by this item.
22. Bring permanently ignored CI tests back under an explicit policy. Current
    CI invokes pytest with four `--ignore` entries:
    `tests/test_symbol_scanner.py`, `tests/test_dashboard_view_data.py`,
    `tests/test_dashboard_page_runtime.py`, and
    `tests/test_dashboard_home_digest.py`. Either make them CI-safe, move them
    behind a named optional job with documented prerequisites, or replace them
    with smaller CI-covered regression slices. Tests that only run locally are
    a drift channel for dashboard and symbol-scanner behavior. 2026-07-03:
    policy is documented in `docs/CI_IGNORED_TEST_POLICY.md`; actual CI
    behavior is unchanged. 2026-07-04: `make test-ci-ignored` is added as the
    named optional local job for the exact ignored slice. CI behavior remains
    unchanged; future work is to make these tests CI-safe, split them into
    smaller CI-covered regressions, or move them to an explicit optional CI job.
    2026-07-11: implementation proof is ready for independent review for the
    optional CI lane: `.github/workflows/ci-ignored-tests.yml` adds a
    `workflow_dispatch`-only **Optional Ignored Tests** job that runs
    `make test-ci-ignored`. It is deliberately not triggered on
    `pull_request` or `push`, so required CI behavior remains unchanged.
    Remaining work: make the four ignored tests CI-safe, split them into
    smaller required regressions, or retire unsupported surfaces.
    2026-07-15: closure proof is ready for independent review. The formerly
    ignored slice now passes locally (`90 passed in 2.20s`), required GitHub CI
    no longer passes `--ignore` for those files, and `make test-fast` /
    `make test-full` run the full `tests/` tree without excluding dashboard or
    symbol-scanner tests (`make test-fast`: `2859 passed, 64 skipped`).
    `tests/test_ci_ignored_tests_policy.py` now guards against reintroducing
    those ignores. The manual workflow/target remain only as a focused
    diagnostic slice, not as substitute coverage.
    2026-07-21: current source confirms the closure state: required CI,
    `make test-fast`, and `make test-full` no longer carry permanent ignores
    for the four files; `.github/workflows/ci-ignored-tests.yml` remains manual
    `workflow_dispatch` only; `tests/test_ci_ignored_tests_policy.py` is the
    regression guard. Remaining work is future hygiene only: do not reintroduce
    hidden permanent ignores without a reviewed policy update.
23. Decide retention policy for evidence, snapshot, status, and runtime stores
    before server operation accumulates unbounded state. Prior audits found
    pruning/DELETE behavior only in narrow strategy-state and desktop logging
    surfaces; evidence logs, snapshots, status files, and SQLite stores mostly
    grow indefinitely. "Keep forever" is acceptable if explicit, backed by disk
    monitoring and backup strategy; otherwise define retention windows,
    archival/export rules, and deletion safety checks. 2026-07-03: baseline
    paper/research retention policy is written in `docs/RETENTION_POLICY.md`;
    server-specific disk, backup, restore, and alert thresholds remain open
    before canonical server operation. 2026-07-04: retention policy now links
    the current Hetzner server threshold baseline from `docs/HETZNER_PAPER_HOST.md`
    including `/srv/cryptkeep/backups`, minimum 2 GiB free space, minimum
    10,000 free inodes, backup age, UTC/NTP sync, and restore-test status.
    Remaining proof: fresh backup/restore drill evidence for any future
    canonical server/capped-live launch packet.
    2026-07-21: current local policy gap is closed. `docs/RETENTION_POLICY.md`
    defines default keep/rotate/must-not-keep families and links Hetzner paper
    host thresholds. Remaining work is operator evidence for future launch
    packets: fresh backup/restore drill, backup-artifact secrets scan, and
    host-specific storage proof.
    2026-07-22: executable retention-policy scope guard is ready for
    independent review. `tests/test_retention_policy_scope.py` pins the
    keep/rotate/must-not-keep families, pruning safety requirements, server
    threshold baseline, and capped-live caveat. This is docs/test only and
    does not change runtime behavior; future launch-packet host evidence
    remains open.
24. Turn paper diagnostics and loss replay into a scheduled strategy-review
    ritual. Tooling exists through `scripts/report_paper_run_diagnostics.py`,
    `scripts/dev/replay_paper_losses.py`, and the AI copilot
    `paper_loss_replay` job, but the repo does not yet define a weekly
    operator artifact that reviews wins/losses, records lessons, and updates
    `services/strategies/hypotheses.py` / `docs/strategies/hypotheses.md`
    invalidation conditions. Add a `make` target or runbook step that produces
    a dated read-only review artifact from the current paper journal, links it
    from the work log or checkpoint docs, and keeps conclusions advisory until
    a separate governed config/code change is accepted. 2026-07-03: runbook
    step is documented in `docs/STRATEGY_REVIEW_RITUAL.md`; no scheduler or
    `make` target is added in this docs-only pass. 2026-07-04: `make
    strategy-review` is added as an operator-run target that executes
    `status-paper-all`, paper diagnostics, and loss replay with overridable
    strategy/symbol/limit variables. No automatic scheduler was added.
    2026-07-21: current local implementation gap is closed. `Makefile` exposes
    `make strategy-review`, `docs/STRATEGY_REVIEW_RITUAL.md` documents the
    ritual, and the remaining action is operator cadence: run and file dated
    review artifacts; conclusions remain advisory until a separate governed
    config/code change is accepted.
    2026-07-21: weekly review artifact is recorded in
    `docs/checkpoints/strategy_review_2026_07_21.md`. The run exposed a
    workflow-default mismatch: `make strategy-review` replayed losses for
    `BTC/USD` while the canonical ES journal uses `BTC/USDT`, producing zero
    replay rows. The default `STRATEGY_REVIEW_SYMBOL` is corrected to
    `BTC/USDT`; override variables still support other strategies/symbols.
    2026-07-22: executable strategy-review ritual guard is ready for
    independent review. `tests/test_strategy_review_ritual_guard.py` pins the
    weekly cadence, input/output fields, Makefile target/defaults,
    advisory-only boundary, RUNBOOKS link, and existing dated artifact. This
    is docs/test only and does not change runtime behavior; future review
    cadence remains an operator action.
25. Define stock-options requirements before any equities/options data,
    campaign, gate, or execution work. This is a separate research/governance
    surface from the current crypto paper gate. Required scope: broker/options
    account approval level, OCC/ODD disclosure boundary, OPRA or vendor market
    data entitlement and redistribution limits, option symbology/OSI mapping,
    contract multiplier, expiration/strike/right, option-chain selection,
    bid/ask/spread/liquidity filters, Greeks/IV source and timestamping,
    assignment/exercise/early-exercise handling, corporate actions, trading
    calendar/session rules, margin/buying-power model, max contract/notional
    caps, multi-leg strategy representation, sandbox lifecycle proof, data
    retention/cost caps, and provenance flags. First eligible implementation is
    read-only research artifact generation. Hard boundaries: no stock/options
    order routing, no broker credentials, no paper/shadow/live campaign, no
    promotion evidence, and no shared risk budget with crypto until a separate
    reviewed policy proves account-level isolation and portfolio exposure caps.
    Stock/options research can run in parallel with crypto only as an isolated
    read-only lane with separate state roots, symbols, calendars, data-source
    provenance, cost caps, and operator status; any executable trading path
    must remain separate until broker/account permissions, margin, assignment,
    exercise, and liquidation/close controls are accepted.

## Recently completed
- Pullback Stage 0 readiness report is accepted:
  PR #139 merged as `f26dd965e`, adding
  `scripts/check_pullback_stage0_readiness.py` and
  `services/analytics/pullback_stage0_readiness.py`. The next pullback action
  is the operator-run 15-minute isolated Stage 0 proof, not another readiness
  review.
- Paper-soak status qualification visibility is complete:
  PR #127 merged after checks passed, and the daily soak output now shows
  qualified/all-history closed trades, latest all-history fill, counted,
  incomplete, and rejected evidence fills, and latest qualified close.
- PR #43 AI operator oversight report implementation proof is accepted:
  `docs/checkpoints/pr43_ai_operator_oversight_rebuild_objective_2026_06_28.md`
  records that the current paper-sim monitor is already the wake-up layer and
  that the accepted implementation is a read-only one-shot oversight synthesis
  report, not a second background monitor.
- PR #43 managed multi-symbol runtime is scoped:
  `docs/checkpoints/pr43_managed_multi_symbol_runtime_objective_2026_06_28.md`
  records that the current explicit manifest runtime remains the authority and
  any rebuild must start as a read-only campaign proposal planner, not an
  autonomous campaign starter.
- PR #43 managed multi-symbol runtime implementation proof is accepted:
  `scripts/plan_managed_paper_campaigns.py` and
  `services/analytics/managed_paper_campaign_planner.py` provide a read-only
  proposal planner that writes only proposal artifacts. Campaign manifests,
  state directories, and running collectors are unchanged.
- PR #43 safe-pipeline/startup hardening is scoped:
  `docs/checkpoints/pr43_safe_pipeline_startup_hardening_objective_2026_06_28.md`
  records that the current canonical startup path and existing safe wrappers
  must be audited first; do not add `run_pipeline_safe.py` or alter startup
  behavior unless a current-master gap is reproduced and separately reviewed.
- PR #43 safe-pipeline/startup hardening implementation proof is accepted:
  `scripts/audit_startup_hardening.py` and
  `services/runtime/startup_hardening_audit.py` provide a read-only topology
  audit that writes only startup-audit artifacts. Runtime startup behavior is
  unchanged and any wrapper/topology change remains a separate high-risk task.
- Composite/hybrid long-window research proof is accepted:
  `docs/checkpoints/composite_hybrid_long_window_research_proof_2026_06_27.md`
  records the accepted proof. It fixes the composite warmup/participation gap
  for one long synthetic window, but the candidate remains blocked from paper
  until comparison evidence exists across at least three realized synthetic
  windows.
- Composite/hybrid long-window variant proof is accepted:
  `docs/checkpoints/composite_hybrid_long_window_variant_proof_2026_06_29.md`
  records two additional research-only windows. The composite now has three
  realized synthetic windows, but remains blocked from paper because evidence
  is still synthetic-only and low confidence.
- Shadow spread fresh-record proof is complete:
  `docs/checkpoints/shadow_spread_fresh_record_proof_2026_06_24.md` records
  `9/9` fresh `es_daily_trend_v1` signal records with `spread_bps` and
  `market_quality_reason=ok`.
- PR #43 rebuild follow-up is fully scoped:
  `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md` records
  supervised-soak reporting, durable pipeline log evidence, and AI operator
  oversight as accepted. Managed multi-symbol runtime and safe-pipeline
  wrapper/startup hardening now have separate read-only objective checkpoints;
  implementation remains blocked until those scoped proofs are pursued.
- Paper gate snapshot refreshed:
  `docs/checkpoints/paper_gate_status_2026_06_24.md` records local laptop
  campaigns healthy, canonical `es_daily_trend_v1` at `2/10`
  provenance-qualified round trips, and manual review still required.
- Short-side feasibility audit is complete:
  `docs/checkpoints/short_context_data_feasibility_audit_2026_06_19.md`
  selected the read-only crypto-edge collector as the safe base; PR #72 then
  added accepted open-interest and order-book row support without enabling
  replay, paper short simulation, routing, or execution.
- Short/context readiness report is accepted:
  `docs/checkpoints/short_context_readiness_report_2026_06_29.md` adds a
  read-only check that fails closed unless required `live_public` crypto-edge
  row families are present. It does not contact exchanges or enable replay.
- Hetzner manifest ownership proof is accepted:
  `docs/checkpoints/hetzner_paper_campaign_ownership_proof_2026_06_30.md`
  adds a read-only laptop/Hetzner manifest ownership check. PR #145 merged as
  `6d9f8af66`. It does not SSH, restore, stop, or start collectors.
- Hetzner runtime ownership proof tooling is accepted:
  `docs/checkpoints/hetzner_paper_runtime_ownership_proof_2026_06_30.md`
  adds a read-only check over already-captured laptop and Hetzner status JSON.
  PR #147 merged as `8d75486e`. It does not SSH, restore, stop, or start
  collectors.
- Hetzner storage-health preflight tooling is accepted:
  `docs/checkpoints/hetzner_storage_preflight_proof_2026_07_01.md`
  adds read-only backup-directory, free-space, and free-inode checks to the
  host preflight. It does not SSH, restore, stop, or start collectors.
- Hetzner host-health alerting wrapper is accepted:
  `docs/checkpoints/hetzner_paper_host_health_alerting_proof_2026_07_01.md`
  records a read-only scheduled-safe wrapper that writes a latest host-health
  artifact and uses the local critical-alert fallback on failure. It does not
  SSH, restore, stop, or start collectors.
- Hetzner status reporting is bounded and diagnostic:
  `make status-paper-hetzner` now routes through a timeout-aware read-only
  wrapper, prints bounded stdout/stderr previews on failure, and exposes
  `HETZNER_STATUS_TIMEOUT_SEC` so routine checks do not block indefinitely on
  Tailscale browser-auth or local Tailscale preference failures.
- Hetzner isolated EMA backup restore rehearsal is accepted:
  `docs/deployment_records/hetzner_isolated_challenger_proof_2026_06_20.md`
  records the isolated restore path, manifest verification, evidence counts,
  and active-collector non-interference proof. It does not authorize canonical
  `.cbp_state` migration.
- Read-only candidate outcome report objective is accepted by PR #113:
  `614bae6e7` added the report builder, root CLI, Make target, tests, and
  artifact path; implementation remains read-only and does not enable
  candidate-advisor strategy selection.
- Pipeline exit evidence capture is closed by PR #109:
  `b4db2dba2` added durable supervised process log paths, the implementation
  was independently accepted, and PR #109 merged as `f4b8c296d`.

## Master integration TODO
Master integration completed through
[#49](https://github.com/Ddthomas415/CryptKeep/pull/49) on 2026-06-06.

SHOWN on 2026-06-06:
- PR #49 merged as `5ab9732a2`.
- All eight GitHub checks passed before merge.
- `origin/master...origin/review-stabilized = 0 / 0` after branch alignment.
- The prior 25-file conflict plan is obsolete and closed.

Next action:
- Keep new accepted work on focused branches or `review-stabilized`.
- Integrate future batches through reviewed pull requests without allowing
  `master` and the integration branch to accumulate avoidable divergence.

## Interpretation
Current paper-campaign path:

1. use `make status-paper-all` for the daily check-in: laptop campaign health,
   canonical paper-gate progress, and Hetzner-owned `ema_cross_default` status
2. use `make status-paper-soak` or `make status-paper-hetzner` only when you
   intentionally want one side of the split-host status
3. use `make status-paper-campaigns` only when you need raw laptop process
   restore/status detail
4. wait for `es_daily_trend_v1` to satisfy its active
   `slow_daily_single_symbol_v1` policy, then perform the manual performance
   review

Root-runtime launch path:

1. use the frozen canonical root-runtime path recorded in `docs/checkpoints/root_runtime_scope_record.md`
2. obtain one reachable supported sandbox/testnet venue from the operator environment
3. prove private lifecycle runtime flow on that reachable venue
4. or make an explicit human launch decision accepting the current environment-blocked exception

Already completed on the frozen canonical path:
- private authenticated connectivity for one supported venue
- singular live-mode source of truth
- boundary-governed live lifecycle authority
- hidden-default fencing for the chosen launch path

## Notes
Do not mix:
- launch blockers
- strategy signal-quality / paper-evaluation work
- conditional broader-scope controls
- non-blocking architectural debt

Do not treat raw all-history trade count as promotion progress. The actionable
paper gate is the provenance-qualified count reported by `make
status-paper-all`, `make status-paper-soak`, or
`scripts/check_promotion_gates.py --json`.

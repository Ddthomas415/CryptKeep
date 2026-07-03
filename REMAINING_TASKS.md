# Remaining Tasks

This file is a lightweight index only.

## Current state
The active operating state is paper-evidence collection, not live launch.

SHOWN:
- `master`, `origin/master`, and `review-stabilized` are kept aligned after
  accepted PR merges. Verify the exact current boundary with
  `git rev-parse HEAD origin/master origin/review-stabilized`.
- Laptop-owned paper campaigns are healthy:
  - `es_daily_trend_v1`: `fills=18`, `closed=9`, `pnl=32.1776`
  - `breakout_default`: `fills=12`, `closed=6`, `pnl=-4.1120`
- Hetzner-owned `ema_cross_default` is healthy when checked through the
  Hetzner campaign manifest:
  - `ema_cross_default`: `fills=6`, `closed=3`, `pnl=-0.2678`
  - latest fill: `2026-06-24T00:01:43.601405+00:00`
  - status: `idle`, `waiting_for_next_day`, session evidence already recorded
    for `2026-07-02`
- Codex sandboxed Tailscale may report
  `tailscale_cli_preferences_unavailable`; use a normal operator terminal or
  approved out-of-sandbox status check when Hetzner status must be verified.
- Canonical `es_daily_trend_v1` paper promotion remains blocked at `2/10`
  provenance-qualified round trips, with `8` remaining.
- `make status-paper-gate-qualification` now explains which fills count,
  remain incomplete, or are rejected by provenance checks.
- `make status-paper-soak` and `make status-paper-all` now surface compact
  paper-history qualification details directly in the daily status output.
- Raw all-history currently reports `9` closed trades, but those remain
  diagnostic unless both entry and exit fills carry the required non-sample
  public-OHLCV provenance.

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

## Active Backlog
These are the remaining tasks visible from the accepted checkpoint and planning
documents. Keep implementation scoped; high-risk runtime, launch, strategy, or
deployment work still needs independent review.

1. Continue canonical paper evidence collection until `es_daily_trend_v1`
   reaches 10 provenance-qualified round trips.
2. After the paper gate reaches 10 qualified round trips, write the manual
   strategy performance decision against the accepted baseline. Before relying
   on the expectancy/manual-review gate, populate or explicitly waive the
   currently null `backtest_expectations` fields in
   `configs/strategies/es_daily_trend_v1.yaml` from an accepted parity/backtest
   baseline; otherwise the gate can report count readiness while the strategy
   performance comparison remains unresolved.
   Ground truth must come from the operator-host gate/status command output
   (`make status-paper-gate-qualification` or the equivalent gate JSON), not
   from stale counts copied into this backlog.
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
   zero execution-store fills.
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
   isolated candidate.
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
   open-interest, and basis rows, but adopting OKX into the canonical live
   collector plan still needs an explicit config/docs review. Keep replay
   fixture-only unless
   `make check-short-context-readiness` reports `live_public_replay_ready=true`.
10. Make the strategy registry fail closed before new discovery wiring lands.
   `strategy_registry.compute_signal()` currently falls back to `ema_cross`
   when `strategy.name` is unknown. That is a latent evidence-poisoning risk
   once new names like `funding_extreme` enter campaign configs. Unknown
   strategies should produce a non-actionable error/hold result that is visible
   in session evidence; prove a typo cannot emit an actionable signal.
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
    later evidence proves it is also the best profit candidate.
13. Treat any paper-qualification extension for crypto-edge provenance as
    high-risk gate work. The proof must show an edge-compliant fill is accepted
    and a deliberately stale/mismatched edge fixture is rejected, while existing
    OHLCV qualification fixtures remain unchanged. Also prove the session stays
    paper-only: deployment stage is paper, live intent/order tables are
    unchanged before/after, and the diff does not touch live execution or risk
    gates.
14. Start scheduled read-only crypto-edge collection early once the canonical
    source decision is accepted. Funding and open-interest history mostly
    accrue in real time; OKX funding/OI/basis is a validated read-only
    candidate, but OKX adoption still needs explicit config/docs review and
    Binance derivatives remain unavailable from the current network. If the
    canonical source decision remains open, prioritize the decision itself
    because every idle day loses mostly unrecoverable funding/OI history.
    Treat this as a one-venue research focus until one venue/strategy pair
    proves expectancy; multi-exchange remains a scaling objective, not the
    near-term discovery path. Once the source decision is accepted, collect a
    broader plausible symbol universe than the active campaign needs and, if
    read-only support is available, at least one second venue for comparison.
    Add a cadence-gap alert for the edge collector specifically; a silent
    collector outage burns unrecoverable funding/OI history even when paper
    campaigns keep running.
15. Continue the derivatives/intraday roadmap as read-only data collection and
   replay only until compliance, margin, liquidation, reduce-only, and risk
   controls are proven.
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
18. Maintain the retired-family regression guard. `services/paper`,
    `services/marketdata`, `services/strategy`, `services/strategy_runner`, and
    `services/storage` are retired. Do not reintroduce those packages without a
    new accepted architecture decision.
19. Classify candidate-advisor strategy coverage against the registry.
    `services/signals/candidate_advisor.py` currently allows only a subset of
    `services/strategies/strategy_registry.py::SUPPORTED`; the current drift is
    `breakout_volume`, `gap_fill`, `sma_200_trend`, and
    `volatility_reversal`. Add an explicit exclusion set with rationale, and a
    test that fails whenever a registered strategy is neither advisor-allowed
    nor deliberately excluded. This prevents future discovery wiring from
    silently omitting strategies. Implementation proof is ready for review:
    the advisor now has an explicit exclusion-rationale map, and the test suite
    fails if any registry strategy is not classified as allowed or excluded.
20. Harden the strategy-runner single-instance lock. `_acquire_lock()` in
    `services/execution/strategy_runner.py` is check-then-write and has no
    stale-PID recovery. Replace it with an atomic create path and a stale-lock
    reclamation proof: dead PID lock is reclaimed, and concurrent acquire
    attempts allow exactly one winner.
21. Make sample-mode provenance agree with the actual data source. Current
    paper evidence stamps `ohlcv_sample_mode` from `CBP_USE_SAMPLE_OHLCV`; the
    promotion gate then treats that label as authoritative. Derive the sample
    label from the data source/path used, and make mismatched env/source labels
    fail closed or record explicit sample provenance.
22. Add per-strategy governance configs before promoting additional
    challenger strategies. `configs/strategies/es_daily_trend_v1.yaml` is the
    only full strategy YAML contract today; challenger campaigns currently
    rely heavily on presets/defaults. Before `ema_cross`, `breakout_donchian`,
    `pullback_recovery`, or future context strategies become promotion
    candidates, add strategy-specific config files with backtest expectations,
    risk settings, evidence contract, and manual-review criteria.
23. Wire paper/gate event alerting into the existing alert dispatcher. The
    dispatcher is now used for Hetzner host-health alerts, but paper events
    still depend on manual polling. Add trigger-based alerts for qualified
    round-trip changes, gate-ready transitions, campaign stop/failure,
    evidence-write failure thresholds, and strategy decision changes. Keep the
    first implementation read-only/notification-only.
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
    pressure.
25. Write and rehearse the first-hour paper-to-shadow runbook before the paper
    gate turns green. The runbook should start from fresh gate output, confirm
    baseline/manual-review status, confirm `observe_only` and no live routing,
    promote the stage, start the shadow session, verify shadow signal and
    would-be-fill evidence is being written, verify zero venue orders, and
    record rollback/recovery steps. This is separate from the later launch
    evidence packet; it is the operator checklist for the first shadow hour.
26. Decide whether to widen the paper universe to accelerate qualified evidence.
    The current canonical paper gate is slow because daily strategies on a
    narrow symbol set produce few qualified round trips. Before changing the
    campaign, write a decision record covering candidate symbols, venue/source
    support, provenance qualification, correlation/non-independence caveats,
    per-symbol risk caps, and whether cross-symbol round trips count toward the
    same strategy gate. Do not retroactively count unqualified history or widen
    the universe without preserving the evidence contract.
27. Write a single-operator continuity and absence runbook before shadow or
    server migration becomes the primary operating mode. The system currently
    depends on one operator knowing which checks, hosts, branches, campaigns,
    and recovery procedures matter. Document what continues running if the
    operator is unreachable for a week or a month, what alerts must fire, what
    automatically degrades or stops, who can access the host/repo if needed,
    how to restore from backup, and which actions are explicitly forbidden
    without the operator. This is not a staffing fix; it is the minimum proof
    that the system fails safe without constant human attention.

## Deferred Live-Money Substrate Backlog
These items are not blockers for the current paper/research campaign, but they
must be resolved or explicitly accepted before any capped-live capital exposure.

1. Convert order qty/price/fee/PnL math to `Decimal` with per-venue step size,
   lot size, and min-notional quantization. Start with the order-construction
   boundary quantizer before a full end-to-end migration, and write venue
   golden tests before changing behavior. Blocks capped live.
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
   controls do not read corrupt config through a permissive path.
3. Replace string-match order retry classification with typed `ccxt` exception
   handling. Ambiguous submit timeouts must verify by `clientOrderId` before any
   retry. Add a kill-between-writes submit-path test. Blocks live.
4. Add crash-consistency/fault-injection tests for submit, fill, reconcile, and
   restart. Kill between each side effect and assert reconciler convergence.
   This is a launch-packet companion, not a replacement for restart evidence.
5. Ship server deployment units or retire the stale deployment story. Provide
   systemd units for collector, trader, reconciler, and dashboard, and either
   make Docker compose runnable from this repo or move it behind a documented
   companion-repo pointer. Prefer boring host infrastructure (`systemd`,
   `journald`, bounded status commands, and external dead-man checks) over
   expanding custom supervisor code unless a repo-specific need is shown.
   Blocks server shadow quality and live.
6. Add trading-loop metrics and dead-man alerting. Host health checks are not
   enough; each managed trading loop needs heartbeat metrics and alert-on-absence
   within a defined time window. Include a watchdog proof that each loop checks
   kill/stop signals within a bounded interval and a synthetic alert-delivery
   test so dead email/Slack credentials are detected. Prefer a simple external
   dead-man and push channel such as healthchecks-style pings plus ntfy,
   Telegram, or another operator-visible channel before writing more custom
   alert infrastructure. Blocks shadow/live quality.
7. Write a state-store consolidation decision record before implementation.
   Decide how fills, positions, PnL, intents, and ledgers should move toward one
   transactional schema or explicitly accept the current reconciler-dependent
   multi-store risk. Blocks live.
8. Add a full-state backup/restore drill to the launch evidence packet. Script
   backup of all state DBs and record one executed restore-and-resume rehearsal.
   Blocks live.
9. Surface evidence-write failures in session status. If signal/fill evidence
   writes fail repeatedly while a campaign keeps running, operators should see a
   failure counter and the session should refuse after a bounded threshold
   rather than silently starving the promotion gate.
10. Consolidate config authority before live expansion. The repo still has
    legacy/default `config/` surfaces, strategy/campaign `configs/` surfaces,
    and compatibility normalization between `live.enabled` and
    `execution.live_enabled`. Decide the canonical schema, migrate readers, and
    retire or document compatibility shims so the most dangerous live flag has
    one authority.
11. Add clock/venue-time sanity checks before capped live. Funding age,
    candle boundaries, order timestamps, and reconciliation windows assume UTC
    clock correctness. Add a host/venue skew check and operator-visible status
    before relying on timestamp-sensitive shadow/live evidence.
12. Define the server secrets and rotation model before capped live. Current
    keyring/env handling is adequate for desktop/paper, but server operation
    needs a documented injection path, rotation procedure, and proof that
    secrets are not written to deployment records, logs, or evidence artifacts.
13. Add supply-chain verification to release/CI policy. Requirements are
    pinned, but hash pinning and dependency-audit evidence are not yet a
    visible release gate. Decide whether to add `pip-audit`/hash checks or
    explicitly accept the risk for paper-only operation.
14. Audit operator/action event coverage. Event stores, journals, and fill
    logs exist, but it is not yet shown that every material operator action
    and state transition has a who/what/when trail sufficient for live
    incident review.
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

## Deferred Structure And Research Hygiene
These are lower priority than the active paper/research campaign and live-money
substrate work, but they are concrete enough to keep visible.

1. Resolve `services/runtime/run_mode.py` and
   `services/runtime/bot_process.py`: implement the Phase 218/220 operator
   flow or delete the stubs with a documentation update.
2. Reduce duplicate/twin modules that obscure which code guards money:
   `live_trader_fleet` versus `live_trader_multi`,
   `client_oid.py` versus `client_order_id.py`, and duplicate kill-switch /
   risk-gate modules. Start with a decision record if behavior differs.
3. Extend archive-first backtesting proof to include one walk-forward run over
   the archive producing enough out-of-sample windows to demonstrate research
   depth, not only byte-identical reruns.
4. Rename or document `ws_*` / `market_ws` surfaces before intraday work assumes
   streaming exists. Current accepted direction treats intraday as read-only
   until data cadence and streaming assumptions are proven.
5. Add a backtest-to-paper fill parity property test around the shared fill
   model so paper evidence transferability is tested directly.
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
   mixed buy/sell fills so future changes preserve that invariant.
8. Classify the three paper execution surfaces and retire or document
   non-canonical paths. Audits found `services/paper/main.py`,
   `services/paper_trader/main.py`, and `services/execution/paper_engine.py`
   with different responsibilities. `paper_engine.py` appears to be the
   evidence-aware path; the older runners should either delegate to it, be
   marked retired, or have an explicit supported-use label.
9. Classify dormant or partially wired signal-discovery modules.
   `signal_library`, `market_ranker`, `candidate_engine`,
   `candidate_strategy_mapper`, `trade_type_classifier`, and
   `universe_loader` contain useful discovery/ranking logic, but their active
   production path and intended operator workflow are still unclear. Decide
   which are part of the candidate pipeline, which are research-only, and which
   should be retired.
10. Classify storage orphan modules before more reconciliation work.
    Prior audits flagged unused SQLite stores such as fill reconciler,
    idempotency, and order-tracker variants. Confirm whether each is truly
    unused on current master, then delete, wire, or document it as a retired
    compatibility surface.
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
    operator decision quality.
13. Keep pattern/candlestick strategy research visible but behind the archive
    and paper-evidence gates. Existing code covers pullbacks, gap fills,
    volatility reversals, order-book imbalance, funding, and open interest.
    Missing pattern work includes candlestick confirmation, fair-value gaps,
    order-block style zones, and larger chart-pattern recognition. Treat these
    as research filters or candidate strategies only after archive-first
    backtesting and provenance-qualified paper paths are in place.
14. Triage dashboard/data-page wiring as a product backlog, not a trading gate.
    Several dashboard pages have UI surfaces without confirmed live service
    data behind them. Prioritize operator-critical pages first: gate status,
    paper reconciliation, campaign health, market movers, and copilot reports.
15. Vendor, explicitly integrate, or excise the companion-repo dependency.
    `phase1_research_copilot` has appeared in compose/docs/skip-test context
    during audits. Split-brain repos rot deployment stories. Decide whether the
    companion is a vendored dependency, an external documented prerequisite, or
    retired from the canonical path, then update compose, docs, and tests to
    match.
16. Add risk-tiered governance lanes to the operator workflow. Keep full
    ceremony for high-risk changes touching gates, dispatch, execution,
    secrets, deployment, and live-risk surfaces. Allow a lighter documented
    lane for low-risk docs/tests/reporting changes with clear PR labeling,
    targeted verification, and work-log coverage. The goal is to preserve
    rigor where it protects money while reducing process tax where it only
    delays low-risk cleanup.
17. Define the operational core and quarantine policy. Add a `CORE.md` or
    equivalent decision record that names the modules required for the current
    paper/research/shadow path, plus a quarantine/attic policy for surfaces not
    in that core. Do not move broad directories in one sweep; first classify,
    then retire, delegate, or document.
18. Protect operator attention as a managed resource. Add a decision record or
    runbook rule that caps open audit loops, limits low-value review churn, and
    forces each proactive task to tie back to one of: evidence velocity,
    profitability discovery, cost measurement, safety, recovery, or operator
    wake-up quality.
19. Clarify repo identity in public/operator docs. Until live expectancy is
    proven, describe CryptKeep as a profit-measurement and evidence-generation
    lab, not a profitable trading bot. This keeps strategy discovery,
    archive-backed research, shadow cost measurement, and stop criteria ahead
    of dashboard/product polish.

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
4. wait for `es_daily_trend_v1` to reach 10 provenance-qualified round trips,
   then perform the manual performance review

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

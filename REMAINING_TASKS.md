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
   If archive-first backtesting lands before the manual review, prefer an
   archive-backed multi-year baseline with dataset hashes over any shallow
   single-fetch baseline. Do not populate the expectancy fields from a
   short-window or non-reproducible run unless that limitation is explicitly
   accepted in the decision record.
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
    later evidence proves it is also the best profit candidate. Include a
    shared `regime_context` provider in this context contract. The flagship
    `sma_200_trend` path already computes and enforces
    `es_daily_trend.regime_stability()`; extract that market-state awareness so
    other strategies can consume the same regime facts without duplicating
    logic, while proving current `sma_200_trend` behavior remains unchanged.
    Treat `composite_hybrid` confirmation mode as a context/confirmation
    consumer, not as a standalone live strategy, until archive-backed
    walk-forward evidence and paper provenance justify runtime registration.
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
    campaigns keep running. The first post-decision proof should verify the
    collector schedule on the host, show recent snapshot timestamps, and report
    any cadence gaps before more strategy wiring depends on that history.
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
    the runner before building a second stale-lock mechanism.
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
    risk settings, evidence contract, no-trade filter settings, and
    manual-review criteria. Explicitly verify that each strategy's documented
    no-trade filters are enabled or consciously waived in its campaign config;
    documented discipline that is off in runtime config does not count as
    governed discipline.
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
    pressure. 2026-07-03: baseline policy is written in
    `docs/STRATEGY_STOP_AND_RETIREMENT_POLICY.md`; future strategy promotion
    still requires a dated per-strategy decision record using fresh gate output.
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
    preserving the evidence contract.
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
    implementation proof is ready for independent review: paper buy fees are
    folded into cost basis, sell fees reduce realized proceeds, new fill
    evidence carries `pnl_usd_semantics=net_of_fees`, and targeted tests prove
    a flat round trip with 10 bps fees records negative `pnl_usd` and fails the
    expectancy helper. 2026-07-04: human/operator independent review accepted
    the implementation with risk. Remaining operational proof: verify the
    active campaign config uses realistic fee/slippage values, and segment old
    gross/unknown-semantics evidence during future analysis.
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
    settings prove stable.
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
   2026-07-03 audit update: `services/execution/live_reconciler.py` already has
   a verify-before-retry path for `submit_unknown` intents through
   client-order-id lookup. Remaining work is typed exception classification,
   fault-injection proof around crash-between-writes, and explicit policy for
   the venue-lookup-not-found case.
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
   alert infrastructure. A 2026-07-03 audit found
   `services/process/heartbeat.py::write_heartbeat()` has no callers while
   `services/process/watchdog.py` reads heartbeat state and can arm the kill
   switch / set `HALTING` on staleness. Add heartbeat writes in every managed
   loop that matters for unattended operation: strategy runner, evidence
   service, collectors, live intent consumer, and reconciler. Also wire alert
   dispatch on watchdog trigger and `bot_not_running`, prove host scheduling,
   and fold the status-only `services/admin/watchdog.py` surface into the
   process watchdog or document why both remain. Blocks shadow/live quality.
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
    A 2026-07-03 audit tightened the constraint: current paper-engine limit
    fills are crossing-style only and market fills are full fills, so maker-side
    research must come from shadow would-be-fill records or an explicit engine
    extension, not from current paper-fill behavior.
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
    strategy/evidence/promotion system. Blocks capped live.
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
    reason. Blocks capped live.
18. Add intent TTL before live/shadow consumers are trusted unattended.
    `storage/live_intent_queue_sqlite.py` dequeues and claims queued intents by
    `created_ts ASC`, while current consumers check market snapshot freshness
    but not the intent's own age. A restart after hours or days could submit an
    intent sized and justified by stale context at current prices. Add
    `max_intent_age_sec` with a fail-closed default, mark aged queued/submitting
    intents `expired` with an operator-visible reason, and make the reconciler
    treat `expired` as terminal. Proof: aged-intent fixture expires with zero
    submits; fresh-intent fixture remains eligible.
19. Remove hardcoded reference-price fallbacks from paper pre-submit safety
    checks. `services/execution/paper_engine.py` currently falls back to
    `60000.0` when no limit price, market-quality price, or last price is
    available, and then uses that reference price for notional/safety checks.
    Missing quote/reference data should fail closed with `no_reference_price`
    rather than using a BTC-shaped constant for any symbol. Proof: missing-price
    fixture rejects before safety-cap math; normal quoted paths remain
    unchanged.

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
   2026-07-03 audit map: `services/admin/kill_switch.py` appears to be the
   operational switch state used by scripts/resume/halt flows;
   `services/risk/kill_conditions.py` is the strategy-runner risk-block logic;
   `services/execution/kill_switch.py` is a thin setter wrapper used by one
   script; `services/risk/killswitch.py` has no production importers and should
   be deleted, wired, or explicitly retired.
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
   retired. Follow-up remains for `services/trading_runner/run_trader.py`.
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
   through archive-backed, net-fee, governed activation.
10. Classify storage orphan modules before more reconciliation work.
    Prior audits flagged unused SQLite stores such as fill reconciler,
    idempotency, and order-tracker variants. Confirm whether each is truly
    unused on current master, then delete, wire, or document it as a retired
    compatibility surface. 2026-07-03: classification is documented in
    `docs/architecture/storage_surface_classification.md`; three candidate
    stores remain unwired candidates pending a deeper caller/migration audit.
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
13. Keep pattern/candlestick strategy research visible but behind the archive
    and paper-evidence gates. Existing code covers pullbacks, gap fills,
    volatility reversals, order-book imbalance, funding, and open interest.
    Missing pattern work includes candlestick confirmation, fair-value gaps,
    order-block style zones, and larger chart-pattern recognition. Treat these
    as research filters or candidate strategies only after archive-first
    backtesting and provenance-qualified paper paths are in place. 2026-07-03:
    visible backlog is documented in `docs/research/pattern_strategy_backlog.md`.
14. Triage dashboard/data-page wiring as a product backlog, not a trading gate.
    Several dashboard pages have UI surfaces without confirmed live service
    data behind them. Prioritize operator-critical pages first: gate status,
    paper reconciliation, campaign health, market movers, and copilot reports.
    2026-07-03: priority policy is documented in
    `docs/dashboard/DATA_PAGE_BACKLOG.md`; state-mutating pages still require
    role guards and cannot bypass accepted ceremonies.
15. Vendor, explicitly integrate, or excise the companion-repo dependency.
    `phase1_research_copilot` has appeared in compose/docs/skip-test context
    during audits. Split-brain repos rot deployment stories. Decide whether the
    companion is a vendored dependency, an external documented prerequisite, or
    retired from the canonical path, then update compose, docs, and tests to
    match. 2026-07-03: `docs/COMPANION_REPO_DEPENDENCY.md` classifies it as a
    sidecar/archived companion, not a required root runtime dependency; future
    active use must vendor it or document it as an explicit external
    prerequisite.
16. Add risk-tiered governance lanes to the operator workflow. Keep full
    ceremony for high-risk changes touching gates, dispatch, execution,
    secrets, deployment, and live-risk surfaces. Allow a lighter documented
    lane for low-risk docs/tests/reporting changes with clear PR labeling,
    targeted verification, and work-log coverage. The goal is to preserve
    rigor where it protects money while reducing process tax where it only
    delays low-risk cleanup. 2026-07-03: baseline lane policy is written in
    `docs/OPERATOR_GOVERNANCE_LANES.md`; future work should apply the lane
    label in PRs without weakening AGENTS.md high-risk review rules.
17. Define the operational core and quarantine policy. Add a `CORE.md` or
    equivalent decision record that names the modules required for the current
    paper/research/shadow path, plus a quarantine/attic policy for surfaces not
    in that core. Do not move broad directories in one sweep; first classify,
    then retire, delegate, or document. 2026-07-03: baseline is documented in
    `docs/CORE.md`.
18. Protect operator attention as a managed resource. Add a decision record or
    runbook rule that caps open audit loops, limits low-value review churn, and
    forces each proactive task to tie back to one of: evidence velocity,
    profitability discovery, cost measurement, safety, recovery, or operator
    wake-up quality. 2026-07-03: this rule is captured in
    `docs/OPERATOR_GOVERNANCE_LANES.md` as the operator attention cap.
19. Clarify repo identity in public/operator docs. Until live expectancy is
    proven, describe CryptKeep as a profit-measurement and evidence-generation
    lab, not a profitable trading bot. This keeps strategy discovery,
    archive-backed research, shadow cost measurement, and stop criteria ahead
    of dashboard/product polish. 2026-07-03: `docs/PROJECT_IDENTITY_AND_SCOPE.md`
    defines the current identity, and `docs/GOLDEN_PATH.md` /
    `docs/OBJECTIVE.md` now link that scope.
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
    design is accepted.
21. Bring permanently ignored CI tests back under an explicit policy. Current
    CI invokes pytest with four `--ignore` entries:
    `tests/test_symbol_scanner.py`, `tests/test_dashboard_view_data.py`,
    `tests/test_dashboard_page_runtime.py`, and
    `tests/test_dashboard_home_digest.py`. Either make them CI-safe, move them
    behind a named optional job with documented prerequisites, or replace them
    with smaller CI-covered regression slices. Tests that only run locally are
    a drift channel for dashboard and symbol-scanner behavior. 2026-07-03:
    policy is documented in `docs/CI_IGNORED_TEST_POLICY.md`; actual CI
    behavior is unchanged.
22. Decide retention policy for evidence, snapshot, status, and runtime stores
    before server operation accumulates unbounded state. Prior audits found
    pruning/DELETE behavior only in narrow strategy-state and desktop logging
    surfaces; evidence logs, snapshots, status files, and SQLite stores mostly
    grow indefinitely. "Keep forever" is acceptable if explicit, backed by disk
    monitoring and backup strategy; otherwise define retention windows,
    archival/export rules, and deletion safety checks. 2026-07-03: baseline
    paper/research retention policy is written in `docs/RETENTION_POLICY.md`;
    server-specific disk, backup, restore, and alert thresholds remain open
    before canonical server operation.
23. Turn paper diagnostics and loss replay into a scheduled strategy-review
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
    `make` target is added in this docs-only pass.

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

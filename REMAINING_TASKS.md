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
   numeric-ingestion proof is ready for independent review. `MarketStore` now
   rejects non-positive or non-finite OHLCV timestamps/prices, invalid high/low
   envelopes, and non-finite/negative volume before writing `market_ohlcv`,
   while preserving missing-volume rows. This protects dataset hashes and
   archive-backed walk-forward inputs from malformed bars. 2026-07-14:
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
    touched. Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.
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
   operator action. Docker-compose disposition and host-side installation
   remain open.
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
11. Add clock/venue-time sanity checks before capped live. Funding age,
    candle boundaries, order timestamps, and reconciliation windows assume UTC
    clock correctness. Add a host/venue skew check and operator-visible status
    before relying on timestamp-sensitive shadow/live evidence. 2026-07-04:
    policy is documented in `docs/CLOCK_VENUE_TIME_SANITY_POLICY.md`.
    Remaining capped-live proof: host UTC/NTP status, venue server-time query
    or limitation record, observed skew against threshold, fail-closed behavior
    for excessive skew, and operator-visible status output. 2026-07-10: the
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
14. Audit operator/action event coverage. Event stores, journals, and fill
    logs exist, but it is not yet shown that every material operator action
    and state transition has a who/what/when trail sufficient for live
    incident review. 2026-07-04: coverage policy is documented in
    `docs/OPERATOR_ACTION_AUDIT_COVERAGE.md`. Remaining capped-live proof:
    dashboard/CLI/system/automation coverage matrix, audit-log replay of at
    least one live-arm-to-halt drill, no-secret audit payload scan, and
    fail-closed behavior for critical audit-write failures.
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
    2026-07-16: AI copilot external-provider audit hook is ready for
    independent review. `services.ai_copilot.providers.call_llm` now appends
    best-effort `ai_copilot_external_provider_call` operator events for
    provider attempts, recording provider/model, prompt character counts,
    result, and error metadata without logging system prompts, user prompts,
    incident context, or report content. The coverage matrix moves the AI
    copilot external-provider family from MISSING to PARTIAL. Remaining
    coverage: local-only report writes, provider-governance policy, and any
    future provider path that bypasses `call_llm`.
    2026-07-16: AI copilot local report-write audit hook is ready for
    independent review. Central `services.ai_copilot` report writers now append
    best-effort metadata-only `ai_copilot_report_write` operator events after
    persisted report artifacts are written, recording report type,
    status/severity, and artifact names/count without logging report payloads,
    stdout/stderr, prompts, recommendations, summaries, or artifact contents.
    Remaining coverage: provider-governance policy and any future provider path
    that bypasses `call_llm` or the central report writers.
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
    family from MISSING to PARTIAL. Remaining coverage: user role management
    changes.
    2026-07-16: API credential-rotation operator-event hook is ready for
    independent review. `services.security.credential_store` now appends
    best-effort metadata-only `api_credential_rotation` operator events after
    central keyring set/delete calls, recording exchange, operation, result,
    and stored field names without logging API keys, API secrets, or
    passphrases. The coverage matrix moves API credential rotation from
    MISSING to PARTIAL. Remaining coverage: direct keyring edits,
    environment-based credential changes, server injection/rotation drills,
    and fail-closed audit-write policy.
    2026-07-16: strategy stage-transition operator-event hook is ready for
    independent review. `services.control.deployment_stage` now appends
    best-effort `strategy_stage_transition` events for central promote, demote,
    and safe-degraded transitions, carrying actor, strategy id, from/to stage,
    reason, timestamp, and transition result. The coverage matrix moves
    strategy stage promotion/demotion from MISSING to PARTIAL. Remaining proof:
    promotion audit-write fail-closed policy and host-side promotion proof.
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
5. Add a backtest-to-paper fill parity property test around the shared fill
   model so paper evidence transferability is tested directly. 2026-07-04:
   parity guard added for paper market buy/sell fills: paper engine fill price
   and fee must match `services.execution.fill_model.apply_fee_slippage()` for
   the same mid price, side, qty, fee bps, and slippage bps.
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
   features.
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
    2026-07-04: targeted caller audit found no visible production source
    importers for `fill_reconciler_store_sqlite.py`,
    `order_idempotency_sqlite.py`, or `order_tracker_store_sqlite.py`; matches
    are the modules themselves and prior docs/audit artifacts. 2026-07-04:
    disposition decision is recorded in
    `docs/architecture/storage_surface_classification.md`: explicitly retain
    the three schemas as quarantined retained schemas during paper/research,
    do not wire new callers, and defer deletion/migration until the state-store
    consolidation migration packet decides whether any schema/data is needed.
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
    `docs/CORE.md`. 2026-07-04: `docs/CORE.md`, `docs/ARCHITECTURE.md`, and
    `docs/REPO_LAYOUT.md` now link the paper execution, safety, storage,
    websocket, and signal-discovery classification records so the quarantine
    policy points at concrete disposition docs.
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
    design is accepted. 2026-07-04: provider-data disclosure boundary is
    documented in `docs/AI_COPILOT_OPERATING_RULES.md`, including allowed
    summary fields, forbidden secret/account/config payloads, and advisory-only
    constraints. 2026-07-04: SQLite context-access implementation proof is
    accepted: AI-copilot incident context queries now use SQLite read-only URI
    connections, reject non-`SELECT` SQL, do not create missing DB files, and
    include a regression proving rejected write SQL does not mutate the source
    DB. Remaining work: any future provider expansion must stay within the
    documented payload boundary.
21. Bring permanently ignored CI tests back under an explicit policy. Current
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
22. Decide retention policy for evidence, snapshot, status, and runtime stores
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
    `make` target is added in this docs-only pass. 2026-07-04: `make
    strategy-review` is added as an operator-run target that executes
    `status-paper-all`, paper diagnostics, and loss replay with overridable
    strategy/symbol/limit variables. No automatic scheduler was added.

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

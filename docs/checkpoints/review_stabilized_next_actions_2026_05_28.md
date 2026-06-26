# Review Stabilized Next Actions - 2026-05-28

This checkpoint records the proactive task list raised during the 2026-05-28
audit discussion. It is intentionally separate from the work log: the work log
records completed work; this file records pending work and ordering.

## Evidence Basis

SHOWN:
- Current branch is `review-stabilized`.
- Local comparison `master...review-stabilized` reported `64 / 83` when this
  checkpoint was first created.
- Later 2026-05-28 inspection reported `64 / 84` after the work-log checkpoint
  commit.
- `REMAINING_TASKS.md` documents the 2026-05-25 master integration blocker and
  25 conflicted files from a no-commit test merge.
- A local integration worktree exists at
  `/private/tmp/cryptkeep-master-review-stabilized-integration`.
- That worktree is on `codex/master-review-stabilized-integration`.
- The integration branch was refreshed with latest `review-stabilized` and
  pushed to GitHub as PR #44:
  `https://github.com/Ddthomas415/CryptKeep/pull/44`.
- Latest integration worktree commit shown:
  `8602c509f Merge branch 'review-stabilized' into codex/master-review-stabilized-integration`.
- PR #10 was verified open, verified superseded by `6cc95f678`, and closed on
  2026-05-28 with an audit comment.
- PR #10 state was verified as `CLOSED` after closure.
- 2026-06-19 audit verified current open PR state:
  - PR #42 is draft, dirty against `master`, and 27 branch-only commits remain
    by patch-equivalence comparison.
  - PR #43 is not draft, dirty against `master`, and 98 branch-only commits
    remain by patch-equivalence comparison.
  - PR #3 is not draft, dirty against `master`, and 54 branch-only commits
    remain by patch-equivalence comparison.

CLAIMED:
- Auditor reported `review-stabilized` as 83 commits ahead of master and 59
  behind.
- Auditor reported PR #42 and PR #43 as open/draft or held upstream PRs.

UNVERIFIED:
- PR #42, PR #43, and PR #3 have not been rebuilt or independently reviewed
  against current `master`.
- PR #44 has not received full-suite or independent merge review in this
  checkpoint file.

## Priority 1 - Master Integration

Status: complete. PR #49 independently reviewed, accepted, and merged on
2026-06-06 as `5ab9732a2`

Why it matters:
- `review-stabilized` is clean and accepted, but `master` remains behind.
- Audit work is not in the canonical production line until master receives it.
- The old conflict-resolution branch no longer reflects the current topology.
- SHOWN on 2026-06-06: `origin/master` is an ancestor of
  `origin/review-stabilized`, with no master-only commits.
- SHOWN: PR #49 directly proposes `review-stabilized` into `master`.

Next action:
- Keep future integration batches focused and preserve branch alignment after
  each accepted merge.

Verification:
- SHOWN: all eight GitHub checks passed on the accepted PR head.
- SHOWN: PR #49 state is `MERGED`.
- SHOWN: `origin/master...origin/review-stabilized = 0 / 0` after
  fast-forwarding the integration branch to the merge commit.

Risk:
- CLOSED: the accepted aggregate is canonical on `master`; future changes
  require their own review cycle.

## Priority 2 - Work Log Accuracy

Status: complete as of `507d9f05d`

Required fixes:
- Update `84aa49113` acceptance state to `ACCEPTED`.
- Add missing `e06d49371` work-log entry.
- Replace vague "accepted by later review" wording with reviewer/date/session
  references.
- Fix ambiguous `9f90a8d2e` acceptance wording.

Risk:
- MEDIUM: audit-trail credibility.

## Priority 3 - Close Superseded PR #10

Status: complete as of 2026-05-28

Shown context:
- PR #10 was open against `review-stabilized` from
  `audit/defect-05-null-overwrite`.
- PR #10 contained `5858dcc1969ec68763a11dc85fe589ca7de5a755`.
- The exact PR commit was not an ancestor of `review-stabilized`.
- The hardened equivalent fix `6cc95f678` is an ancestor of
  `review-stabilized`.
- Current code contains COALESCE preservation for paper and live queue order-id
  fields.

Verification:
- `rg -n "COALESCE\\(\\?, client_order_id\\)|COALESCE\\(\\?, linked_order_id\\)|COALESCE\\(\\?, exchange_order_id\\)" storage/intent_queue_sqlite.py storage/live_intent_queue_sqlite.py`
  - SHOWN: matched the current paper/live queue preservation paths.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_queue_update_status_preserves_ids.py`
  - SHOWN: `2 passed in 0.08s`.

Outcome:
- PR #10 closed with a comment referencing `6cc95f678` and the targeted
  verification result.

Risk:
- CLOSED: repository hygiene and audit-noise reduction complete.

## Priority 4 - Keep Paper Campaign Running

Status: healthy as of 2026-05-28 check

Current gate state:
- 3 more round trips needed.
- 7 more calendar days needed.
- Daily evidence collector is alive and idle because the 2026-05-28 UTC
  session already completed.
- Paper sim monitor is expected to stop after the daily collector run; the
  collector restarts it during evidence collection and seeds watches.

Verification:
- `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: `pid_alive=true`, `status=idle`, `reason=waiting_for_next_day`,
    `last_completed_day=2026-05-28`.
- `./.venv/bin/python scripts/run_paper_sim_monitor.py --status`
  - SHOWN: monitor `status=stopped`, `recommendation=continue`, watches active,
    last campaign reports written on 2026-05-28.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: `23/30 days`, `7/10 round trips`, `manual_review_required=true`.

Next action:
- Continue daily evidence collection.
- Re-check after each UTC session or when a watch report fires.

Risk:
- MEDIUM: operational interruption could waste the shortened paper-gate window.

## Priority 5 - Prepare Shadow Gate Before Paper Clears

Status: complete as of 2026-06-24; fresh signal records observed with
`spread_bps`

Why it matters:
- Paper gate is close enough that shadow tooling should be validated before the
  paper gate clears.
- Shadow requires signal logging against live market data and slippage/depth
  validation.

What was found:
- SHOWN: `./.venv/bin/python scripts/check_promotion_gates.py --stage shadow --json`
  reported `All signals logged with spread/depth data` as failed across
  `33251` historical signals.
- SHOWN: historical signal records contained no spread/depth keys.

What changed:
- Public-OHLCV signal evidence now includes market-quality fields from the
  local tick snapshot path, including `spread_bps` when fresh bid/ask data is
  available.
- The shadow gate now recognizes `spread_bps` and explicit depth keys instead
  of only literal `spread` or `depth`.

Verification:
- `python3 -c "... _market_quality_evidence_extra('coinbase','BTC/USDT') ..."`
  - SHOWN: current idle tick data was stale, so no `spread_bps` was emitted in
    the idle probe.
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_check_promotion_gates.py`
  - SHOWN: `52 passed in 0.80s`.

Acceptance evidence:
- `9f0dd8b0c` implemented market-quality evidence stamping for future
  public-OHLCV signal records and shadow-gate recognition of `spread_bps`.
- `4c414b256` recorded operator acceptance of the shadow spread evidence fix.
- `64bd86e54` later merged PR #51 to scope shadow-gate readiness to active
  shadow-stage evidence.
- `docs/checkpoints/shadow_spread_fresh_record_proof_2026_06_24.md` records
  fresh `es_daily_trend_v1` public-OHLCV records with spread evidence.

Fresh-record proof:
- SHOWN: `.cbp_state/data/evidence/es_daily_trend_v1/signal_2026-06-24.jsonl`
  contains `9` signal records.
- SHOWN: all `9` records include `spread_bps`.
- SHOWN: all `9` records include `market_quality_reason=ok`.

Next action:
- Do not treat historical unstamped signal records as sufficient shadow proof.
- When the strategy enters shadow stage, collect separate shadow-stage signal
  logs and evaluate the full shadow checklist against those records.

Risk:
- HIGH: promotion path and live-adjacent operational readiness. This closes the
  fresh-record stamping observation only; it does not complete a future
  shadow-stage campaign.

## Priority 6 - `daily_loss_halt_pct` Wiring

Status: complete. Independently reviewed and accepted by operator on
2026-06-04.

Why it matters:
- `configs/strategies/es_daily_trend_v1.yaml` declares `daily_loss_halt_pct`.
- The spec says runtime enforcement currently lives in a separate absolute-USD
  service.
- This is a safety-control discrepancy unless explicitly wired or accepted.

Next action:
- Keep the config percentage target and runtime USD limit manually consistent
  until an accepted equity-to-USD translation exists.

Risk:
- HIGH: risk controls and safety enforcement.

## Priority 7 - Strategy Performance Decision

Status: baseline populated; current paper performance is machine-blocking

Why it matters:
- `manual_review_required=true` now persists until observed win rate and average
  win/loss are compared against backtest expectations.
- Paper gate progress should not be confused with strategy profitability.
- SHOWN: the 2026-06-05 baseline audit found no usable machine-readable
  backtest baseline in the visible repo state.
- SHOWN: the committed generic daily sample produced no closed trades for
  `sma_200_trend`.
- SHOWN: the local Coinbase snapshot produced no trades and is not a committed
  reproducible baseline artifact.
- SHOWN: the deterministic SMA-200 round-trip fixture produced one closed trade
  but is synthetic CI mechanics, not a profitability expectation source.
- SHOWN: a 2026-06-04 candidate baseline was generated with Coinbase `BTC/USD`
  historical daily bars while preserving `BTC/USDT` as the strategy/report
  symbol.
- SHOWN: that candidate produced `31` closed trades and `baseline_ready=true`.
- SHOWN: raw-dollar average win/loss values were not comparable to paper sizing.
- SHOWN: the normalized replacement uses net PnL divided by entry notional and
  preserves the same `31` closed trades.
- SHOWN: the normalized baseline and disclosed Coinbase `BTC/USD` data basis
  were independently accepted and populated.
- SHOWN: current paper comparison passes average winning return but blocks on
  win rate and average losing return drift.
- SHOWN: the apparent `7/10` progress mixed unstamped legacy fills with
  latest-window public provenance. None of the seven raw round trips has
  matching provenance on both entry and exit.

Next action:
- Collect 10 provenance-qualified round trips without changing the accepted
  baseline or tolerance. The qualified counter starts at zero; the seven raw
  journal round trips remain diagnostic history.
- Treat the prior win-rate and exit-loss comparison as unqualified until enough
  matched daily-public round trips exist.
- After the paper gate reaches 10 round trips, write the strategy performance
  decision using the machine comparison and exit-path investigation.

Reference:
- `docs/checkpoints/es_daily_trend_backtest_baseline_audit_2026_06_05.md`
- `docs/checkpoints/es_daily_trend_backtest_baseline_candidate_2026_06_04.md`
- `docs/checkpoints/es_daily_trend_normalized_baseline_candidate_2026_06_04.md`

Risk:
- HIGH: financial strategy evaluation.

## Priority 8 - PR #42 Decision

Status: complete as of 2026-06-19; PR #42 closed as superseded

Current evidence:
- SHOWN on 2026-06-19: PR #42 remains a draft branch targeting `master`.
- SHOWN: PR #42 merge state is `DIRTY`.
- SHOWN: `origin/master...origin/codex/runtime-hardening-ai-alert-monitor`
  reports `224 / 27`.
- SHOWN: the 27 branch-only commits are the early runtime-hardening, AI alert
  monitor, multi-symbol, and safe-pipeline commits that also appear in PR #43's
  larger branch history.
- SHOWN: `docs/checkpoints/pr43_operator_observability_disposition_2026_06_19.md`
  treats PR #42 as superseded by the broader PR #43 disposition path.
- SHOWN: PR #42 was closed on 2026-06-19 after the accepted PR #43
  disposition checkpoint was merged via PR #64.

Next action:
- Do not reopen or merge PR #42 directly.
- Rebuild only accepted PR #43 disposition `rebuild` groups from current
  `master`.

Risk:
- MEDIUM to HIGH: upstream branch divergence and background-job/runtime
  supervision behavior.

## Priority 9 - Rebuild PR #43 From Clean Base

Status: complete as of 2026-06-19; PR #43 closed after accepted disposition

Current evidence:
- SHOWN on 2026-06-19: PR #43 targets `master`, is not draft, and has merge
  state `DIRTY`.
- SHOWN: `origin/master...origin/fix/p1-pre-live` reports `224 / 98`.
- SHOWN: the branch touches high-risk surfaces including live execution,
  auth/dashboard save gates, runtime supervision, AI alert monitoring, paper
  simulation monitoring, managed symbol selection, and pipeline wrappers.
- SHOWN: much of the desired paper-monitoring concept has since been rebuilt on
  `review-stabilized`; remaining PR #43 content must be extracted, not merged
  wholesale.
- SHOWN: `docs/checkpoints/pr43_operator_observability_disposition_2026_06_19.md`
  accounts for all 98 raw branch-only commits and separates `rebuild`,
  `superseded`, and `drop` decisions.
- SHOWN: PR #43 was closed on 2026-06-19 after the accepted disposition
  checkpoint was merged via PR #64.
- SHOWN: no open PRs remained after PR #42 and PR #43 were closed.

Current follow-up status:
- SHOWN: supervised-soak reporting was rebuilt and accepted through
  `scripts/report_supervised_soak_status.py` and
  `tests/test_report_supervised_soak_status.py`.
- SHOWN: durable supervised pipeline log evidence was rebuilt and accepted by
  PR #109.
- SHOWN: the current source tree still does not contain the old PR #43 AI
  alert/oversight source files, managed-symbol source files, or
  `scripts/run_pipeline_safe.py`.

Next action:
- Rebuild only one still-open candidate group at a time from current `master`:
  1. AI alert monitor and operator oversight, only if current paper-sim watches
     and reports are insufficient for operator wake-up needs.
  2. Managed multi-symbol paper runtime, only after campaign ownership and
     evidence isolation are explicitly scoped.
  3. Safe pipeline wrapper and startup hardening, only after a current-master
     startup or fail-closed gap is reproduced.
- Keep live execution, auth gates, and unrelated runtime supervisor changes out
  of the same PR unless they are required for the specific rebuild.
- See
  `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md`.

Risk:
- HIGH: the old branch mixes operator observability with live execution and
  fail-closed behavior. Direct merge is not acceptable.

## Priority 10 - CI Fixture For `sma_200_trend`

Status: complete as of `e4ad5d99c`

Why it matters:
- Sample mode can prove entry/fill mechanics but not a deterministic
  `sma_200_trend` exit.
- A 220-bar synthetic OHLCV fixture can cover 200 warmup bars plus engineered
  entry and exit windows.

Next action:
- Keep `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json` and its parity
  test aligned with future `sma_200_trend` semantics.
- Do not treat the synthetic fixture as promotion-gate or profitability
  evidence.

Risk:
- CLOSED: CI repeatability and strategy-path coverage task complete.

## Priority 11 - Higher-Turnover Daily/Weekly Strategy Plan

Status: implementation-proof-ready as of 2026-06-05

Why it matters:
- `sma_200_trend` is a slow-turnover daily trend strategy. It validates the
  pipeline, but it is not designed to produce frequent weekly income.
- The current repo already contains higher-turnover candidates such as
  `ema_cross`, `breakout_donchian`, and `mean_reversion_rsi`; they need real
  paper evidence before any promotion decision.

Next action:
- Follow `docs/checkpoints/ema_cross_challenger_plan_2026_06_05.md`.
- Start with the isolated Stage 0 one-shot proof for `ema_cross_default` using
  a separate `CBP_STATE_DIR`.
- Do not start a persistent challenger daily loop until Stage 0 proves clean
  startup, status, artifact routing, and state isolation.
- Keep `breakout_donchian` as the next challenger candidate if the objective
  shifts from faster evidence accumulation to testing the strongest synthetic
  leaderboard strategy.

Risk:
- HIGH: financial strategy selection and future promotion behavior.
- Acceptance state: READY_FOR_INDEPENDENT_REVIEW.

## Priority 12 - Short-Market Strategy Research

Status: read-only collector/store extension accepted; sample and spot-context
proofs complete; Binance derivatives context blocked

Why it matters:
- The current `es_daily_trend_v1` strategy is long/flat only. It does not
  participate directly in downtrends except by exiting or staying flat.
- A short-market strategy could improve regime coverage, but it changes the
  risk profile materially and must not be treated as a small tweak to
  `sma_200_trend`.
- `docs/checkpoints/short_market_strategy_research_spec_2026_06_19.md`
  defines the separate research path, evidence gates, instrument tracks, data
  requirements, and stop conditions.
- `docs/checkpoints/short_context_data_feasibility_audit_2026_06_19.md`
  identifies the existing read-only crypto-edge collector as the safest base
  and documents missing open-interest, liquidation, order-book-depth,
  provenance, and storage support.
- PR #72 extends the crypto-edge collector/store/report path for
  read-only `open_interest` and `order_books` rows without changing strategy
  routing, paper execution, promotion gates, credentials, or live behavior.
- Isolated sample proof completed against
  `/private/tmp/cbp_crypto_edge_context_sample_proof_20260619.sqlite` with
  `research_only=true`, `execution_enabled=false`, and all five row families
  present: funding, open interest, basis, quotes, and order books.
- Live-public proof completed against
  `/private/tmp/cbp_crypto_edge_context_live_public_proof_20260619.sqlite` with
  `research_only=true` and `execution_enabled=false`. Coinbase/Kraken quotes
  and Coinbase order-book rows were collected. Binance funding, open-interest,
  and basis rows were not collected because the repo's Binance guard blocks
  Binance unless `CBP_VENUE` and `CBP_ALLOW_BINANCE=1` explicitly allow it.
- Guard-enabled Binance-only proof was attempted against
  `/private/tmp/cbp_crypto_edge_context_binance_guard_proof_20260619.sqlite`
  with `CBP_VENUE=binance` and `CBP_ALLOW_BINANCE=1`. It collected no rows
  because Binance exchange open failed with `NetworkError`; output still
  reported `research_only=true` and `execution_enabled=false`.

Next action:
- If derivatives context is needed, resolve the Binance public-data
  `NetworkError` separately or choose a different read-only derivatives venue
  after compliance/account review. Do not run this as a long-lived loop and do
  not treat it as venue/compliance approval.
- Do not use the new rows in replay analysis until the public-data proof is
  accepted for the relevant row family, or the replay is explicitly limited to
  deterministic sample data.
- Keep all short-side work research-only until separate paper gates, risk
  controls, compliance assumptions, and operator review exist.

Risk:
- HIGH: short exposure has different tail-risk, margin, liquidation, and
  operational failure modes than long/flat paper trading.
- Acceptance state: ACCEPTED by human operator review on 2026-06-19 after PR
  #72 checks passed and the merge landed on `master` as `977ea9c3`.

## Priority 13 - Pattern And Hybrid Strategy Roadmap

Status: `pullback_recovery` plan accepted; attribution fix merged; full
post-fix Stage 0 rerun pending operator execution; composite/hybrid wrapper
design accepted; pure combiner proof ready for independent review

Why it matters:
- `pullback_recovery` is already coded and wired into the strategy registry.
- It now has a default preset and is part of the aggregate leaderboard evidence
  candidate set.
- Pattern recognition is a better fit for the operator's "identify the move
  early enough" objective than only slow trend following.
- Hybrid strategy work can combine existing signals, but it needs a
  backtestable composite strategy path rather than ad hoc operator judgment.

Next action:
- Run only the full post-fix Stage 0 isolated one-shot proof for
  `pullback_recovery_default` when the operator is ready for a 15-minute
  command. Do not enable a persistent daily campaign until that proof passes.
- Independently review the pure combiner proof for the confirmation-gate
  wrapper before any parity backtest integration. Do not add a leaderboard
  row, persistent paper campaign, or production path until the combiner proof
  and follow-up backtest proof are reviewed.
- Track candlestick recognition as a later versioned strategy such as
  `candlestick_reversal_v1`, after `pullback_recovery` has a baseline.
- Treat `order_book_imbalance`, `open_interest_shift`, and `funding_extreme` as
  separate context-pattern work until reliable order-book, derivatives,
  funding, and open-interest data plumbing is verified.

Risk:
- HIGH: financial strategy selection, future promotion behavior, and potential
  expansion from simple single-signal strategies into composite decision logic.

## Priority 14 - Repo Infrastructure Activation Audit

Status: complete. Initial audit and second-pass corrections accepted by
independent operator review.

Why it matters:
- The repo contains infrastructure beyond the current active
  `sma_200_trend` paper campaign, including AI/ML, signals/candidate ranking,
  alerting, learning/feedback, dashboard pages, desktop packaging, and many
  operator scripts.
- Activating dormant infrastructure without an audit could add operational risk,
  duplicate responsibilities, or mix unvalidated systems into the evidence
  campaign.
- A structured inventory is needed before deciding which systems should be
  wired, documented, retired, or left research-only.

Next action:
- Turn the highest-priority activation item into a scoped objective with proof
  requirements.

Risk:
- HIGH: repository architecture, operational workflow, and future trading
  automation. The audit should not enable dormant systems by itself.

## Priority 15 - Golden Path And Script Index Alignment

Status: complete. Independently reviewed and accepted by operator on
2026-06-04.

Why it matters:
- The repo has many operator scripts beyond the narrow Golden Path. Some are
  documented in `scripts/SCRIPTS.md` or focused feature docs, while others may
  not be visible from the canonical operator workflow.
- Operators should not have to infer which scripts are safe daily commands,
  diagnostics, one-off repairs, research tools, or deprecated surfaces.
- A single visible command map reduces operator-memory burden without changing
  runtime behavior.

Next action:
- Use `scripts/SCRIPTS.md` as the authoritative root script command map going
  forward.
- Keep `docs/GOLDEN_PATH.md` narrow and update `scripts/SCRIPTS.md` whenever
  root script entrypoints are added or removed.

Risk:
- MEDIUM: operator workflow and documentation accuracy. This should remain
  documentation-only unless the audit exposes an unsafe command path that needs
  separate engineering work.

## Priority 16 - Hetzner Paper Campaign Host

Status: runbook accepted; host hardening proof complete; Tailscale-only SSH,
Hetzner Cloud firewall, backups, and delete/rebuild protection applied;
state-transfer manifest tooling, host preflight tooling, and the isolated
challenger proof template are accepted. Campaign deployment remains blocked
pending explicit single-owner operation, server-hosted UTC cycle proof, and
backup/restore rehearsal.

Why it matters:
- The current detached collectors stop when the operator laptop is shut down,
  restarted, disconnected for maintenance, or unavailable for recovery.
- A stable VPS is appropriate for the daily SMA campaign and the 5-minute EMA
  and Donchian paper challengers because it provides continuous outbound market
  data access and persistent local state.
- Infrastructure uptime can improve evidence continuity, but it cannot increase
  strategy signal frequency, qualify legacy fills, or prove profitability.
- The existing Docker Compose stack publishes backend and dashboard ports on
  all interfaces, while the repo's auth documentation says remote/public
  hardening remains incomplete. It must not be deployed unchanged to a public
  VPS.

Next action:
- Keep the paper-only Hetzner deployment runbook as the controlling artifact:
  `docs/HETZNER_PAPER_HOST.md`.
- Use `scripts/paper_state_manifest.py` for state-transfer integrity. Do not
  use ad hoc OS-specific checksum commands for this path.
- Use `scripts/hetzner_paper_host_preflight.py` on the host before restore and
  again with `--require-state` after state transfer.
- Copy
  `docs/deployment_records/hetzner_isolated_challenger_proof_TEMPLATE.md` to a
  dated deployment record before any collector stop, state transfer, or VPS
  restore command.
- Administer the host with Tailscale SSH only:
  `tailscale ssh cryptkeep@100.86.128.9`.
- Do not use the older CIDR-based safeguard mode for this host unless the access
  policy is explicitly changed away from Tailscale-only.
- Run collectors with no live-trading credentials and no public application
  ports.
- Define one owner for `ema_cross_default` before transfer so laptop and VPS
  collectors cannot run simultaneously against copied state.
- Record the laptop status, laptop stop proof, manifest create proof, transfer
  proof, Hetzner preflight proof, manifest verify proof, VPS restore proof,
  and single-owner proof in the dated deployment record.
- Add disk-space monitoring, collector health alerts, and backup restore
  rehearsal evidence before any canonical `.cbp_state` migration.
- Prove the deployment first with an isolated challenger state directory, then
  migrate canonical `.cbp_state` only after a reviewed stop-copy-verify-start
  procedure.
- Keep the current laptop recovery path available as rollback until the VPS has
  completed at least one healthy UTC cycle and one restore rehearsal.

Proof required:
- Targeted deployment/config tests and a documented dry run.
- No externally reachable dashboard or backend port.
- `scripts/hetzner_paper_host_preflight.py` reports `ok=true` on the host at
  the accepted deployment commit.
- Hetzner Cloud firewall remains `cryptkeep-tailscale-only`, `0 Rules`,
  `1 Server`, and `Fully applied`.
- Hetzner backups remain enabled and backup window is visible.
- Hetzner delete/rebuild protection remains enabled.
- One collector owner per campaign, with duplicate-process checks passing.
- State manifest verification reports `ok=true`, `missing=[]`, `changed=[]`,
  and `extra=[]` before the VPS collector starts.
- Evidence counts match or advance after state transfer; they must not be
  merged from independently advanced laptop and VPS state trees.
- `restore_paper_campaigns.py --status` reports all configured collectors
  healthy on the VPS.
- A backup can be restored into an isolated directory and read successfully.

Risk:
- HIGH: persistent financial-evidence background jobs, state migration,
  credentials/configuration, remote host security, and duplicate campaign
  ownership.
- Acceptance state: runbook, cloud safeguards, manifest tooling, host preflight
  tooling, and proof template are accepted. Actual collector stop, state
  transfer, VPS restore/start, backup rehearsal, and canonical migration remain
  high-risk operations and must stop at `READY_FOR_INDEPENDENT_REVIEW` unless
  separately accepted by the human operator.

## Priority 17 - Derivatives, Intraday, And Context-Pattern Roadmap

Status: pending research and compliance review only

Why it matters:
- The operator wants strategies that can identify large intraday crypto moves
  early enough, not only slow daily trend-following entries.
- The repo already contains strategy/context modules for `funding_extreme`,
  `open_interest_shift`, `order_book_imbalance`, and `pullback_recovery`.
- Crypto perpetual futures are the closer derivatives path than traditional
  ES/NQ futures because the exchange/API pattern is nearer to the existing
  crypto connectors, but leverage, margin, liquidation, funding cost, and
  short exposure make this a separate high-risk workstream.
- Traditional futures remain a later workstream requiring a broker/FCM
  integration, contract specs, expiry/roll logic, and futures-specific margin
  controls.

Next action:
- Keep the current paper campaigns running; do not interrupt evidence
  collection for this roadmap.
- Use Priority 13 for the near-term pattern path: add `pullback_recovery` to
  leaderboard/evidence evaluation before adding new candlestick strategies.
- Add read-only context collection first for funding, open interest, order-book
  imbalance, and intraday candle/session features. Do not route these signals
  to orders until their data quality and evidence value are proven.
- Treat Bybit as out of scope unless a later compliance review proves the
  operator can legally use it; current public Bybit restrictions exclude U.S.
  users.
- Treat Binance perpetual futures as research/testnet-only until jurisdiction,
  account eligibility, API permissions, funding-rate accounting, leverage
  controls, margin tracking, reduce-only exits, and liquidation-risk controls
  are documented and tested.
- Add candlestick recognition as a confirmation layer after `pullback_recovery`
  has a baseline. Candidate filters include hammer/pin bar, bullish engulfing,
  fair-value gap, and order-block-style impulse/pullback zones.
- Add day-trading context only as read-only evidence at first: 1m/5m/15m
  timeframes, VWAP/session levels, prior day high/low/close, Level 2/order book
  imbalance, and time-of-day/session labels.

Proof required:
- Compliance note for each venue before any derivatives execution adapter is
  built.
- Read-only data collectors with provenance for funding, open interest, order
  book, and intraday OHLCV/session context.
- Backtest or replay baseline showing whether context-pattern signals identify
  moves earlier than the current strategies without unacceptable false positives.
- Separate paper gates for any short-side or leveraged strategy.
- Explicit risk controls for funding cost, leverage, margin, reduce-only exits,
  liquidation protection, max loss, and kill-switch behavior.

Risk:
- HIGH: derivatives, shorting, leverage, margin, liquidation risk, financial
  strategy selection, and future order-routing behavior.
- Acceptance state: planning only; implementation must stop at
  `READY_FOR_INDEPENDENT_REVIEW`.

## Priority 18 - PR #3 Cleanup/Disposition

Status: complete as of 2026-06-19; PR #3 closed after accepted disposition

Why it matters:
- PR #3 was a dirty stale branch against `master` and was not tracked by the
  prior top-priority checkpoint list before the disposition work.
- The branch contained old execution cleanup, queue authority, paper scenario,
  live reconciler, and CI-collection fixes. Some of those topics have since
  been independently rebuilt, but the branch had patch-unique commits that
  needed disposition before closure.
- Closing it after accepted disposition prevents the same false backlog problem
  previously fixed for superseded PR #10.

Current evidence:
- SHOWN on 2026-06-19: PR #3 targets `master`, is not draft, and has merge
  state `DIRTY`.
- SHOWN: `origin/master...origin/cleanup/import-collection-failures` reports
  `283 / 54`.
- SHOWN: the 54 branch-only commits are accounted for in
  `docs/checkpoints/pr3_cleanup_disposition_2026_06_19.md` as 52 non-merge
  commits plus 2 merge commits.
- SHOWN: PR #3 was closed on 2026-06-19 after the accepted disposition
  checkpoint was merged via PR #62.
- SHOWN: the closure work log recorded `gh pr view 3` returning
  `state=CLOSED` and `closed=true`.
- SHOWN: PR #42 and PR #43 were later closed after the accepted PR #43
  disposition path, so no stale PR #3/#42/#43 merge candidate remains open.
- SHOWN: the branch touches high-risk execution and live reconciliation files
  including `services/execution/live_reconciler.py`,
  `services/execution/intent_consumer.py`, `services/execution/paper_engine.py`,
  `storage/intent_queue_sqlite.py`, and `storage/live_intent_queue_sqlite.py`.

Next action:
- Rebuild only commits marked `rebuild` in the accepted disposition checkpoint
  as narrow current-master PRs with targeted tests.
- Do not reopen or merge PR #3 directly.

Proof required:
- Commit-by-commit disposition table: `superseded`, `rebuild`, or `drop`.
- Targeted tests for any rebuilt execution or reconciliation change.

Risk:
- HIGH: live execution state transitions, queue authority, reconciliation, and
  CI behavior.
- Acceptance state: planning/audit only; implementation must stop at
  `READY_FOR_INDEPENDENT_REVIEW`.

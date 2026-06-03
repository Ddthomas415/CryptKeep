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

CLAIMED:
- Auditor reported `review-stabilized` as 83 commits ahead of master and 59
  behind.
- Auditor reported PR #42 and PR #43 as open/draft or held upstream PRs.

UNVERIFIED:
- PR #42 and PR #43 current GitHub state was not checked in this pass.
- PR #44 has not received full-suite or independent merge review in this
  checkpoint file.

## Priority 1 - Master Integration

Status: draft PR created, pending independent review and merge decision

Why it matters:
- `review-stabilized` is clean and accepted, but `master` remains behind.
- Audit work is not in the canonical production line until master receives it.
- The local resolved integration branch is now preserved remotely, but `master`
  is still unchanged.

Next action:
- Review PR #44 before any master update.
- Re-run full suite or CI before merge.
- Use `REMAINING_TASKS.md` as the source list for the 25 known conflict files.

Risk:
- HIGH: integration touches live execution, paper execution, queues, dashboard
  settings, and tests.

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

Status: implementation proof ready, pending independent review

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

Next action:
- Independent review of the shadow-gate evidence change.
- Let the next daily collector run create fresh signal records and verify new
  records contain `spread_bps` when tick data is fresh.

Risk:
- HIGH: promotion path and live-adjacent operational readiness.

## Priority 6 - `daily_loss_halt_pct` Wiring

Status: pending

Why it matters:
- `configs/strategies/es_daily_trend_v1.yaml` declares `daily_loss_halt_pct`.
- The spec says runtime enforcement currently lives in a separate absolute-USD
  service.
- This is a safety-control discrepancy unless explicitly wired or accepted.

Next action:
- Either wire the strategy config target into runtime enforcement, or document
  an accepted decision that the separate service is authoritative and the config
  field is declarative only.

Risk:
- HIGH: risk controls and safety enforcement.

## Priority 7 - Strategy Performance Decision

Status: pending manual review

Why it matters:
- `manual_review_required=true` now persists until observed win rate and average
  win/loss are compared against backtest expectations.
- Paper gate progress should not be confused with strategy profitability.

Next action:
- Write a strategy performance decision after comparing paper-history metrics
  against backtest expectations.
- Decide whether current underperformance is acceptable variance or structural
  weakness.

Risk:
- HIGH: financial strategy evaluation.

## Priority 8 - PR #42 Decision

Status: pending

Claimed context:
- PR #42 has remained a draft soak branch.
- It either needs to be marked ready and merged or have unique content extracted
  before closing.

Next action:
- Verify current PR #42 state.
- Decide whether to merge, extract unique content, or close.

Risk:
- MEDIUM to HIGH: upstream branch divergence.

## Priority 9 - Rebuild PR #43 From Clean Base

Status: blocked behind master integration and audit branch merge state

Claimed context:
- PR #43 has valuable AI copilot, multi-symbol runtime, and
  `run_pipeline_safe.py` content.
- It conflicts heavily with audit branches.

Next action:
- After master integration, rebuild unique PR #43 content as a focused clean PR
  against updated master.

Risk:
- MEDIUM: valuable feature work is currently stranded.

## Priority 10 - CI Fixture For `sma_200_trend`

Status: pending low-priority hardening

Why it matters:
- Sample mode can prove entry/fill mechanics but not a deterministic
  `sma_200_trend` exit.
- A 220-bar synthetic OHLCV fixture can cover 200 warmup bars plus engineered
  entry and exit windows.

Next action:
- Add deterministic fixture under `sample_data/ohlcv/`.
- Add CI test proving a buy -> sell round trip for `sma_200_trend`.

Risk:
- LOW to MEDIUM: CI repeatability and strategy-path coverage.

## Priority 11 - Higher-Turnover Daily/Weekly Strategy Plan

Status: pending strategy design

Why it matters:
- `sma_200_trend` is a slow-turnover daily trend strategy. It validates the
  pipeline, but it is not designed to produce frequent weekly income.
- The current repo already contains higher-turnover candidates such as
  `ema_cross`, `breakout_donchian`, and `mean_reversion_rsi`; they need real
  paper evidence before any promotion decision.

Next action:
- Write a dedicated paper-only strategy plan for a daily/weekly income
  candidate.
- Define candidate strategy, timeframe, expected turnover, hold period, risk
  cap, evidence gate, backtest baseline, and isolation rules.
- Prefer `ema_cross` if the objective is faster evidence accumulation.
- Prefer `breakout_donchian` if the objective is to test the strongest current
  synthetic leaderboard candidate.

Risk:
- HIGH: financial strategy selection and future promotion behavior.

## Priority 12 - Short-Market Strategy Research

Status: pending research only

Why it matters:
- The current `es_daily_trend_v1` strategy is long/flat only. It does not
  participate directly in downtrends except by exiting or staying flat.
- A short-market strategy could improve regime coverage, but it changes the
  risk profile materially and must not be treated as a small tweak to
  `sma_200_trend`.

Next action:
- Create a separate short-side research spec before any implementation.
- Define allowed instruments, borrow/margin assumptions, stop behavior,
  max loss, liquidation protection, short-specific kill-switch behavior, and
  whether the strategy is spot-compatible or requires derivatives.
- Keep all short-side work research/paper-only until separate paper gates,
  risk controls, and operator review exist.

Risk:
- HIGH: short exposure has different tail-risk, margin, liquidation, and
  operational failure modes than long/flat paper trading.

## Priority 13 - Pattern And Hybrid Strategy Roadmap

Status: pending strategy design

Why it matters:
- `pullback_recovery` is already coded and wired into the strategy registry, but
  it is not part of the current aggregate leaderboard evidence set.
- Pattern recognition is a better fit for the operator's "identify the move
  early enough" objective than only slow trend following.
- Hybrid strategy work can combine existing signals, but it needs a
  backtestable composite strategy path rather than ad hoc operator judgment.

Next action:
- Add `pullback_recovery` to leaderboard/evidence evaluation first because it is
  the lowest-infrastructure pattern candidate already available in the repo.
- Create a paper-only `pullback_recovery` campaign plan with its own backtest
  baseline, expected turnover, risk cap, and evidence gate.
- Design a backtestable composite/hybrid wrapper before combining strategies in
  production paths. Candidate hybrids include trend-confirmed breakout,
  range/trend switcher, and weighted-vote consensus.
- Track candlestick recognition as a later versioned strategy such as
  `candlestick_reversal_v1`, after `pullback_recovery` has a baseline.
- Treat `order_book_imbalance`, `open_interest_shift`, and `funding_extreme` as
  separate context-pattern work until reliable order-book, derivatives,
  funding, and open-interest data plumbing is verified.

Risk:
- HIGH: financial strategy selection, future promotion behavior, and potential
  expansion from simple single-signal strategies into composite decision logic.

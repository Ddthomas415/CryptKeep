# Review Stabilized Next Actions - 2026-05-28

This checkpoint records the proactive task list raised during the 2026-05-28
audit discussion. It is intentionally separate from the work log: the work log
records completed work; this file records pending work and ordering.

## Evidence Basis

SHOWN:
- Current branch is `review-stabilized`.
- Local comparison `master...review-stabilized` reports `64 / 83`.
- `REMAINING_TASKS.md` documents the 2026-05-25 master integration blocker and
  25 conflicted files from a no-commit test merge.
- A local integration worktree exists at
  `/private/tmp/cryptkeep-master-review-stabilized-integration`.
- That worktree is on `codex/master-review-stabilized-integration` and is
  `ahead 70` of `origin/master`.
- Latest local integration worktree commit shown:
  `9862147ed merge: integrate review-stabilized into master`.

CLAIMED:
- Auditor reported `review-stabilized` as 83 commits ahead of master and 59
  behind.
- Auditor reported PR #10 as superseded by `6cc95f6`.
- Auditor reported PR #42 and PR #43 as open/draft or held upstream PRs.

UNVERIFIED:
- Current GitHub PR state was not checked in this pass.
- The local integration worktree was inspected only by `git status` and
  `git log -1`; its conflict resolutions were not revalidated in this pass.

## Priority 1 - Master Integration

Status: pending

Why it matters:
- `review-stabilized` is clean and accepted, but `master` remains behind.
- Audit work is not in the canonical production line until master receives it.
- The local resolved integration branch is at risk of being lost if the temp
  worktree is reset.

Next action:
- Preserve or push the local integration branch only after an explicit operator
  decision because this updates the master integration path.
- Re-run conflict-sensitive verification before any master update.
- Use `REMAINING_TASKS.md` as the source list for the 25 known conflict files.

Risk:
- HIGH: integration touches live execution, paper execution, queues, dashboard
  settings, and tests.

## Priority 2 - Work Log Accuracy

Status: in progress in this checkpoint's companion work-log update

Required fixes:
- Update `84aa49113` acceptance state to `ACCEPTED`.
- Add missing `e06d49371` work-log entry.
- Replace vague "accepted by later review" wording with reviewer/date/session
  references.
- Fix ambiguous `9f90a8d2e` acceptance wording.

Risk:
- MEDIUM: audit-trail credibility.

## Priority 3 - Close Superseded PR #10

Status: pending

Claimed context:
- PR #10 is conflicted.
- Its COALESCE/null-overwrite fix is already present in `review-stabilized` at
  `6cc95f6`.

Next action:
- Verify PR #10 state through GitHub tooling.
- If verified, close it with a comment referencing `6cc95f6`.

Risk:
- LOW to MEDIUM: repository hygiene and audit-noise reduction.

## Priority 4 - Keep Paper Campaign Running

Status: passive monitoring

Current gate state:
- 3 more round trips needed.
- 8 more calendar days needed.

Next action:
- Confirm paper evidence collector is alive.
- Confirm paper sim monitor is healthy.
- Continue daily evidence collection.

Risk:
- MEDIUM: operational interruption could waste the shortened paper-gate window.

## Priority 5 - Prepare Shadow Gate Before Paper Clears

Status: pending

Why it matters:
- Paper gate is close enough that shadow tooling should be validated before the
  paper gate clears.
- Shadow requires signal logging against live market data and slippage/depth
  validation.

Next action:
- Audit whether shadow-mode signal logging includes contemporaneous spread/depth
  fields.
- Audit whether the shadow comparison pipeline can run before any sandbox
  promotion decision.
- Add missing tests/docs if the shadow surface is incomplete.

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

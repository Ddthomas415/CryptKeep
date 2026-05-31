# Review Stabilized Work Log

This file is the durable Codex work log for `review-stabilized`.

Purpose: make engineering/audit work visible in git, including what was found,
what changed, why that change was chosen, expected outcome, verification, and
remaining risk.

## Logging Rule

Every future Codex change that affects code, docs, tests, runtime policy,
operator workflow, or gate behavior must add or update an entry here before
handoff.

Minimum entry fields:
- date/time or commit SHA
- active role and objective
- what was found
- what changed
- why that change was chosen
- expected outcome
- verification run, or why verification was not run
- remaining risk and acceptance state

High-risk work must end at `READY_FOR_INDEPENDENT_REVIEW` in this log until a
separate reviewer or human accepts it.

## Retrospective Scope

SHOWN:
- The current branch is `review-stabilized`.
- Recent visible commit history is available through `git log --oneline`.
- Recent verification results were captured in this thread for the latest gate
  and monitor changes.

UNVERIFIED:
- Older commit intent can only be reconstructed from commit messages and visible
  repo artifacts unless a decision record or command output is present.
- This retrospective is therefore a best-effort reconstruction, not a substitute
  for the original review transcript.

## 2026-05-28 - Master Integration Branch Refresh With Shadow Evidence

Date: 2026-05-28

Active role: `ENGINEER`

Objective: refresh draft PR #44 with the latest accepted `review-stabilized`
tip after the shadow spread evidence fix and acceptance-log update.

What was found:
- SHOWN: main `review-stabilized` was clean and synced at
  `4c414b256 docs: accept shadow spread evidence fix`.
- SHOWN: the existing PR #44 branch
  `codex/master-review-stabilized-integration` did not contain `4c414b256`.
- SHOWN: merging latest `review-stabilized` into the integration branch merged
  source changes cleanly and produced one content conflict in
  `docs/work_log/review_stabilized_work_log.md`.

What changed:
- Resolved the work-log conflict by preserving the prior master-integration
  entry plus the newer PR #10 and shadow-spread evidence entries.
- Refreshed the integration branch with the accepted shadow-gate evidence
  changes from `review-stabilized`.
- Left `master` unchanged.

Why this change:
- PR #44 is the current review surface for moving `review-stabilized` toward
  `master`; it must carry the latest accepted work or reviewers will audit a
  stale integration branch.
- Keeping the integration conflict resolution on the PR branch avoids repeating
  temp-worktree recovery work.

Expected outcome:
- PR #44 remains the single reviewable master-integration branch and now
  includes the latest accepted shadow evidence work.
- Future master merge review can focus on PR #44 instead of chasing branch
  drift between `review-stabilized` and the integration branch.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_check_promotion_gates.py tests/test_service_control_path.py tests/test_service_ctl_smoke.py tests/test_safe_wrapper_import_side_effects.py tests/test_intent_services_safe_import.py tests/test_hardening_smoke.py tests/test_run_bot_runner.py tests/test_intent_services_safe_runtime_config.py tests/test_bootstrap_helper_adoption.py tests/test_no_duplicate_script_bootstrap.py`
  - SHOWN: `102 passed in 1.68s`.

Remaining risk:
- HIGH: master integration branch and promotion evidence behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator in
  the 2026-05-28 audit session after commit `4ce4d083e`.

## 2026-05-28 - Master Integration Branch Refresh

Date: 2026-05-28

Active role: `ENGINEER`

Objective: update the existing `codex/master-review-stabilized-integration`
worktree with the latest accepted `review-stabilized` tip without changing
`master`.

What was found:
- SHOWN: `review-stabilized` was clean and synced at
  `507d9f05d docs: fix work log audit trail`.
- SHOWN: local `master...review-stabilized` comparison reported `64 / 84`.
- SHOWN: the existing integration worktree at
  `/private/tmp/cryptkeep-master-review-stabilized-integration` was on
  `codex/master-review-stabilized-integration`.
- SHOWN: merging latest `review-stabilized` into that integration branch
  produced four add/add conflicts:
  - `scripts/run_bot_runner.py`
  - `scripts/run_intent_executor_safe.py`
  - `scripts/run_intent_reconciler_safe.py`
  - `scripts/service_ctl.py`

What changed:
- Resolved the four conflicts by taking the `review-stabilized`
  executable-wrapper shape.
- Preserved executable bits on the four wrapper files.
- Left `master` and the main `review-stabilized` worktree unchanged.

Why this change:
- The integration branch is the correct place to absorb master/review branch
  conflicts before any canonical `master` update.
- The `review-stabilized` wrapper shape preserves direct script execution,
  avoids import-time side effects, and matches the service-control text test.
- Pushing the integration branch prevents the resolved worktree from being lost
  if the temporary worktree is removed.

Expected outcome:
- `codex/master-review-stabilized-integration` contains the latest accepted
  `review-stabilized` work plus the existing master integration resolution.
- Reviewers can inspect one branch for the master update instead of recovering
  temp-state conflict work.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_service_control_path.py tests/test_service_ctl_smoke.py tests/test_safe_wrapper_import_side_effects.py tests/test_intent_services_safe_import.py tests/test_hardening_smoke.py tests/test_run_bot_runner.py tests/test_intent_services_safe_runtime_config.py tests/test_bootstrap_helper_adoption.py tests/test_no_duplicate_script_bootstrap.py`
  - SHOWN: `50 passed in 1.00s`.

Remaining risk:
- HIGH: master integration and script entrypoint behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator in
  the 2026-05-28 audit session after PR #44 was created.

## 2026-05-28 - Paper Campaign Check and Shadow Signal Spread Evidence

Date: 2026-05-28

Active role: `ENGINEER`

Objective: verify the paper evidence campaign is still progressing and close
the immediate shadow-gate spread/depth logging gap before the paper gate clears.

What was found:
- SHOWN: `scripts/run_paper_strategy_evidence_collector.py --status` reported
  the collector `pid_alive=true`, `status=idle`, `reason=waiting_for_next_day`,
  and `last_completed_day=2026-05-28`.
- SHOWN: `scripts/check_promotion_gates.py --json` reported `23/30` days and
  `7/10` round trips, with manual review still required.
- SHOWN: `scripts/run_paper_sim_monitor.py --status` reported monitor
  `status=stopped`, `recommendation=continue`, and active watches. This is
  expected after the daily collector stops run components.
- SHOWN: `scripts/check_promotion_gates.py --stage shadow --json` reported
  `All signals logged with spread/depth data` as failed across `33251`
  historical signal records.
- SHOWN: historical `es_daily_trend_v1` signal records had no spread/depth keys.

What changed:
- Added `_market_quality_evidence_extra(...)` in
  `services/strategy_runner/ema_crossover_runner.py`.
- Public-OHLCV signal evidence now merges local market-quality fields into
  `evidence_extra`, including `spread_bps` when fresh bid/ask data is present.
- Updated the shadow gate to recognize `spread_bps` and explicit depth keys.
- Added tests for the market-quality evidence helper and shadow gate
  spread/depth recognition.
- Updated the next-actions checkpoint with campaign status and shadow-gate
  implementation proof.

Why this change:
- The shadow checklist requires contemporaneous spread/depth data before
  paper -> shadow/sandbox review.
- Existing historical signals could never satisfy that gate because the runner
  did not attach market-quality fields to signal evidence.
- Using the local tick snapshot path avoids adding network calls to the signal
  path and aligns with the existing market-quality guard.

Expected outcome:
- Future public-OHLCV signal records include `spread_bps` when the tick
  publisher has fresh bid/ask data.
- The shadow gate can distinguish new market-quality-stamped signal evidence
  from legacy unstamped evidence.
- Existing historical signal evidence remains honestly failing until replaced
  or supplemented by fresh stamped runs.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_check_promotion_gates.py`
  - SHOWN: `52 passed in 0.80s`.
- `python3 -c "... _market_quality_evidence_extra('coinbase','BTC/USDT') ..."`
  - SHOWN: current idle tick data was stale, returning `market_quality_reason:
    stale_tick`; no `spread_bps` was emitted during idle.

Remaining risk:
- HIGH: promotion evidence and shadow-gate behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator in
  the 2026-05-28 audit session after commit `9f0dd8b0c`.

## 2026-05-28 - PR #10 Supersession Closure and Checkpoint Refresh

Date: 2026-05-28

Active role: `ENGINEER`

Objective: close the stale PR #10 audit-noise item after verifying the fix is
already present on `review-stabilized`, and update the visible checkpoint.

What was found:
- SHOWN: PR #10 was open against `review-stabilized` from
  `audit/defect-05-null-overwrite`.
- SHOWN: PR #10 contained commit
  `5858dcc1969ec68763a11dc85fe589ca7de5a755`.
- SHOWN: that exact commit is not an ancestor of `review-stabilized`.
- SHOWN: `6cc95f678 fix: preserve queue ids on guarded status updates` is an
  ancestor of `review-stabilized`.
- SHOWN: current paper/live queue code preserves existing client, linked, and
  exchange order ids with `COALESCE`.

What changed:
- Closed PR #10 with an audit comment referencing `6cc95f678`.
- Updated `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to
  mark PR #10 complete and record PR #44 as the preserved master-integration
  draft PR.
- Updated this work log so the repository records the GitHub housekeeping work.

Why this change:
- Leaving a superseded PR open creates false audit noise and makes it look like
  a queue-id preservation defect is still unresolved.
- The checkpoint should reflect current repository state instead of stale
  pending work.

Expected outcome:
- Reviewers can see that PR #10 is closed because the accepted equivalent fix is
  already on `review-stabilized`.
- The remaining highest structural item is review/merge decision for PR #44,
  not recovery of the old temp integration worktree.

Verification:
- `gh pr view 10 --json ...`
  - SHOWN: PR #10 was open before closure.
- `gh pr view 10 --json number,state,url,title`
  - SHOWN: PR #10 state is `CLOSED` after closure.
- `git merge-base --is-ancestor 6cc95f678 review-stabilized`
  - SHOWN: passed.
- `rg -n "COALESCE\\(\\?, client_order_id\\)|COALESCE\\(\\?, linked_order_id\\)|COALESCE\\(\\?, exchange_order_id\\)" storage/intent_queue_sqlite.py storage/live_intent_queue_sqlite.py`
  - SHOWN: matched current queue preservation paths.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_queue_update_status_preserves_ids.py`
  - SHOWN: `2 passed in 0.08s`.

Remaining risk:
- LOW: GitHub PR hygiene and checkpoint accuracy.
- Acceptance state: `ACCEPTED`.

## 2026-05-28 - Work Log Audit Corrections and Next-Actions Checkpoint

Date: 2026-05-28

Active role: `ENGINEER`

Objective: correct work-log acceptance states, add the missing high-risk
promotion-ladder entry, and make the broader next-action list visible in git.

What was found:
- SHOWN: the auditor identified four work-log accuracy issues:
  - `84aa49113` still showed `READY_FOR_INDEPENDENT_REVIEW`.
  - `e06d49371` had no entry.
  - several entries used vague "accepted by later review" wording.
  - `9f90a8d2e` had ambiguous acceptance wording.
- SHOWN: `git show e06d49371` changed promotion ladder code, docs, digest
  wiring, and tests.
- SHOWN: local `master...review-stabilized` comparison reports `64 / 83`.
- SHOWN: `REMAINING_TASKS.md` documents the master integration conflict list.

What changed:
- Updated `84aa49113` and `9f90a8d2e` acceptance states to `ACCEPTED` with
  auditor/session references.
- Added a full entry for `e06d49371`.
- Replaced "accepted by later review" with reviewer/date/session references.
- Added `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` with
  the prioritized task list and SHOWN/CLAIMED/UNVERIFIED evidence labels.

Why this change:
- The work log is now a governed artifact under `AGENTS.md`.
- Incorrect or vague acceptance states weaken the audit trail.
- The broader next-action list needs to be visible in git instead of existing
  only in chat.

Expected outcome:
- Future readers can trace accepted high-risk changes to an auditor/date/session
  reference.
- The promotion-ladder coupling fix is represented in the governed work log.
- Master integration, PR cleanup, paper campaign monitoring, shadow prep,
  safety wiring, and CI-fixture work are tracked as visible pending actions.

Verification:
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- MEDIUM: documentation accuracy and governance traceability.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator in
  the 2026-05-28 audit session after commit `507d9f05d`.

## 2026-05-27 - Paper Gate Threshold and Manual Review

Commit: `84aa49113 fix: align paper gate threshold with slow turnover`

Active role: `ENGINEER` then `GATE`

Objective: make the paper-stage round-trip threshold coherent for a daily
slow-turnover strategy without implying profitability.

What was found:
- SHOWN: `check_promotion_gates.py` reported `7/50, 43 remaining`.
- SHOWN: `docs/DECISION_FRAMEWORK.md` and
  `docs/strategies/es_daily_trend_v1.md` used a 50+ paper round-trip gate.
- SHOWN: the strategy spec says the holding period is days to months, making
  50 paper round trips an impractical paper-to-sandbox blocker.
- SHOWN: the machine gate checked positive average PnL but did not machine-check
  win rate and avg win/loss against backtest expectations.

What changed:
- Paper-stage round-trip threshold changed from `50` to `10` in
  `services/control/promotion_thresholds.py`.
- Gate label and progress output changed to `10+ completed round trips`.
- `50+` was retained in docs as a later research/live-capital confidence floor.
- `check_promotion_gates.py` now emits:
  - `machine_ready`
  - `manual_review_required`
  - `manual_review`
- The manual-review block surfaces the outstanding win-rate and avg win/loss vs
  backtest comparison and includes observed paper-history metrics.
- Docs now state that 10+ round trips validates the paper execution path and
  does not prove profitability.

Why this change:
- A slow daily strategy cannot reasonably be blocked from sandbox/shadow review
  by a threshold that may require months or years.
- Lowering the paper threshold without surfacing manual review would create a
  false readiness signal.
- Keeping `50+` as a later confidence floor preserves the stronger evidence bar
  for larger live-capital decisions.

Expected outcome:
- The machine gate reports current progress as `7/10, 3 remaining`.
- Even after machine thresholds pass, `ready=false` while manual review remains
  outstanding.
- Operators see that sandbox/shadow review is path validation, not a
  profitability endorsement.

Verification:
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: `7/10, 3 remaining`
  - SHOWN: `manual_review_required=true`
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py tests/test_dashboard_page_runtime.py`
  - SHOWN: `67 passed`
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `1907 passed, 33 skipped`

Remaining risk:
- HIGH: promotion-gate policy and financial/operator decision logic.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor in the 2026-05-28 audit session
  after the `manual_review_required` clarification, targeted tests, and full
  suite proof (`1907 passed, 33 skipped`).

## 2026-05-27 - Paper Promotion Progress in Monitor

Commit: `9f90a8d2e feat: surface paper promotion progress in monitor`

Active role: `ENGINEER` then `GATE`

Objective: make promotion-gate progress visible in the paper sim monitor and
Operations dashboard so the operator does not have to poll CLI output manually.

What was found:
- SHOWN: `check_promotion_gates.py --json` exposed remaining day and round-trip
  thresholds.
- SHOWN: paper sim monitor status exposed current campaign state and watches but
  did not include authoritative promotion threshold progress.
- SHOWN: stopped monitor status could preserve a stale PID and report
  `pid_alive=true` after the PID file disappeared.

What changed:
- Added service-layer promotion threshold helpers:
  - `services/control/promotion_thresholds.py`
  - `services/control/paper_promotion_progress.py`
- Paper sim monitor now includes `promotion_progress`,
  `promotion_thresholds_ready`, and `promotion_progress_summary`.
- Operations dashboard table now shows promotion threshold readiness and
  progress.
- Stopped monitor status no longer trusts stale status PIDs unless the monitor is
  running or starting.
- `docs/GOLDEN_PATH.md` documents that the monitor surfaces promotion progress.

Why this change:
- Operator-facing monitor output should distinguish current campaign evidence
  from promotion readiness.
- The service-layer helper preserves the repo rule against services importing
  scripts.
- Stale PID correction prevents reused OS PIDs from making a stopped monitor look
  alive.

Expected outcome:
- Monitor and dashboard show threshold progress directly.
- A local monitor recommendation cannot be mistaken for promotion readiness.
- Stopped monitor status reconciles correctly.

Verification:
- `./.venv/bin/python scripts/run_paper_sim_monitor.py --status`
  - SHOWN: promotion progress appeared in status.
  - SHOWN: stopped monitor reported `pid=null`, `pid_alive=false`.
- Targeted monitor/dashboard/gate tests:
  - SHOWN: `66 passed`
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `1906 passed, 33 skipped`

Remaining risk:
- HIGH: background-job/operator gate visibility.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor in the 2026-05-28 audit session as
  part of the paired monitor/gate-policy review.

## 2026-05-18 - Target-Strategy Paper Promotion Gating

Commit: `e06d49371 fix: scope paper promotion gating to target strategy`

Active role: `ENGINEER` then `GATE`

Objective: decouple paper -> sandbox promotion readiness from the global
leaderboard top row and evaluate the named target strategy's own evidence row.

What was found:
- SHOWN by the audit finding: `breakout_donchian` could block
  `es_daily_trend_v1` paper -> sandbox review because the ladder evaluated the
  global top row.
- SHOWN by commit diff: `dashboard/services/promotion_ladder.py` used top-row
  helpers and was changed to accept and normalize a target `strategy_id`.
- SHOWN by commit diff: paper -> sandbox criteria changed from "Top strategy"
  wording to "Target strategy" wording.
- SHOWN by commit diff: sandbox -> tiny-live kept the top-strategy policy.

What changed:
- Added target-strategy normalization and lookup in
  `dashboard/services/promotion_ladder.py`.
- `build_promotion_readiness(...)` now accepts `strategy_id` for paper ->
  sandbox review.
- Paper -> sandbox blockers now evaluate the target row's recommendation,
  closed trades, evidence status, confidence, and post-cost return.
- Sandbox -> tiny-live review remains portfolio/top-strategy based.
- `docs/safety/strategy_promotion_ladder.md` documents the policy split.
- Tests were added for target-strategy paper gating and digest wiring.

Why this change:
- Paper -> sandbox answers whether a specific strategy has enough controlled
  behavior to shadow with real infrastructure.
- A different strategy with synthetic-only or weak evidence should not block a
  target strategy's paper-stage review.
- Portfolio-wide/top-strategy gating is still appropriate before real-capital
  exposure at the later sandbox -> tiny-live stage.

Expected outcome:
- `es_daily_trend_v1` paper -> sandbox readiness is judged from the
  `sma_200_trend` / target strategy evidence row.
- A synthetic-only global top strategy no longer creates an incoherent paper
  promotion blocker.
- Later live-capital review still requires the strongest portfolio candidate to
  be acceptable.

Verification:
- SHOWN by audit record supplied in this session: `34 tests pass`.
- SHOWN by commit diff: tests added in `tests/test_promotion_ladder.py` and
  `tests/test_dashboard_home_digest.py`.

Remaining risk:
- HIGH: promotion policy and operator gate behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: auditor sign-off on `e06d49371` in the 2026-05 audit
  session: "policy fix is correct, scoped correctly, and tested."

## 2026-05-27 - Promotion Gate Output Clarity

Commits:
- `183ac148e fix: suppress passed gate hints`
- `4354ca665 fix: show remaining paper gate thresholds`

Active role: `ENGINEER`

Objective: make gate output more actionable and reduce operator confusion.

What was found:
- SHOWN: passed gates could still include remediation hints.
- SHOWN: threshold gates did not clearly show remaining days/trips.

What changed:
- Passed gates now suppress hints.
- Paper days and round-trip gates now include observed/required counts and
  remaining counts.

Why this change:
- Passed gate hints make status output look degraded when it is not.
- Remaining counts are the operator's next-action data.

Expected outcome:
- Gate output should focus attention on actual blockers.
- Operators can see exactly how many days/trips remain.

Verification:
- SHOWN from prior handoff: targeted tests passed.
- SHOWN from later full-suite runs: full suite passed after these changes.

Remaining risk:
- LOW to MEDIUM: reporting-only, but promotion-gate output influences operator
  decisions.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through
  `INDEPENDENTLY_REVIEWED AND ACCEPTED` in the 2026-05 review-stabilized audit
  session after targeted gate-output verification.

## 2026-05-27 - No-Trade Evidence Windows and Script Compatibility

Commits:
- `7bf129bd5 fix: allow no-trade evidence windows`
- `108cbc403 fix: restore root script compatibility`

Active role: `ENGINEER`

Objective: prevent valid no-trade daily sessions and root script entrypoints
from blocking the evidence campaign.

What was found:
- SHOWN: daily paper runs can validly produce signal/session evidence without
  orders or fills.
- SHOWN: root script compatibility wrappers had regressed.

What changed:
- Promotion evidence presence allows no-trade windows when signal and session
  logs exist and no order/fill was expected.
- Root `scripts.*` compatibility wrappers were restored.

Why this change:
- A slow strategy often produces no trade on a valid day; treating that as an
  evidence failure makes the campaign unusable.
- Root script compatibility keeps documented operator commands runnable.

Expected outcome:
- No-trade daily sessions count as valid operational evidence.
- Existing script invocation paths continue to work.

Verification:
- SHOWN from prior handoff:
  - no-trade change full suite: `1902 passed, 33 skipped`
  - script compatibility full suite: `1900 passed, 33 skipped`

Remaining risk:
- MEDIUM: evidence semantics affect gate outcomes.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through
  `INDEPENDENTLY_REVIEWED AND ACCEPTED` in the 2026-05 review-stabilized audit
  session after full-suite proof (`1902 passed, 33 skipped` and `1900 passed,
  33 skipped` for the grouped changes).

## 2026-05-26 - Evidence Provenance and Gate Trust

Visible commits:
- `49c4570b7 fix: skip unattributed signal evidence`
- `2f44b97ad fix: report unknown provenance sources`
- `074856eb2 fix: report latest evidence log window in promotion gate`
- `b47bc3fed fix: require recent kill switch test in promotion gate`
- `705c6a10b fix: keep backtests out of runtime evidence`
- `6520636ad fix: align promotion gate paper history counts`
- `836cb42b7 fix: preserve paper evidence provenance`
- `f461a131c fix: require promotion evidence provenance`
- `1de9a3513 fix: stamp signal evidence provenance`

Active role: `ENGINEER`

Objective: make promotion evidence attributable, current-window based, and
separate from synthetic/backtest evidence.

What was found:
- SHOWN by commit history: the branch had repeated fixes around provenance,
  latest-window reporting, kill-switch recency, and paper-history counts.
- SHOWN by current gate output: current-window provenance is reported separately
  from all-time historical provenance diagnostics.

What changed:
- Signal evidence gained market-data provenance stamping.
- Unattributed signal evidence is skipped for promotion use.
- Promotion gates require non-sample provenance.
- Unknown provenance sources are reported.
- Latest-window evidence log status is reported.
- Kill-switch gate checks recency.
- Runtime evidence excludes backtest-derived evidence.
- Paper-history counts align with the trade journal.

Why this change:
- Promotion gates must not pass on synthetic, stale, or unattributed evidence.
- Latest-window checks prevent old bad/missing evidence from blocking a valid
  current evidence cycle while preserving diagnostics.

Expected outcome:
- Gate readiness is based on current, attributable paper evidence.
- Historical unknown/missing provenance remains visible as a diagnostic without
  automatically blocking the latest valid window.

Verification:
- SHOWN from later full-suite runs: full suite passed after these commits.
- UNVERIFIED: exact targeted command output for each individual commit is not in
  this retrospective.

Remaining risk:
- HIGH: promotion evidence logic.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through the 2026-05
  review-stabilized audit cycle; later gate/full-suite verification remained
  clean after these commits.

## 2026-05-18 to 2026-05-26 - Paper Campaign Monitor and Operator Workflow

Visible commits:
- `92c2c35d7 feat: show paper sim monitor in home digest`
- `6f7482623 feat: add paper sim desktop alert setting`
- `6fcf705f8 fix: surface paper sim notification truth`
- `c3f61c15b feat: add dashboard paper sim watch controls`
- `b6ade1c66 feat: add paper sim watch notifications`
- `ada32aa7d fix: break digest monitor import cycle`
- `215fe908d fix: tighten home digest paper sim monitor wiring`
- `9f8efe2c2 Update test_dashboard_home_digest.py`
- `92626d032 feat: surface paper_sim_monitor in home digest builder`
- `6dc87550c fix: reconcile stopped paper sim monitor summary`
- `b1a470534 fix: surface paper evidence persistence phase`
- `c965f9786 fix: name evidence persistence in monitor summary`
- `73bb81d4c fix: supervise paper evidence collection daily`
- `08793e700 fix: surface idle paper evidence collector state`

Active role: `ENGINEER`

Objective: reduce manual polling by making paper evidence collection and monitor
state visible through runtime status, dashboard, home digest, watches, and
notifications.

What was found:
- SHOWN by commit history and current runtime status: the repo has a managed
  daily paper evidence collector and a paper sim monitor.
- SHOWN by current status: collector can be idle while waiting for the next UTC
  day and still be healthy.

What changed:
- Home digest surfaces paper sim monitor state.
- Dashboard Operations exposes monitor watch controls.
- Paper sim monitor can write watch reports and local desktop notification
  status.
- Paper evidence collector runs in a managed daily-loop path.
- Runtime summaries distinguish idle, persisting evidence, completed, stopped,
  and notification states.

Why this change:
- The operator should not have to remember files or manually poll low-level
  artifacts to know whether the campaign is working.
- Watch reports and notifications turn important state changes into durable
  artifacts.

Expected outcome:
- Operator can see campaign and monitor status from dashboard/home surfaces.
- Meaningful events such as fills, position closes, campaign completion, and
  investigate recommendations are visible.

Verification:
- SHOWN from later full-suite runs: full suite passed after these commits.
- UNVERIFIED: exact targeted command output for every listed commit is not in
  this retrospective.

Remaining risk:
- HIGH: background job/operator workflow.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through the 2026-05
  review-stabilized audit cycle; later monitor/gate full-suite verification
  remained clean after these commits.

## 2026-05-18 to 2026-05-26 - Evidence Artifacts and Decision Records

Visible commits:
- `c1fbd6372 docs: add 2026-05-26 strategy decision record`
- `5ab5f3cee docs: refresh 2026-05-18 decision record`
- `27f6b8ab5 docs: add 2026-05-18 strategy decision record`
- `f73a3d069 docs: track master integration blocker`
- `89ee99159 fix: scope runtime ignore rules`
- `e3248ffff fix: restore script alignment wrappers`
- `ff2e3fba1 fix: bootstrap nested script entrypoints`
- `30d465ea7 fix: tolerate missing parity strategy config`

Active role: `ENGINEER`

Objective: keep evidence artifacts, decision records, ignore rules, and script
entrypoints aligned with the active branch state.

What was found:
- SHOWN by current docs: strategy decision records exist for 2026-05-18 and
  2026-05-26.
- SHOWN by commit history: runtime ignore rules, script wrappers, nested
  bootstraps, and missing parity strategy config were addressed.

What changed:
- Added/refreshed strategy decision records.
- Documented a master integration blocker.
- Scoped runtime ignore behavior.
- Restored alignment wrappers and nested script bootstrap paths.
- Tolerated missing parity strategy config.

Why this change:
- Decision records need to match canonical evidence, not temp proof artifacts.
- Script entrypoints and ignores must not create recurring git dirt or broken
  operator commands.

Expected outcome:
- Audit artifacts are tracked where appropriate.
- Temp/runtime artifacts do not recur as untracked git noise.
- Script paths remain runnable from documented entrypoints.

Verification:
- SHOWN from later full-suite runs: full suite passed after these commits.
- UNVERIFIED: exact targeted command output for every listed commit is not in
  this retrospective.

Remaining risk:
- LOW to MEDIUM: mostly documentation and compatibility, with some operational
  workflow impact.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through the 2026-05
  review-stabilized audit cycle; later branch verification remained clean after
  these commits.

## 2026-05-30 - PR #44 Integration Suite Repair

Active role: `ENGINEER`

Objective: repair the PR #44 `codex/master-review-stabilized-integration`
branch after the master integration full suite exposed regressions.

What was found:
- SHOWN: the original temporary integration worktree became prunable and no
  longer had a `.git` directory.
- SHOWN: the prunable directory still contained the interrupted repair edits,
  so it was treated as a recovery copy rather than deleted.
- SHOWN: `scripts.run_intent_executor` was missing at the root import path even
  though tests and runtime status writers import that canonical path.
- SHOWN: `scripts.run_ws_ticker_feed` used a star-import wrapper, so callers
  monkeypatching the root module did not affect the relocated implementation.
- SHOWN: `test_place_order_fail_closed.py` could read a repo-local
  `risk_sink_failed.flag`, masking the intended fail-closed assertions.
- SHOWN: older live-arming tests conflicted with the hardened policy: fresh
  persisted arming is valid, stale persisted arming is blocked.
- SHOWN: `LiveIntentQueueSQLite.upsert_intent` still mutated existing queued
  rows, conflicting with insert-only queue-authority expectations.
- SHOWN: paper reconciliation marked an intent filled before journal inserts,
  which could hide a fill-journal failure.

What changed:
- Recreated a clean integration worktree at
  `/private/tmp/cryptkeep-master-review-stabilized-integration-v2`.
- Added `scripts.run_intent_executor` compatibility aliasing to the relocated
  compat implementation.
- Converted the root `scripts.run_ws_ticker_feed` wrapper into an implementation
  module alias so CLI and imported behavior share one module object.
- Made live intent upsert insert-only for existing intent IDs; lifecycle changes
  remain under `update_status`.
- Reordered paper reconciliation so fills are journaled before an intent is
  marked filled.
- Isolated order fail-closed tests with per-test `CBP_STATE_DIR`.
- Updated older tests to the accepted live-arming persisted-state policy and to
  explicitly pass ticker symbol when environment defaults are irrelevant.

Why this change:
- The smallest safe repair was to preserve production fail-closed behavior and
  fix compatibility/test isolation around it.
- Deleting or bypassing `risk_sink_failed.flag` would have weakened a safety
  control; isolating tests proves the intended behavior without mutating
  operator state.
- Insert-only intent creation and journal-before-filled ordering keep state
  authority coherent in order/fill lifecycle paths.

Expected outcome:
- PR #44 can advance with the full suite green.
- Runtime import paths remain backward compatible after script relocation.
- Live/order fail-closed protections remain intact while tests no longer depend
  on repo-local runtime state.

Verification:
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_canonical_runtime_status_writers.py tests/test_intent_reconciler_fill_journal_order.py tests/test_live_arming_contract.py tests/test_live_arming_state_fallback.py tests/test_live_intent_upsert_insert_only.py tests/test_live_intent_queue_integrity.py tests/test_live_reconciler.py tests/test_place_order_fail_closed.py tests/test_run_ws_ticker_feed.py`
  was run from the integration worktree using the repository venv path and
  passed: `55 passed, 1 warning`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  was run from the integration worktree and passed:
  `2085 passed, 33 skipped, 13 warnings in 202.46s`.

Remaining risk:
- HIGH: master integration touches live/order/risk-adjacent lifecycle behavior
  and compatibility entrypoints.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-30 after PR #44 CI reported all checks passing and merge state
  `CLEAN`.

## 2026-05-30 - PR #44 Release Checklist Entrypoint Repair

Active role: `ENGINEER`

Objective: repair the PR #44 macOS PyInstaller CI failure after the integration
suite repair was pushed.

What was found:
- SHOWN: GitHub Actions macOS build failed before packaging work could run.
- SHOWN: the failing command was
  `python scripts/release_checklist.py --sync-requires --pyinstaller`.
- SHOWN: the repository had `scripts/release/release_checklist.py` but no root
  `scripts/release_checklist.py` compatibility entrypoint.
- SHOWN: after adding the root wrapper, dry-run exposed a relocated-script root
  bug: `scripts/release/release_checklist.py` resolved `ROOT` to `scripts/`,
  so it could not find repo-root `pyproject.toml`.

What changed:
- Added `scripts/release_checklist.py` as a root compatibility entrypoint.
- The wrapper executes `scripts.release.release_checklist` as `__main__` via
  `runpy` so the relocated script keeps its CLI behavior.
- Corrected `scripts/release/release_checklist.py` root calculation from
  `parent.parent` to `parents[2]`.
- Added a regression test that runs
  `scripts/release_checklist.py --dry-run` in a subprocess.

Why this change:
- The documented workflows and release docs all call the root
  `scripts/release_checklist.py` path.
- Fixing the entrypoint and underlying root calculation is smaller and safer
  than editing every workflow and doc path.
- `runpy` avoids importing and calling `main()` in a way that would bypass the
  relocated script's `__main__` setup.

Expected outcome:
- GitHub Actions can resolve the documented root release checklist command.
- The relocated release checklist can find repo-root release metadata.
- PyInstaller CI proceeds past the missing-file/root-resolution failure.

Verification:
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_remaining_compat_wrappers.py::test_release_checklist_root_wrapper_dry_run`
  passed: `1 passed`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/release_checklist.py --dry-run`
  passed and returned `ok=true`, `manifest_written=null`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/release/release_checklist.py --dry-run`
  passed and returned `ok=true`, `manifest_written=null`.
- UNVERIFIED: full PyInstaller packaging was not run locally because
  `--pyinstaller` writes build/release artifacts; GitHub CI remains the
  intended verification surface for that build.

Remaining risk:
- HIGH: release/desktop packaging CI path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-30 after PR #44 CI reported macOS and Windows desktop builds passing.

## 2026-05-30 - PR #44 Paper Runner Entrypoint Repair

Active role: `ENGINEER`

Objective: repair the remaining PR #44 CI failure in the main `validate`
workflow after desktop builds, sanity, ruff, mypy, and core pytest passed.

What was found:
- SHOWN: GitHub Actions main `validate` failed after the core pytest step
  passed with `1967 passed, 62 skipped`.
- SHOWN: the failing command was
  `python scripts/run_es_daily_trend_paper.py --dry-run`.
- SHOWN: the implementation exists at
  `scripts/dev/run_es_daily_trend_paper.py`, while CI and docs still call the
  historical root path.
- SHOWN: the CI workflow reads the root script source directly to assert the
  ManagedComponent contract marker `lock_dir=runtime_dir()`.

What changed:
- Added `scripts/run_es_daily_trend_paper.py` as a root compatibility
  entrypoint that delegates to `scripts.dev.run_es_daily_trend_paper`.
- Preserved the visible ManagedComponent contract marker in the root wrapper
  because the workflow intentionally checks the historical entrypoint source.
- Added a subprocess regression test for
  `scripts/run_es_daily_trend_paper.py --dry-run`.

Why this change:
- The CI and documentation contract is the root runner path.
- Restoring a compatibility wrapper is smaller and safer than editing multiple
  workflows and docs during master integration.
- Delegating with `runpy` avoids duplicating runner behavior.

Expected outcome:
- The main CI `Paper runner dry-run` step can resolve and execute the
  historical root runner path.
- The following workflow source-contract step still sees the expected
  ManagedComponent marker.

Verification:
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_remaining_compat_wrappers.py::test_es_daily_trend_paper_root_wrapper_dry_run`
  passed: `1 passed`.
- `CBP_STATE_DIR=/tmp/cbp_ci_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/run_es_daily_trend_paper.py --dry-run`
  passed and printed `DRY RUN: pre-flight passed. Stage=paper, kernel=allow`.
- Local reproduction of the CI ManagedComponent source-contract check passed:
  `ManagedComponent API contract: OK`.

Remaining risk:
- HIGH: paper-runner/operator workflow and CI integration path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-30 after PR #44 CI reported the main `validate` workflow passing.

## 2026-05-31 - Paper Gate Backtest Baseline Contract

Active role: `ENGINEER`

Objective: remove the ambiguity around the paper-gate checklist item requiring
observed win rate and average win/loss to be compared against backtest
expectations before `es_daily_trend_v1` can advance.

What was found:
- SHOWN: `scripts/check_promotion_gates.py --json` already surfaced
  `manual_review_required=true`.
- SHOWN: the gate included observed paper-history metrics for
  `sma_200_trend`: 7 closed trades, 14 fills, 28.6% win rate, +35.75 net
  realized PnL, +5.11 expectancy per closed trade.
- SHOWN: no machine-readable backtest baseline for `win_rate`, `avg_win`, and
  `avg_loss` existed in the strategy config, so the gate could only ask for
  manual comparison.

What changed:
- Added `promotion.paper.backtest_expectations` to
  `configs/strategies/es_daily_trend_v1.yaml` with `source`, `tolerance_pct`,
  `win_rate`, `avg_win`, and `avg_loss` fields.
- Updated `scripts/check_promotion_gates.py` so the paper gate reads those
  configured expectations, compares observed paper metrics against the
  configured tolerance, and marks the item as `machine_checked`,
  `machine_blocking`, or `manual_required`.
- Kept the current config values unset because no accepted closed-trade
  backtest baseline has been identified for `sma_200_trend`.
- Updated `docs/strategies/es_daily_trend_v1.md` and
  `docs/DECISION_FRAMEWORK.md` to document the config-backed baseline contract.
- Added tests for matching configured metrics, out-of-tolerance configured
  metrics, and the config contract existing before a baseline is accepted.

Why this change:
- The smallest safe fix is to create the machine-readable contract without
  inventing baseline numbers.
- A missing baseline must remain visible as `manual_review_required=true`;
  otherwise the gate can appear ready while the spec's performance-comparison
  item is still unresolved.

Expected outcome:
- When an accepted backtest baseline exists, the paper gate can compare
  observed paper metrics automatically.
- Until then, the gate remains blocked with explicit missing baseline fields
  and current observed paper metrics in JSON output.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_es_daily_trend.py`
  - SHOWN: `68 passed in 0.85s`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: `manual_review_required=true`.
  - SHOWN: missing baseline metrics are `win_rate`, `avg_win`, and `avg_loss`.
  - SHOWN: observed metrics include 7 closed trades, 14 fills, 28.6% win rate,
    +35.75 net realized PnL, and +5.11 expectancy per closed trade.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2095 passed, 33 skipped, 13 warnings in 382.38s`.

Remaining risk:
- HIGH: promotion-gate behavior for a financial strategy.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-31 after targeted and full-suite verification.

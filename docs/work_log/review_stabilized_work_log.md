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

## 2026-05-31 - Live Risk Limits Fail Closed From Runtime Config

Active role: `ENGINEER`

Objective: harden the live daily-loss risk-limit source of truth while
investigating the `daily_loss_halt_pct` wiring discrepancy.

What was found:
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` declares
  `daily_loss_halt_pct` as a percentage target.
- SHOWN: the live risk gate enforces absolute USD limits via
  `services/risk/live_risk_gates.py`.
- SHOWN: `LiveRiskLimits.from_trading_yaml()` read
  `canonical_runtime.json` directly and substituted broad hardcoded defaults
  when `risk.live.*` was absent.
- SHOWN: docs and a Phase 82 helper still referenced the removed
  `services/risk/live_risk_gates_phase82.py` path.

What changed:
- Changed `LiveRiskLimits.from_trading_yaml()` to load the canonical runtime
  trading config through `load_runtime_trading_config(path)`.
- Removed hardcoded fallback live-risk limits from that loader.
- Made missing or invalid `risk.live.*` return `None`, preserving fail-closed
  behavior in callers that block when limits are unavailable.
- Added regression tests proving the loader uses runtime config and fails
  closed when live risk limits are missing.
- Updated stale Phase 82 and strategy docs to point at
  `services/risk/live_risk_gates.py`.

Why this change:
- The percentage-to-USD translation still needs a separate accepted equity
  source; inventing that translation now would be unsafe.
- The smallest safety hardening is to prevent live risk gates from silently
  inventing default dollar limits when the canonical runtime config lacks
  explicit `risk.live.*` values.

Expected outcome:
- Live risk evaluation remains blocked when live dollar limits are missing or
  malformed.
- Operators see the current v1 contract clearly: strategy
  `daily_loss_halt_pct` is declarative, while live enforcement uses explicit
  `risk.live.max_daily_loss_usd`.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_live_risk_gates.py tests/test_placeholder_recovery_phase2.py tests/test_phase82_apply_safe_import.py tests/test_show_live_gate_inputs.py tests/test_live_executor_latency_safety_integration.py`
  - SHOWN: `43 passed in 0.90s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2097 passed, 33 skipped, 13 warnings in 355.48s`.

Remaining risk:
- HIGH: live risk-gate behavior and daily-loss safety control.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-31 after targeted and full-suite verification.

## 2026-06-01T09:19:28Z - SMA Backtest Parity Flat Exit

Active role: `ENGINEER`

Objective: make the parity backtest able to close `sma_200_trend` round trips
when the documented SMA rule flips from long to flat, without adding a new live
paper exit path.

What was found:
- SHOWN: `sma_200_trend` signal logic returns `flat` when price is below the
  SMA, but `signal_from_ohlcv()` keeps runtime `action=hold`.
- SHOWN: the paper runner owns position state and can emit sells from signal
  changes or the strategy-aware exit stack.
- SHOWN: historical paper orders include `sma_200_trend` sells with
  `signal_reason=sma200:long:...`, so not every closed paper trade was caused
  by the SMA flat signal.
- SHOWN: the 2026-05-26 `sma_200_trend` sell had
  `signal_reason=sma200:flat:regime:trending` and no persisted `exit_reason`,
  so the runtime path already has distinct exit behavior from the parity
  backtest simulator.
- SHOWN: `sample_data/ohlcv/BTC_USDT_1d.json` still produces 1 buy, 0 sells,
  and 0 closed trades for the default SMA path, so it is not a valid
  closed-trade baseline fixture.

What changed:
- Left `services/strategies/es_daily_trend.py::signal_from_ohlcv()` runtime
  behavior unchanged: a flat SMA signal still returns `action=hold`.
- Added a backtest-only translation in
  `services/backtest/parity_engine.py`: when the simulated strategy is already
  long, the strategy is `sma_200_trend`, and the computed signal is `flat`, the
  simulator treats that bar as a sell.
- Added a regression test proving `run_parity_backtest()` can close an SMA
  round trip on a flat signal.
- Added a regression test proving the runtime adapter still returns `hold` for
  flat, preserving live paper signal semantics.

Why this change:
- Changing the registry adapter to emit `sell` would alter live paper behavior
  and potentially introduce a second exit path.
- The smallest safe change is to fix the simulator's position-aware
  interpretation of the documented flat/exit condition while leaving runtime
  exit ownership unchanged.

Expected outcome:
- Backtest parity can now produce closed-trade metrics for `sma_200_trend`
  when the input OHLCV window contains both above-SMA entry and below-SMA exit
  participation.
- Live paper behavior is unchanged by this patch.
- The existing sample OHLCV remains insufficient as a closed-trade baseline;
  a deterministic SMA CI fixture is still required as separate work.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_es_daily_trend.py tests/test_backtest_parity_engine.py tests/test_strategy_registry.py`
  - SHOWN: `50 passed in 0.54s`.
- `./.venv/bin/python -m pytest -q tests/test_campaign_summary.py tests/test_es_signal_regression.py tests/test_paper_engine_integration.py tests/test_run_paper_strategy_evidence_collector.py tests/test_dashboard_strategy_evaluation.py`
  - SHOWN: `46 passed in 0.98s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2099 passed, 33 skipped, 13 warnings in 388.18s`.
- Sample OHLCV proof:
  - SHOWN: `ok=true`, `bars=230`, `buy_count=1`, `sell_count=0`,
    `closed_trades=0`.

Remaining risk:
- HIGH: financial backtest semantics for a promoted paper strategy.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-01 after targeted verification and fresh full-suite verification
  reported `2099 passed, 33 skipped, 13 warnings in 372.93s`.

## 2026-06-01T09:35:12Z - SMA 200 CI Round-Trip Fixture

Active role: `ENGINEER`

Objective: add a deterministic CI-only OHLCV fixture that proves the default
`sma_200_trend` parity path can produce a buy-to-sell round trip.

What was found:
- SHOWN: the previous parity fix made flat SMA exits possible in the backtest
  simulator, but the existing sample OHLCV still produced 1 buy, 0 sells, and
  0 closed trades for the default SMA path.
- SHOWN: there was no dedicated `sma_200_trend` fixture under
  `sample_data/ohlcv/` that intentionally crossed back below SMA-200 after
  entry.

What changed:
- Added `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json`, a synthetic
  220-bar OHLCV sequence with 200 warmup bars, an above-SMA entry window, and a
  below-SMA exit window.
- Added a parity-engine regression test that loads the fixture and asserts one
  buy, one sell, one closed trade, an SMA long entry reason, an SMA flat exit
  reason, and scorecard fields needed by the manual review gate.

Why this change:
- A dedicated fixture is the smallest way to make the CI proof deterministic
  without treating synthetic data as promotion evidence.
- Keeping the fixture in `sample_data/ohlcv/` makes its purpose explicit and
  avoids changing live paper runtime behavior or strategy configuration.

Expected outcome:
- CI can prove `sma_200_trend` backtest mechanics for both entry and exit under
  default SMA parameters.
- The fixture remains a synthetic mechanics check only; it does not prove
  profitability, live readiness, or paper-promotion eligibility.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_backtest_parity_engine.py tests/test_es_signal_regression.py`
  - SHOWN: `14 passed in 0.29s`.
- `./.venv/bin/python -m pytest -q tests/test_backtest_parity_engine.py tests/test_es_daily_trend.py tests/test_strategy_registry.py`
  - SHOWN: `51 passed in 0.45s`.

Remaining risk:
- LOW: synthetic fixture and test coverage only; no runtime strategy, order
  routing, evidence-gate, or live execution behavior changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: same-thread low-risk closure after targeted regression
  verification.

## 2026-06-01T09:39:51Z - Post-Integration Master Catch-Up PR

Active role: `GATE`

Objective: preserve the accepted post-PR44 `review-stabilized` work in a
reviewable master catch-up PR without merging high-risk gate/risk changes
directly.

What was found:
- SHOWN: `origin/master` is an ancestor of `review-stabilized`.
- SHOWN: `git rev-list --left-right --count origin/master...review-stabilized`
  reported `0 5`, meaning `review-stabilized` is 5 commits ahead of
  `origin/master` with no new master-only commits.
- SHOWN: the ahead commits are `f6a67ef68`, `c9cd496b8`, `706e9468e`,
  `a3235229a`, and `e4ad5d99c`.
- SHOWN: `gh pr list --base master --head review-stabilized --state open`
  returned no existing open PR for this delta.

What changed:
- Created draft PR #45:
  `https://github.com/Ddthomas415/CryptKeep/pull/45`.
- Verified PR #45 is open, draft, targets `master`, uses
  `review-stabilized` as head, and reports `mergeable=MERGEABLE`.

Why this change:
- The old master-integration conflict debt was already resolved by PR #44, but
  five later accepted commits were still only on `review-stabilized`.
- A draft PR is the smallest safe handoff surface: it makes the delta visible
  without bypassing independent review or CI for high-risk financial gate and
  risk-control changes.

Expected outcome:
- Reviewers can evaluate the exact post-integration delta before master moves
  again.
- Master remains unchanged until PR #45 receives independent review and fresh
  CI/full-suite confirmation.

Verification:
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2100 passed, 33 skipped, 13 warnings in 367.83s`.
- Final PR-head gate run after pushing the acceptance record:
  `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2100 passed, 33 skipped, 13 warnings in 370.35s`.
- `gh pr view 45 --json number,title,state,isDraft,headRefName,baseRefName,url,mergeable`
  - SHOWN: PR #45 is `OPEN`, `isDraft=true`, `baseRefName=master`,
    `headRefName=review-stabilized`, and `mergeable=MERGEABLE`.
- `git status --short --branch`
  - SHOWN: `review-stabilized...origin/review-stabilized` before this
    work-log entry.

Remaining risk:
- HIGH: PR #45 contains promotion-gate, live risk-gate, and financial backtest
  semantics changes.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-01, with full-suite verification shown above.
- Gate outcome: PR #45 is ready to mark non-draft and merge after the final
  PR-head full-suite result shown above. This line is a docs-only proof update;
  no code or runtime behavior changed after the final suite run.

## 2026-06-03T00:34:50Z - Master Branch Protection Runbook

Active role: `ENGINEER`

Objective: remove ambiguous GitHub check names and document the required
`master` branch-protection settings after PR #45 proved the branch was
unprotected.

What was found:
- SHOWN: PR #45 merged into `master` while one GitHub `validate` workflow was
  still pending.
- SHOWN: the pending workflow later passed, but merge ordering showed that
  GitHub was not enforcing all expected checks before master updates.
- SHOWN: `gh api repos/Ddthomas415/CryptKeep/branches/master/protection`
  returned `Branch not protected`.
- SHOWN: two workflows exposed a job named `validate`, making a required-check
  rule ambiguous.

What changed:
- Added explicit check names for the always-on CI jobs:
  `CI validate`, `CI sanity`, and `Governance smoke`.
- Renamed the path-filtered script integrity job from generic `validate` to
  `script-path-integrity`.
- Added `docs/GITHUB_BRANCH_PROTECTION.md` with the required `master`
  protection settings and the exact status checks that should be required.

Why this change:
- Branch protection itself is external GitHub configuration, not repository
  code.
- The smallest safe repo-side fix is to make required check names unambiguous
  and document the external setting needed to prevent another pending-check
  merge.
- The path-filtered check is documented as non-global because requiring it for
  every PR would block unrelated changes where that workflow does not run.

Expected outcome:
- Future branch-protection setup can require the main CI jobs without confusing
  the main CI `validate` job with the path-filtered script integrity job.
- A reviewer or admin can audit `master` protection against a visible repo
  runbook instead of relying on chat history.

Verification:
- `./.venv/bin/python -c "import pathlib, yaml; [yaml.safe_load(p.read_text()) for p in pathlib.Path('.github/workflows').glob('*.yml')]; print('workflow_yaml_ok')"`
  - SHOWN: `workflow_yaml_ok`.
- `./.venv/bin/python scripts/validate.py --quick`
  - SHOWN: repo doctor and alignment guard passed.
  - SHOWN: quick pytest subset reported `13 passed in 1.33s`.
- `git diff --check`
  - SHOWN: no whitespace errors.
- PR #46 GitHub checks after independent review:
  - SHOWN: `CI validate` passed in `8m45s`.
  - SHOWN: `CI sanity` passed in `4m29s`.
  - SHOWN: `Build (macos-latest)` passed in `1m21s`.
  - SHOWN: `Build (windows-latest)` passed in `2m22s`.
  - SHOWN: `Governance smoke`, `script-path-integrity`, and
    `GitGuardian Security Checks` passed.

Remaining risk:
- MEDIUM: CI/governance workflow naming and external repository protection.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03, with PR #46 CI passing under the new explicit check names.
- Remaining action: merge PR #46, align `review-stabilized` with `master`, then
  configure GitHub branch protection using `docs/GITHUB_BRANCH_PROTECTION.md`.

## 2026-06-03T01:02:12Z - Master Branch Protection Applied

Active role: `GATE`

Objective: apply the documented `master` branch protection after PR #46 merged
with explicit CI check names.

What was found:
- SHOWN: PR #46 merged into `master` with merge commit
  `be005450ec99258046788b9729f7b060fcdc6bde`.
- SHOWN: `origin/master` and `origin/review-stabilized` were aligned at the PR
  #46 merge commit before applying protection.
- SHOWN: GitHub branch protection was previously absent on `master`.

What changed:
- Applied GitHub branch protection to `master` through the GitHub API.
- Required status checks are now strict and include:
  `CI validate`, `CI sanity`, `Governance smoke`, `Build (macos-latest)`,
  `Build (windows-latest)`, and `GitGuardian Security Checks`.
- Enabled admin enforcement.
- Required pull-request review with one approving review.
- Disabled force pushes and branch deletion.
- Left linear history disabled because audited integration PRs use merge
  commits.

Why this change:
- PR #45 proved `master` could advance before all expected checks completed.
- The branch-protection runbook merged in PR #46 made the required settings
  explicit; applying them closes the external GitHub governance gap.

Expected outcome:
- `master` can no longer be advanced through the GitHub PR path until required
  checks are green and at least one PR approval exists.
- Future master updates should use PRs and will expose missing or renamed check
  contexts immediately.

Verification:
- `gh api repos/Ddthomas415/CryptKeep/branches/master/protection`
  - SHOWN: `required_status_checks.strict=true`.
  - SHOWN: required contexts are `CI validate`, `CI sanity`,
    `Governance smoke`, `Build (macos-latest)`, `Build (windows-latest)`,
    and `GitGuardian Security Checks`.
  - SHOWN: `enforce_admins.enabled=true`.
  - SHOWN: `required_approving_review_count=1`.
  - SHOWN: `allow_force_pushes.enabled=false`.
  - SHOWN: `allow_deletions.enabled=false`.
- `git rev-list --left-right --count origin/master...origin/review-stabilized`
  - SHOWN: `0 0` before this work-log-only follow-up commit.

Remaining risk:
- MEDIUM: external GitHub repository setting, not version-controlled source.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03 before applying the documented branch protection.
- Residual risk: this work-log-only record still needs to land through a PR
  because direct `master` updates are now blocked by the protection just
  applied.

## 2026-06-03T16:28:16Z - Strategy Backlog Additions

Active role: `ENGINEER`

Objective: record the operator request to track a higher-turnover daily/weekly
strategy and short-market strategy work as future backlog, without changing
runtime behavior.

What was found:
- SHOWN: `sma_200_trend` remains a long/flat daily strategy with slow turnover.
- SHOWN: `docs/strategies/es_daily_trend_v1.md` states the current v1 universe
  is one instrument and no expansion happens until paper/shadow gates pass.
- SHOWN: the repo already has strategy candidates such as `ema_cross`,
  `breakout_donchian`, and `mean_reversion_rsi`.

What changed:
- Added Priority 11 to
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` for a
  higher-turnover daily/weekly strategy plan.
- Added Priority 12 to the same checkpoint for short-market strategy research.

Why this change:
- The operator wants the repo roadmap to include strategies better aligned with
  daily/weekly opportunity capture, while preserving the current
  `sma_200_trend` evidence campaign.
- Short-market work changes risk symmetry and should be tracked as a separate
  research stream, not as a parameter tweak to the current long/flat strategy.

Expected outcome:
- Future work can prioritize a paper-only higher-turnover strategy plan and a
  separate short-side research spec without interrupting the current paper gate.
- Short-side strategy work remains explicitly gated behind research, paper
  evidence, risk controls, and operator review.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration behavior
  changed.

Remaining risk:
- HIGH: financial strategy direction and future promotion behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03.
- Remaining action: backlog items remain pending future implementation and must
  stay paper/research-scoped until separately reviewed.

## 2026-06-03T16:45:38Z - Pattern And Hybrid Strategy Backlog

Active role: `ENGINEER`

Objective: record the operator-requested pattern-recognition and hybrid
strategy recommendations as future backlog, without changing runtime behavior.

What was found:
- SHOWN: `services/strategies/strategy_registry.py` includes
  `pullback_recovery` in the supported runtime registry.
- SHOWN: `pullback_recovery` is not listed in the current aggregate leaderboard
  rows from `strategy_evidence.latest.json`.
- SHOWN: context-pattern modules exist for `order_book_imbalance`,
  `open_interest_shift`, and `funding_extreme`, but they are not equivalent to
  the standard OHLCV registry path.
- SHOWN: consensus support exists, but the current path scores stored signals
  and reliability; it is not yet a clean backtestable composite strategy
  wrapper.

What changed:
- Added Priority 13 to
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` for pattern
  and hybrid strategy roadmap work.
- Captured `pullback_recovery` leaderboard/evidence evaluation as the first
  recommended pattern-strategy task.
- Captured later candlestick strategy work and context-pattern data plumbing as
  separate follow-up tracks.

Why this change:
- `pullback_recovery` is the lowest-infrastructure way to evaluate pattern-like
  price action using existing code.
- Hybrid and context-pattern strategies are higher-risk design work and should
  be specified before implementation or paper campaigns.

Expected outcome:
- The repo backlog now separates near-term pattern activation
  (`pullback_recovery`) from later candlestick recognition, context-pattern
  data plumbing, and composite/hybrid strategy design.
- Future strategy work can proceed through paper-only evidence gates without
  interrupting the current `sma_200_trend` campaign.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration behavior
  changed.

Remaining risk:
- HIGH: financial strategy direction and future promotion behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03.
- Remaining action: roadmap items remain pending future implementation and must
  receive separate review before any trading behavior changes.

## 2026-06-03T16:57:09Z - Infrastructure Activation Audit Backlog

Active role: `ENGINEER`

Objective: record the operator request to investigate underused repo
infrastructure and determine how much of the repo is actually wired into the
current operating path.

What was found:
- SHOWN: the current active campaign remains focused on `sma_200_trend`,
  `BTC/USDT`, paper evidence collection, gate checks, and paper sim monitoring.
- SHOWN: the repo contains additional infrastructure in areas such as
  `services/ai_engine`, `services/signals`, `services/ai_copilot`,
  `services/alerts`, `services/learning`, dashboard pages, desktop surfaces,
  and operator scripts.
- SHOWN: some of those systems are partially wired through scripts, dashboard
  pages, tests, or selectors, so labeling all of them "unused" would be too
  broad without a structured inventory.

What changed:
- Added Priority 14 to
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` for a repo
  infrastructure activation audit.
- The backlog item requires each subsystem to be classified as `active`,
  `partially_wired`, `dormant`, `research_only`, `superseded`, or
  `unsafe_to_enable`.
- The backlog item requires a prioritized activation roadmap while keeping the
  current `sma_200_trend` campaign isolated.

Why this change:
- The operator wants the repo to be used more completely, but "turn everything
  on" is not a safe engineering strategy for trading infrastructure.
- A visible infrastructure audit gives the project a way to identify dormant
  value, remove confusion, and choose activation order based on evidence and
  risk.

Expected outcome:
- Future work can inventory and prioritize repo infrastructure without mixing
  unvalidated systems into the current evidence campaign.
- The project gains a durable map of which systems are active, partially wired,
  dormant, superseded, or unsafe to enable.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration behavior
  changed.

Remaining risk:
- HIGH: repository architecture, operational workflow, and future trading
  automation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03.
- Remaining action: perform the subsystem-by-subsystem infrastructure inventory
  before enabling dormant or partially wired systems.

## 2026-06-03T17:00:00Z - Initial Infrastructure Activation Audit

Active role: `AUDITOR`

Objective: perform the first-pass infrastructure activation audit requested by
the operator and produce a visible artifact for independent review.

What was found:
- SHOWN: `docs/GOLDEN_PATH.md` identifies the canonical runtime as the managed
  `sma_200_trend` paper campaign and its monitor/gate surfaces.
- SHOWN: `docs/ARCHITECTURE.md` documents the signal/candidate layer as
  paper-only and evidence accumulation phase.
- SHOWN: `docs/ARCHITECTURE.md` marks transitional service families as frozen
  and says not to add new callers.
- SHOWN: repo directories exist for AI engine, signals/candidates, AI copilot,
  alerts, learning/feedback, desktop/service management, dashboard pages, and
  operator scripts.

What changed:
- Added `docs/checkpoints/infrastructure_activation_audit_2026_06_03.md`.
- Updated the Priority 14 checkpoint status to point at the new audit artifact
  and require independent review before activation work.

Why this change:
- The operator asked to investigate underused repo infrastructure.
- A visible audit artifact is safer than enabling dormant systems opportunistically.
- The current evidence campaign must stay isolated while infrastructure is
  inventoried and prioritized.

Expected outcome:
- Reviewers have a concrete subsystem classification table and activation order.
- Future activation work can start from the safest high-leverage item instead
  of trying to use the entire repo at once.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration behavior
  changed.

Remaining risk:
- HIGH: repository architecture, operational workflow, and future trading
  automation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: activation work remains pending and must be implemented as
  separate scoped changes with proof and review.

## 2026-06-04T13:25:45Z - Infrastructure Activation Audit Second Pass

Active role: `ENGINEER`

Objective: record the corrected second-pass infrastructure sweep and turn the
operator-script visibility gap into a separate backlog item.

What was found:
- SHOWN: `docs/OBJECTIVE.md` describes a larger product than the current
  `sma_200_trend` paper campaign, including learning/adaptive capabilities,
  multi-exchange support, safety controls, and a cross-platform installable app.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` still has null
  backtest expectation fields for `win_rate`, `avg_win`, and `avg_loss`.
- SHOWN: root `scripts/` contains 90 Python files in this checkout, not 88.
- SHOWN: several earlier hard claims needed correction: the old paper-runner
  importer counts were not reproduced from visible source imports,
  `signal_library` and `market_ranker` are wired through the candidate engine,
  `ws_feature_blacklist` is imported by the WebSocket ticker feed, and shadow
  gates are implemented directly rather than through missing threshold dicts.

What changed:
- Added a "Second-Pass Corrections - 2026-06-04" section to
  `docs/checkpoints/infrastructure_activation_audit_2026_06_03.md`.
- Updated the audit recommendation to include Golden Path/script-index
  alignment as a visible operator-command-map task.
- Updated Priority 14 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to show that
  the initial audit was accepted and the second-pass corrections now need
  independent review.
- Added Priority 15 for Golden Path and script-index alignment.

Why this change:
- The pasted second sweep was directionally useful but contained over-broad
  dormancy labels and unreproduced counts.
- Recording the corrections prevents future activation work from relying on
  inaccurate evidence.
- The script visibility gap is actionable and safer to address before enabling
  broader repo infrastructure.

Expected outcome:
- Reviewers get a corrected infrastructure activation artifact.
- Future work can proceed from a more reliable subsystem map.
- Operators get a dedicated follow-up task to make safe daily commands,
  diagnostics, emergency tools, and research scripts visible in one command map.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration
  behavior changed.

Remaining risk:
- HIGH: repository architecture, operator workflow, and future trading
  automation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: activation work remains pending and must be implemented as
  separate scoped changes with proof and review.

## 2026-06-04T13:31:57Z - Golden Path And Script Index Alignment

Active role: `ENGINEER`

Objective: make the root script surface visible to operators without broadening
the Golden Path or changing runtime behavior.

What was found:
- SHOWN: `docs/GOLDEN_PATH.md` documented the narrow daily paper-campaign path
  but did not point operators to the full script command map.
- SHOWN: `scripts/SCRIPTS.md` listed only a small canonical operator subset.
- SHOWN: root `scripts/` contains 90 Python entrypoints.
- SHOWN: the existing script-path validator parses the `## Canonical Operator`
  section in `scripts/SCRIPTS.md` and verifies listed scripts exist.

What changed:
- Expanded `scripts/SCRIPTS.md` into an operator-facing script index.
- Preserved the `## Canonical Operator` table for validator compatibility and
  safe daily operation.
- Added classified sections for paper runtime internals, service control,
  safety/reconciliation, market data/exchange connectivity, research/model
  tools, validation/release helpers, and desktop/UI scripts.
- Updated `docs/GOLDEN_PATH.md` to point to `scripts/SCRIPTS.md` for the full
  command map while keeping the Golden Path narrow.
- Updated Priority 15 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to
  implementation-proof-ready pending independent review.

Why this change:
- Operators should not have to infer which scripts are safe daily commands and
  which are specialized, live-adjacent, or research-only tools.
- A visible command map reduces operator-memory burden without activating any
  dormant system or changing trading behavior.
- Keeping the Golden Path narrow prevents specialized scripts from being
  mistaken for the daily evidence-campaign path.

Expected outcome:
- `docs/GOLDEN_PATH.md` remains the current daily path.
- `scripts/SCRIPTS.md` becomes the authoritative root script command map.
- Future script additions/removals have a clear documentation surface to update.

Verification:
- `./.venv/bin/python scripts/validate_script_paths.py`
  - SHOWN: `OK: script paths validated`.
- `./.venv/bin/python -c '...'`
  - SHOWN: `{'script_count': 90, 'missing': []}`.
- `git diff --check`
  - SHOWN: passed with no output.

Remaining risk:
- MEDIUM: operator workflow and documentation accuracy.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: keep `scripts/SCRIPTS.md` aligned with root script
  entrypoint additions/removals.

## 2026-06-04T13:38:21Z - Daily Loss Halt Contract Alignment

Active role: `ENGINEER`

Objective: close the stale `daily_loss_halt_pct` documentation gap without
changing runtime risk-gate behavior.

What was found:
- SHOWN: `docs/strategies/es_daily_trend_v1.md` states that
  `daily_loss_halt_pct` is declarative in v1 and live enforcement comes from
  `services/risk/live_risk_gates.py` using `risk.live.max_daily_loss_usd`.
- SHOWN: `services/risk/live_risk_gates.py` loads `risk.live.*` through the
  canonical runtime trading config and returns `None` for missing or invalid
  live limits, preserving fail-closed behavior in callers.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` still contained a stale
  comment pointing at the removed `services/risk/live_risk_gates_phase82.py`
  path.
- SHOWN: Priority 6 still said the daily-loss-halt discrepancy was pending even
  though the v1 declarative-vs-enforced contract had already been documented
  and accepted in earlier review.

What changed:
- Updated the `configs/strategies/es_daily_trend_v1.yaml` comment so it points
  at `services/risk/live_risk_gates.py` and the explicit
  `risk.live.max_daily_loss_usd` source of truth.
- Updated Priority 6 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to
  implementation-proof-ready pending independent review of the v1 safety
  contract.

Why this change:
- The smallest safe fix is to align the operator-facing config comment with the
  accepted runtime contract.
- Wiring a percentage-to-USD translation without an accepted equity source would
  be unsafe and broader than this defect.
- Leaving the stale Phase 82 path in the strategy config could mislead future
  safety reviews.

Expected outcome:
- The strategy spec and strategy config now describe the same v1 daily-loss
  halt contract.
- Operators and reviewers can see that the percentage target is declarative and
  the live gate is enforced from explicit runtime USD limits.
- Future equity-to-USD translation remains a separate high-risk implementation
  task.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_live_risk_gates.py tests/test_es_daily_trend.py`
  - SHOWN: `51 passed in 0.43s`.
- `grep -RIn "live_risk_gates_phase82.py" configs/strategies docs/strategies services/risk --include='*.yaml' --include='*.yml' --include='*.md' --include='*.py'`
  - SHOWN: no matches in current strategy config/spec/risk paths.
- `git diff --check`
  - SHOWN: passed with no output.

Remaining risk:
- HIGH: risk controls and safety enforcement.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: keep the config percentage target and runtime USD limit
  manually consistent until an accepted equity-to-USD translation exists.

## 2026-06-04T13:43:52Z - SMA Round-Trip Fixture Backlog Reconciliation

Active role: `ENGINEER`

Objective: remove a stale backlog item after verifying the deterministic
`sma_200_trend` CI fixture already exists and is covered by tests.

What was found:
- SHOWN: Priority 10 still listed the `sma_200_trend` CI fixture as pending.
- SHOWN: `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json` exists.
- SHOWN: `tests/test_backtest_parity_engine.py` asserts the fixture has 220
  bars, one buy, one sell, one closed trade, SMA long/flat reasons, and
  scorecard fields.
- SHOWN: commit `e4ad5d99c` added the fixture and regression test and had
  already been accepted in the work log.

What changed:
- Updated Priority 10 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` from pending
  to complete as of `e4ad5d99c`.
- Clarified that the fixture remains a synthetic mechanics test, not
  promotion-gate or profitability evidence.

Why this change:
- Leaving completed work in the pending backlog causes duplicate work and
  confusion about the next real blocker.
- The correct action was backlog reconciliation, not another fixture.

Expected outcome:
- The proactive task list no longer points operators or agents at already
  completed CI-hardening work.
- Future `sma_200_trend` semantic changes have a clear fixture/test pair to
  update.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_backtest_parity_engine.py tests/test_es_daily_trend.py`
  - SHOWN: `41 passed in 0.58s`.
- `wc -l sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json`
  - SHOWN: `1762`.
- `git show --stat --oneline e4ad5d99c`
  - SHOWN: the commit added
    `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json`,
    `tests/test_backtest_parity_engine.py`, and the work log.

Remaining risk:
- LOW: documentation/backlog reconciliation only.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: same-thread low-risk closure after targeted
  verification.
- Remaining action: none for Priority 10.

## 2026-06-04T14:16:45Z - Branch Protection Admin Bypass Policy

Active role: `ENGINEER`

Objective: document the intended branch-protection bypass policy after PR #47
was merged by the human repo admin through the GitHub UI bypass path.

What was found:
- SHOWN: PR #47 merged into `master` at `2026-06-04T14:10:41Z` with merge
  commit `5317e58326c440d32561c57b09eb2499944a03f3`.
- SHOWN: all PR #47 required checks were passing before merge.
- SHOWN: the PR was authored by `Ddthomas415`, and the authenticated GitHub
  account available to this agent was also `Ddthomas415`, so a same-account
  self-review could not satisfy the branch-protection review requirement.
- SHOWN: the human operator reported using the visible GitHub web UI bypass
  path to merge after accepting the audit cycle.
- SHOWN: `origin/master` and `origin/review-stabilized` were reconciled to the
  same merge commit after PR #47 merged.

What changed:
- Updated `docs/GITHUB_BRANCH_PROTECTION.md` to document that administrator
  bypass is intentionally allowed for the solo-project workflow.
- Added policy language stating that AI-agent workflows must not use CLI
  admin-bypass flags.
- Added the audit-note requirements for any future admin-bypass merge.

Why this change:
- The protection rule is intentionally asymmetric: it blocks AI/non-admin
  self-merges while preserving a human owner/admin escape hatch for accepted
  solo-project work.
- Without documenting this, the disabled admin-enforcement setting could look
  accidental instead of deliberate.

Expected outcome:
- Future reviewers understand why administrator bypass is allowed and when it
  may be used.
- AI-agent workflows have an explicit rule not to use admin bypass from the CLI.
- Future bypass merges have a visible PR audit-note standard.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration
  behavior changed.

Remaining risk:
- MEDIUM: governance/runbook documentation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: none for the documented admin-bypass policy.

## 2026-06-05T19:28:41Z - EMA Cross Paper Challenger Plan

Active role: `ENGINEER`

Objective: turn the higher-turnover daily/weekly strategy backlog item into a
concrete paper-only challenger plan without disturbing the active
`sma_200_trend` campaign.

What was found:
- SHOWN: Priority 11 requested a dedicated paper-only strategy plan with
  candidate, timeframe, turnover expectations, risk cap, evidence gate,
  backtest baseline, and isolation rules.
- SHOWN: `ema_cross_default` already exists in `services/strategies/presets.py`
  with `ema_fast=12`, `ema_slow=26`, and post-cross filters.
- SHOWN: `docs/strategies/ema_cross_research_note_2026-03-26.md` did not
  justify shortening the EMA pair; deterministic windows favored default
  `12/26`.
- SHOWN: `scripts/run_paper_strategy_evidence_collector.py --help` exposes the
  command surface needed for an isolated `ema_cross` proof.
- SHOWN: `CBP_STATE_DIR` is the repo-supported state isolation mechanism.

What changed:
- Added `docs/checkpoints/ema_cross_challenger_plan_2026_06_05.md`.
- Updated Priority 11 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` from pending
  strategy design to implementation-proof-ready.
- Defined the first proof as an isolated one-shot run for `ema_cross_default`
  using `public_ohlcv_5m` and a separate `CBP_STATE_DIR`.
- Defined paper-only evidence gates, isolation checks, risk caps, and decision
  rules.

Why this change:
- The active `sma_200_trend` campaign should keep running passively, but its
  slow turnover is structurally mismatched with the operator's faster evidence
  and daily/weekly opportunity objective.
- Planning the challenger first avoids contaminating canonical
  `es_daily_trend_v1` evidence or starting another background campaign before
  state isolation is proven.
- The existing `ema_cross_default` preset is the smallest defensible starting
  point because the repo already rejected an unsupported shorter EMA change.

Expected outcome:
- Operators have a concrete next step for testing a higher-turnover strategy
  without touching the current promotion gate.
- The first challenger run can prove command surface, public OHLCV provenance,
  artifact routing, and journal isolation before any persistent daily loop is
  launched.
- Future `ema_cross` evidence remains separate from `es_daily_trend_v1`
  promotion evidence.

Verification:
- `git diff --check`
  - SHOWN: passed with no output.
- `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --help`
  - SHOWN: command succeeded and exposed `--strategies`,
    `--session-strategy-id`, `--symbol`, `--venue`, `--signal-source`,
    `--runtime-sec`, `--daily-loop`, and `--status`.

Remaining risk:
- HIGH: financial strategy selection and future promotion behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 before the isolated Stage 0 challenger proof.
- Remaining action: completed by the Stage 0 isolated proof entry below.

## 2026-06-05T19:50:25Z - EMA Cross Stage 0 Isolated Proof

Active role: `ENGINEER`

Objective: run the accepted Stage 0 one-shot proof for `ema_cross_default`
without disturbing canonical `es_daily_trend_v1` paper evidence.

What was found:
- SHOWN: before the challenger proof, `check_promotion_gates.py --json`
  reported canonical `es_daily_trend_v1` at `7/10` round trips, `14` fills,
  latest fill `2026-05-26T00:00:09.780106+00:00`, and
  `expectancy_per_closed_trade=$5.11`.
- SHOWN: the canonical evidence collector daily loop was alive and idle,
  waiting for the next UTC day.
- SHOWN: the first sandboxed challenger attempt could not fetch public OHLCV;
  `app.log` repeated `ohlcv_live_fetch_failed` for Coinbase and runner status
  reported `note=no_public_ohlcv`.
- SHOWN: rerunning the proof with network access enabled public OHLCV:
  runner status showed `bars=299`, populated `mid`, `signal_source=public_ohlcv_5m`,
  and `signal_reason=no_cross`.
- SHOWN: the isolated proof completed normally with `stop_reason=runtime_elapsed`.

What changed:
- Ran an isolated one-shot proof with
  `CBP_STATE_DIR=.cbp_state_challengers/ema_cross_default_stage0_20260605T1935Z`.
- Added `/.cbp_state_challengers/` to `.gitignore` so isolated proof state does
  not remain as untracked Git noise.
- No trading source code, strategy preset, gate threshold, or canonical
  `.cbp_state` artifact was modified.

Why this change:
- The accepted plan required Stage 0 proof before any persistent challenger
  daily loop.
- A fresh timestamped state directory avoided mixing the restricted failed
  attempt with the network-enabled proof artifacts.
- Ignoring `.cbp_state_challengers/` preserves the intended local-runtime
  boundary and prevents recurring untracked runtime artifacts.

Expected outcome:
- `ema_cross_default` has a verified isolated startup/status/shutdown proof on
  live Coinbase public OHLCV.
- Future challenger runs can use separate state directories without creating
  Git noise.
- Canonical `es_daily_trend_v1` promotion evidence remains isolated from
  challenger experiments.

Verification:
- Restricted attempt:
  - SHOWN: stopped cleanly after `117.89s`, `fills_total=0`,
    `closed_trades_total=0`, and only isolated session evidence.
- Network-enabled attempt:
  - SHOWN: collector completed at `2026-06-05T19:49:34.715316+00:00`.
  - SHOWN: result `runtime_sec=903.4889707565308`, `stop_reason=runtime_elapsed`,
    `signal_action=hold`, `signal_changed=false`, `enqueued_total=0`,
    `fills_total=0`, `closed_trades_total=0`, `net_realized_pnl_total=0.0`.
  - SHOWN: isolated session artifact has `market_data_source=public_ohlcv`,
    `ohlcv_sample_mode=false`, `ohlcv_timeframe=5m`, `ohlcv_venue=coinbase`,
    `ohlcv_symbol=BTC/USDT`, and `strategy_id=ema_cross_default`.
  - SHOWN: isolated state wrote
    `.cbp_state_challengers/ema_cross_default_stage0_20260605T1935Z/data/snapshots/ohlcv_coinbase_BTC_USDT_5m.json`.
- Canonical isolation:
  - SHOWN: after the challenger proof, `check_promotion_gates.py --json`
    still reported canonical `es_daily_trend_v1` at `7/10` round trips,
    `14` fills, and latest fill `2026-05-26T00:00:09.780106+00:00`.
- Git hygiene:
  - SHOWN: `git diff --check` passed with no output.
  - SHOWN: `git status --short --branch` listed only `.gitignore` and this
    work-log file as modified; `.cbp_state_challengers/` was no longer
    untracked after the ignore rule.

Remaining risk:
- HIGH: financial strategy experimentation and background-job operation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 before the isolated daily-loop challenger start.
- Remaining action: completed by the isolated daily-loop start entry below.

## 2026-06-05T19:55:45Z - EMA Cross Isolated Daily-Loop Start

Active role: `ENGINEER`

Objective: start the independently accepted `ema_cross_default` paper-only
daily-loop challenger campaign in isolated local state.

What was found:
- SHOWN: before start, canonical `es_daily_trend_v1` collector status was
  `idle`, `daily_loop=true`, `pid_alive=true`, and waiting for the next UTC
  day.
- SHOWN: before start, canonical promotion gates still reported `7/10` round
  trips, `14` fills, and latest fill `2026-05-26T00:00:09.780106+00:00`.
- SHOWN: before start, the dedicated challenger daily state
  `.cbp_state_challengers/ema_cross_default_daily` had no collector status and
  reported `status=not_started`.
- SHOWN: after start, challenger collector status reported `status=running`,
  `reason=collecting`, `pid_alive=true`, `strategies=["ema_cross"]`, and
  `session_strategy_id=ema_cross_default` via isolated evidence paths.
- SHOWN: runner status reported `bars=298`, populated `mid`, `strategy_id=ema_cross`,
  `strategy_preset=ema_cross_default`, `signal_source=public_ohlcv_5m`,
  `signal_action=hold`, and `signal_reason=no_cross`.
- SHOWN: after start, canonical promotion gates still reported `7/10` round
  trips and `14` fills.

What changed:
- Started the challenger command with:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/ema_cross_default_daily`.
- Used `--daily-loop`, `--strategies ema_cross`,
  `--session-strategy-id ema_cross_default`, `--symbol BTC/USDT`,
  `--venue coinbase`, `--signal-source public_ohlcv_5m`, `--runtime-sec 900`,
  `--strategy-drain-sec 2`, and `--poll-interval-sec 300`.
- No source code, strategy preset, gate threshold, or canonical `.cbp_state`
  artifact was edited.

Why this change:
- Stage 0 isolated proof was independently accepted, so the next scoped step
  was the isolated monitored daily-loop challenger.
- The dedicated `CBP_STATE_DIR` keeps challenger evidence separate from
  canonical `es_daily_trend_v1` promotion evidence.
- Daily-loop mode lets the system accumulate paper-only `ema_cross_default`
  observation without operator polling.

Expected outcome:
- The challenger runs one isolated public-OHLCV evidence window per UTC day.
- Fills, if any, accumulate only in
  `.cbp_state_challengers/ema_cross_default_daily`.
- The monitor emits watch reports for meaningful events such as campaign
  completion, fills, position close, or investigate conditions.

Verification:
- `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: canonical collector remained alive and idle for `es_daily_trend_v1`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: canonical gate remained `7/10` round trips and `14` fills before
    and after challenger start.
- `CBP_STATE_DIR=.../.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: challenger status was `running`, `reason=collecting`,
    `pid_alive=true`, and evidence directory was under
    `.cbp_state_challengers/ema_cross_default_daily`.
- `cat .cbp_state_challengers/ema_cross_default_daily/runtime/flags/strategy_runner.status.json`
  - SHOWN: runner had live public OHLCV state with `bars=298`,
    `signal_source=public_ohlcv_5m`, `signal_action=hold`, and
    `signal_reason=no_cross`.

Remaining risk:
- HIGH: financial strategy experimentation and background-job operation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 after the daily-loop start proof.
- Remaining action: monitor the isolated campaign until it records fills or
  reaches a no-trade investigation threshold.

## 2026-06-05T20:14:08Z - Paper Sim Monitor Daily-Loop Fill Visibility

Active role: `ENGINEER`

Objective: fix stale `paper_sim_monitor` summaries after a daily-loop
collector finishes a window and returns to idle.

What was found:
- SHOWN: the isolated `ema_cross_default` daily-loop challenger recorded one
  buy fill in JSONL evidence, `paper_trading.sqlite`, and
  `trade_journal.sqlite`.
- SHOWN: `paper_sim_monitor` watch output fired on the campaign transition but
  the summary still reported `fills=0` and `no fill yet`.
- SHOWN: daily-loop idle status stores the completed collection window under
  `last_result.results`, while `_latest_result()` only read top-level
  `results`.
- SHOWN: because no completed result was found, the monitor used the idle wait
  timestamp as the observation window and filtered out the real fill.

What changed:
- Updated `services/analytics/paper_sim_monitor.py` so `_latest_result()` falls
  back to `payload["last_result"]["results"]` when top-level `results` is
  absent.
- Added `test_collect_once_uses_daily_loop_last_result_when_idle` in
  `tests/test_paper_sim_monitor.py`.
- The regression test proves the monitor uses the completed daily-loop
  `started_ts` and `ended_ts` window, counts the fill, surfaces the latest
  journal fill, and includes `fills=1` plus the latest fill timestamp in the
  summary.

Why this change:
- The monitor is the operator-facing wakeup layer for paper campaigns; its
  summary must agree with canonical fill evidence after daily-loop state
  transitions.
- Reading `last_result.results` is the smallest compatible fix because it
  preserves existing top-level `results` behavior for active collection runs.

Expected outcome:
- When a daily-loop campaign is idle and waiting for the next UTC day, the
  monitor still summarizes the most recent completed evidence window.
- New fills and open positions from the completed window remain visible to the
  operator instead of disappearing until the next active run.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_run_paper_sim_monitor.py`
  - SHOWN: `18 passed in 0.25s`.
- `git diff --check`
  - SHOWN: clean.
- `CBP_STATE_DIR=.../.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python - <<'PY' ... svc.collect_once(...) ... PY`
  - SHOWN: isolated monitor output now reports `fills_observed=1`,
    `latest_journal_fill` populated, `paper_position.qty=0.001`, and summary
    text containing `fills=1` and the buy fill timestamp.
- `CBP_STATE_DIR=.../.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: challenger collector remains `idle`, `daily_loop=true`,
    `pid_alive=true`, and waiting for the next UTC day.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: canonical `es_daily_trend_v1` gate remains unchanged at `7/10`
    round trips and `14` fills.

Remaining risk:
- HIGH: operator monitoring for financial strategy experimentation and
  background jobs.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 after commit `ac46fb51c`.
- Remaining action: continue monitoring daily-loop paper campaigns for new
  fills, position closes, and investigate triggers.

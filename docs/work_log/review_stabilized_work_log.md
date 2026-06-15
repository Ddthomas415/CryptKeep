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

## 2026-06-05T20:15:50Z - ES Daily Trend Backtest Baseline Audit

Active role: `ENGINEER`

Objective: determine whether the paper gate's missing `win_rate`, `avg_win`,
and `avg_loss` backtest expectations can be safely populated from visible repo
artifacts.

What was found:
- SHOWN: `scripts/check_promotion_gates.py --json` still reports
  `manual_review_required=true`.
- SHOWN: the only outstanding manual item is
  `win_rate_avg_win_loss_vs_backtest`.
- SHOWN: observed paper-history metrics are `7` closed trades, `14` fills,
  `28.57%` win rate, `$37.33` average win, `-$0.26` average loss, `$35.75`
  net realized PnL, and `$5.11` expectancy per closed trade.
- SHOWN: `sample_data/ohlcv/BTC_USDT_1d.json` produced one buy and zero sells
  under the SMA-200 parity run, so it has no closed-trade baseline metrics.
- SHOWN: `.cbp_state/data/snapshots/ohlcv_coinbase_BTC_USDT_1d.json` produced
  zero trades and is local runtime state rather than a committed baseline
  artifact.
- SHOWN: `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json` produced one
  closed losing trade, but it is synthetic CI mechanics and should not be used
  as a profitability expectation source.

What changed:
- Added `docs/checkpoints/es_daily_trend_backtest_baseline_audit_2026_06_05.md`.
- Updated Priority 7 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to show that
  the strategy performance decision is blocked on an accepted historical
  closed-trade baseline.
- No strategy config, gate threshold, runtime behavior, or campaign state was
  changed.

Why this change:
- Filling `promotion.paper.backtest_expectations` from a synthetic fixture or
  non-closing sample would make the paper gate appear objective while using
  invalid baseline evidence.
- The safer outcome is to leave `manual_review_required=true` until an accepted
  reproducible closed-trade baseline exists.

Expected outcome:
- Future reviewers can see why the current config intentionally leaves
  `backtest_expectations` unset.
- The next correct action is to produce or acquire a reproducible historical
  OHLCV baseline that creates multiple natural `sma_200_trend` closed trades.

Verification:
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: canonical gate remains `7/10` round trips and
    `manual_review_required=true`.
- Parity read-only checks against the three candidate OHLCV sources:
  - SHOWN: committed daily sample: `buy_count=1`, `sell_count=0`,
    `closed_trades=0`.
  - SHOWN: local Coinbase snapshot: `buy_count=0`, `sell_count=0`,
    `closed_trades=0`.
  - SHOWN: synthetic SMA-200 fixture: `buy_count=1`, `sell_count=1`,
    `closed_trades=1`.

Remaining risk:
- LOW for this docs-only audit record.
- HIGH remains for the eventual strategy-performance decision and any future
  config baseline change.
- Acceptance state: `ACCEPTED`.

## 2026-06-05T20:24:00Z - ES Daily Trend Baseline Candidate Runner

Active role: `ENGINEER`

Objective: add a repeatable, non-mutating runner for producing an
`es_daily_trend_v1` SMA-200 backtest baseline candidate from historical OHLCV.

What was found:
- SHOWN: no existing script produced a dedicated ES daily trend paper-gate
  baseline report.
- SHOWN: `services/backtest/parity_engine.py` already provides the accepted
  strategy-registry parity path.
- SHOWN: `services/backtest/signal_replay.py` exposes public OHLCV fetching
  with `since_ms`, but no visible runner paginated enough history for an
  SMA-200 baseline.

What changed:
- Added `scripts/research/run_es_daily_trend_backtest_baseline.py`.
- The runner can read committed/local OHLCV JSON with `--input` or fetch public
  OHLCV with pagination using `--venue`, `--symbol`, `--timeframe`, `--since`,
  `--page-limit`, and `--max-pages`.
- Added `--data-symbol` so exchange OHLCV fetch symbols can differ from the
  strategy/report symbol without hiding the basis difference.
- The runner calls `run_parity_backtest()` with explicit SMA, ATR, warmup,
  fee, slippage, and minimum closed-trade assumptions.
- The runner writes a JSON report containing source metadata, counts,
  scorecard, `candidate_backtest_metrics`, config-ready
  `backtest_expectations`, `baseline_ready`, and `blocking_reasons`.
- When `baseline_ready=false`, `backtest_expectations` remains null-valued and
  the measured values stay under `candidate_backtest_metrics`.
- Added `tests/test_es_daily_trend_backtest_baseline_runner.py`.
- Updated the baseline audit checkpoint and next-actions document to point at
  the runner.
- Added
  `docs/checkpoints/es_daily_trend_backtest_baseline_candidate_2026_06_04.md`
  to record the network-produced candidate without mutating strategy config.
- No strategy config, gate threshold, runtime behavior, or campaign state was
  changed.

Why this change:
- The project needs a reproducible way to produce baseline numbers before
  filling `promotion.paper.backtest_expectations`.
- The runner makes the evidence boundary explicit: it can generate a candidate
  report, but it does not mutate governed promotion config.

Expected outcome:
- Operators can generate a candidate historical closed-trade baseline report
  without hand-written Python snippets.
- If the report lacks enough closed trades or exit signals, it explains why it
  is not baseline-ready.
- Any later config update can cite the exact runner command and output report.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_es_daily_trend.py tests/test_es_daily_trend_backtest_baseline_runner.py tests/test_backtest_parity_engine.py tests/test_check_promotion_gates.py`
  - SHOWN: `80 passed in 1.10s`.
- `git diff --check`
  - SHOWN: clean.
- `./.venv/bin/python scripts/research/run_es_daily_trend_backtest_baseline.py --input sample_data/ohlcv/BTC_USDT_1d.json --min-closed-trades 3 --source-label sample_data:BTC_USDT_1d.json`
  - SHOWN: `baseline_ready=false`.
  - SHOWN: `backtest_expectations` remained null-valued.
  - SHOWN: `candidate_backtest_metrics` preserved the measured non-ready
    values.
- `./.venv/bin/python scripts/research/run_es_daily_trend_backtest_baseline.py --venue coinbase --symbol BTC/USDT --data-symbol BTC/USD --timeframe 1d --since 2018-01-01 --until 2026-06-04 --page-limit 300 --max-pages 20 --min-closed-trades 3 --output /private/tmp/es_daily_trend_v1_baseline_candidate_20260604.json`
  - SHOWN: command exited `0`.
  - SHOWN: `baseline_ready=true`, `rows=3077`, `closed_trades=31`,
    `win_rate=0.22580645161290325`, `avg_win=1881.5222600358036`, and
    `avg_loss=-198.91552614027037`.

Remaining risk:
- HIGH: financial backtest baseline tooling can influence later gate decisions.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 after commit `23e2499a1`.
- Remaining action: do not copy raw dollar `avg_win` and `avg_loss` into the
  promotion config until their sizing basis is compatible with paper-history
  metrics.

## 2026-06-06T02:20:59Z - Normalize Paper Backtest Comparison Metrics

Active role: `ENGINEER`

Objective: make the paper promotion comparison sizing-independent by comparing
closed-trade return percentages rather than raw dollar average win/loss values.

What was found:
- SHOWN: `scripts/check_promotion_gates.py` compared raw paper-history
  `avg_win` and `avg_loss` dollars to raw backtest dollars.
- SHOWN: the accepted candidate used all-in compounding from `$1,000`, while
  paper history used small fixed quantities; those dollar values were not
  comparable.
- SHOWN: `journal_fills` contains entry price, quantity, and allocated fees, so
  net return percentage can be computed per closed trade.
- SHOWN: after fees, paper net win rate is `0.14285714285714285`, not the prior
  gross-PnL-derived `0.2857142857142857`.

What changed:
- Added `net_pnl` and `return_pct` to FIFO closed-trade analytics.
- Added `avg_win_return_pct`, `avg_loss_return_pct`, and
  `expectancy_return_pct` to paper strategy feedback.
- Updated paper gate history output to expose the normalized fields.
- Added explicit `metric_basis: net_return_pct` support to the backtest
  expectation comparison while retaining legacy raw-dollar behavior when no
  metric basis is configured.
- Updated `configs/strategies/es_daily_trend_v1.yaml` to declare the normalized
  metric contract while leaving all baseline values null.
- Updated the baseline runner to emit normalized config candidates.
- Added
  `docs/checkpoints/es_daily_trend_normalized_baseline_candidate_2026_06_04.md`.
- Updated strategy, decision-framework, baseline-audit, next-actions, and
  regression-test contracts.

Why this change:
- Win/loss dollars change with trade quantity and account size, so they cannot
  support a coherent paper-versus-backtest comparison across different sizing
  models.
- Net return divided by entry notional is independent of quantity and includes
  both entry and exit fees.
- Keeping config values null prevents this implementation from silently
  approving the normalized candidate.

Expected outcome:
- The gate compares like-for-like trade performance once a normalized baseline
  is independently accepted and populated.
- Until then, `manual_review_required=true` remains visible.
- Paper win rate is based on net closed-trade outcomes after fees.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_journal_analytics.py tests/test_strategy_feedback.py tests/test_es_daily_trend_backtest_baseline_runner.py tests/test_check_promotion_gates.py tests/test_es_daily_trend.py`
  - SHOWN: `80 passed in 1.05s`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: gate remains `7/10` round trips and
    `manual_review_required=true`.
  - SHOWN: missing baseline fields are `win_rate`,
    `avg_win_return_pct`, and `avg_loss_return_pct`.
  - SHOWN: observed paper metrics include net win rate
    `0.14285714285714285`, average win return `93.63856474626441%`,
    average loss return `-0.34741823139579114%`, and expectancy return
    `13.079150765412809%`.
- `./.venv/bin/python scripts/research/run_es_daily_trend_backtest_baseline.py --venue coinbase --symbol BTC/USDT --data-symbol BTC/USD --timeframe 1d --since 2018-01-01 --until 2026-06-04 --page-limit 300 --max-pages 20 --min-closed-trades 3 --output /private/tmp/es_daily_trend_v1_normalized_baseline_candidate_20260604.json`
  - SHOWN: `baseline_ready=true`, `rows=3077`, `closed_trades=31`,
    `win_rate=0.22580645161290325`,
    `avg_win_return_pct=78.71095396512578`, and
    `avg_loss_return_pct=-4.0629558060999225`.
- `./.venv/bin/python -m pytest -q tests/test_journal_analytics.py tests/test_strategy_feedback.py tests/test_es_daily_trend_backtest_baseline_runner.py tests/test_check_promotion_gates.py tests/test_es_daily_trend.py tests/test_backtest_evidence_cycle.py`
  - SHOWN: `94 passed in 1.11s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2107 passed, 33 skipped, 13 warnings in 377.72s`.
- `git diff --check`
  - SHOWN: clean.

Remaining risk:
- HIGH: this changes financial analytics and promotion-gate comparison
  semantics.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `0e81e0aad`.
- Accepted decisions: `net_return_pct` comparison basis, disclosed Coinbase
  `BTC/USD` historical source for the `BTC/USDT` strategy comparison, and
  unchanged `25%` relative tolerance.
- Remaining action: populate the accepted normalized baseline values and verify
  the resulting gate output.

## 2026-06-06T02:31:19Z - Populate Accepted Normalized Baseline

Active role: `ENGINEER`

Objective: copy the independently accepted normalized backtest expectations
into `es_daily_trend_v1` config and verify the resulting paper gate decision.

What was found:
- SHOWN: the normalized candidate was independently accepted with Coinbase
  `BTC/USD` as the disclosed historical data basis, `net_return_pct` as the
  comparison basis, and `25%` relative tolerance.
- SHOWN: before population, the gate could only report missing baseline values.
- SHOWN: after population, the gate can compare all three accepted metrics.

What changed:
- Populated `promotion.paper.backtest_expectations` in
  `configs/strategies/es_daily_trend_v1.yaml` with:
  - source
    `public_ohlcv:coinbase:BTC/USDT:data=BTC/USD:1d:2018-01-01:2026-06-04`
  - `win_rate=0.22580645161290325`
  - `avg_win_return_pct=78.71095396512578`
  - `avg_loss_return_pct=-4.0629558060999225`
- Updated the strategy config contract test to pin the accepted values.
- Updated the gate integration test to require a `machine_blocking` comparison
  rather than a missing-baseline manual-review result.
- Updated the normalized candidate and next-actions checkpoints with the
  resulting metric-by-metric gate outcome.
- No gate threshold, tolerance, campaign process, or paper-history artifact was
  changed.

Why this change:
- The baseline values had completed independent review and were ready to become
  the machine-readable comparison source.
- Populating them converts an unresolved manual review into an explicit
  reproducible performance decision.

Expected outcome:
- The gate reports exactly which paper metrics match or diverge from the
  accepted backtest.
- A favorable but materially different average-loss magnitude remains visible
  as exit-behavior drift rather than being silently treated as equivalent.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_es_daily_trend.py tests/test_check_promotion_gates.py tests/test_es_daily_trend_backtest_baseline_runner.py`
  - SHOWN: `75 passed in 0.86s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2107 passed, 33 skipped, 13 warnings in 369.07s`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: paper campaign remains `7/10` round trips.
  - SHOWN: comparison status is `machine_blocking`.
  - SHOWN: win rate fails: observed `0.14285714285714285`, accepted range
    `0.16935483870967744` to `0.28225806451612906`.
  - SHOWN: average win return passes: observed `93.63856474626441%`, accepted
    range `59.033215473844336%` to `98.38869245640723%`.
  - SHOWN: average loss return fails: observed `-0.34741823139579114%`,
    accepted range `-5.078694757624903%` to `-3.047216854574942%`.
- `git diff --check`
  - SHOWN: clean.

Remaining risk:
- HIGH: this populates financial promotion-gate policy values.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `4651680f5`.
- Remaining action: investigate whether the average-loss drift reflects genuine
  paper strategy behavior or mixed historical evidence attribution.

## 2026-06-06T02:49:14Z - Qualify Paper Promotion History by Fill Provenance

Active role: `ENGINEER`

Objective: prevent unstamped or incompatible legacy paper fills from advancing
the `es_daily_trend_v1` paper promotion gate.

What was found:
- SHOWN: the journal contained `14` `sma_200_trend` fills and `7` raw closed
  trades.
- SHOWN: six raw round trips closed within minutes despite the configured daily
  strategy holding horizon.
- SHOWN: only the 2026-05-26 exit fill carried explicit `public_ohlcv`, `1d`,
  Coinbase, `BTC/USDT`, non-sample provenance.
- SHOWN: no raw round trip had matching provenance on both entry and exit.
- SHOWN: latest-window provenance health previously allowed those older
  unstamped journal fills to supply the separate round-trip and expectancy
  thresholds.

What changed:
- Added `services/control/paper_evidence_qualification.py`.
- JSONL fill records now identify provenance-qualified order IDs; only complete
  entry-to-exit cycles are selected.
- The trade journal supplies immutable price, quantity, and fee data only for
  those selected order IDs.
- The machine gate and paper monitor progress use qualified counts and metrics.
- Raw journal totals remain visible as `paper_history.all_history`,
  `all_history_fills`, and `all_history_closed_trades`.
- Updated evidence-authority, operator, decision-framework, strategy, and
  checkpoint documentation.

Why this change:
- Current collector health cannot retroactively prove the source and timeframe
  of historical trades.
- Keeping raw history while excluding it from promotion is the smallest
  fail-closed correction; no evidence or database rows are deleted.
- A shared qualification service prevents the CLI gate and monitor summary from
  reporting different progress.

Expected outcome:
- The canonical campaign reports `0/10` qualified round trips and `7` raw
  all-history round trips.
- Future trades count only when both legs explicitly match the configured
  daily public-OHLCV contract.
- Performance comparison remains blocked until qualified closed trades exist.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py`
  - SHOWN: `38 passed in 0.64s`.
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py tests/test_paper_sim_monitor.py tests/test_strategy_feedback.py`
  - SHOWN: `55 passed in 0.84s`.
- `./.venv/bin/python -m py_compile services/control/paper_evidence_qualification.py scripts/check_promotion_gates.py services/control/paper_promotion_progress.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: final post-edge-case run completed with `2110 passed, 33 skipped,
    13 warnings in 369.22s`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: `0/10` qualified round trips, `10` remaining.
  - SHOWN: `14` raw all-history fills and `7` raw all-history round trips
    remain visible.
  - SHOWN: one provenance-qualified exit fill remains incomplete because its
    entry leg is unstamped.
- `git diff --check`
  - SHOWN: clean.
- `./.venv/bin/python tools/repo_doctor.py`
  - SHOWN: supported baseline complete, no non-canonical duplicate top-level
    directories, and no suspicious top-level files.

Remaining risk:
- HIGH: this changes financial promotion-gate eligibility and resets displayed
  qualified progress from `7/10` to `0/10`.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `7ab11da59`.
- Accepted decisions: require matching provenance on both trade legs, reset
  qualified progress to zero, and preserve the seven raw round trips as
  diagnostic all-history data.

## 2026-06-06T03:47:43Z - Refresh Collector and Correct Window PnL Attribution

Active role: `ENGINEER`

Objective: reload the accepted qualified-progress semantics in the managed
collector and prevent lifetime realized PnL from being labeled as current
campaign-window PnL.

What was found:
- SHOWN: the daily collector was healthy but had started before commit
  `7ab11da59`; its persisted monitor snapshot still displayed raw `7/10`
  promotion progress.
- SHOWN: the collector was idle after the completed 2026-06-06 UTC campaign.
- SHOWN: a read-only refreshed monitor snapshot correctly loaded qualified
  `0/10` progress but reported the lifetime position realized PnL of `$36.52`
  as `current_window_realized_pnl` despite `fills_observed=0`.
- SHOWN: `_result_realized_pnl()` fell back to lifetime position/equity totals
  when no campaign delta existed.

What changed:
- Requested a graceful managed stop and waited for PID `7178` to clear.
- Restarted the daily loop with the recorded parameters:
  `sma_200_trend`, `BTC/USDT`, Coinbase, `public_ohlcv_1d`, 20-second strategy
  runtime, and 300-second polling.
- Verified replacement PID `23879` is alive and idle without rerunning today's
  campaign.
- Changed current-window PnL reporting to use only
  `net_realized_pnl_delta`.
- When no explicit delta exists, the monitor now returns
  `current_window_realized_pnl=null`,
  `current_window_realized_pnl_known=false`, and source `unavailable`.
- Lifetime position and equity realized PnL remain separately visible.
- Updated the Golden Path and added an idle-monitor regression test.

Why this change:
- A long-running process must reload accepted code before operator output can
  reflect the new evidence policy.
- Lifetime totals are not valid substitutes for a campaign-window delta.
- Returning an explicit unknown is safer than displaying a precise but
  misattributed financial value.

Expected outcome:
- The next daily campaign and monitor process use qualified `0/10` promotion
  progress.
- Idle snapshots no longer imply that historical PnL was earned in the current
  window.
- Operators still retain lifetime PnL context in dedicated total fields.

Verification:
- `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: PID `23879`, `status=idle`, `pid_alive=true`,
    `signal_source=public_ohlcv_1d`, and no duplicate 2026-06-06 campaign.
- `./.venv/bin/python scripts/run_paper_sim_monitor.py --once --no-desktop-notify`
  - SHOWN before the reporting patch: qualified `0/10` progress loaded; stale
    lifetime PnL attribution reproduced.
- `./.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py tests/test_dashboard_home_digest.py tests/test_dashboard_page_runtime.py`
  - SHOWN: `51 passed in 1.81s`.
- `./.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py tests/test_dashboard_home_digest.py tests/test_dashboard_page_runtime.py tests/test_paper_strategy_evidence_service.py tests/test_run_paper_strategy_evidence_collector.py`
  - SHOWN: `82 passed in 2.03s`.
- `./.venv/bin/python -c "...collect_once..."`
  - SHOWN: idle `current_window_realized_pnl=null`,
    `current_window_realized_pnl_known=false`, source `unavailable`.
  - SHOWN: position lifetime total remains `$36.52320704250005`, equity
    lifetime total remains `-$1014.3944812741194`, and qualified promotion
    progress remains `0/10`.
- `git diff --check`
  - SHOWN: clean.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2111 passed, 33 skipped, 13 warnings in 375.81s`.
- `./.venv/bin/python scripts/run_paper_sim_monitor.py --once --no-desktop-notify`
  - SHOWN: persisted snapshot refreshed with idle window PnL
    `null/unavailable`, qualified `0/10` progress, and collector PID `23879`
    alive.

Remaining risk:
- HIGH: this changes financial operator-reporting semantics and restarts a
  managed background job.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `0003bd71c`.
- Accepted decision: use `null/unavailable` for current-window realized PnL
  when no explicit campaign delta exists while preserving lifetime totals.

## 2026-06-06T09:56:25Z - Unify Paper Evidence Collector Entrypoints

Active role: `ENGINEER`

Objective: ensure every supported operator entrypoint starts, stops, or
inspects the same managed paper evidence collector implementation.

What was found:
- SHOWN: the Makefile routed its three paper evidence targets through
  `scripts/data/run_paper_strategy_evidence_collector.py`.
- SHOWN: that nested script contained a separate one-shot collector CLI and
  did not expose the canonical daily-loop, polling, maximum-loop, or session
  strategy options.
- SHOWN: the root `scripts/run_paper_strategy_evidence_collector.py` is the
  entrypoint used by the dashboard, operator documentation, tests, and active
  daily collector.
- SHOWN: running the Makefile path could therefore start a campaign with
  behavior different from the documented and monitored campaign.

What changed:
- Replaced the nested collector implementation with a compatibility delegate
  to the root collector's `main()` function.
- Routed the Makefile collect, status, and stop targets directly through the
  root canonical collector.
- Documented the root collector as authoritative in `scripts/SCRIPTS.md`.
- Added regression tests that prevent a second parser from returning in the
  compatibility path, lock the Makefile to the canonical path, and verify the
  compatibility path exposes canonical daily-loop and session options.

Why this change:
- Keeping one collector implementation prevents background-job and evidence
  policy drift between operator entrypoints.
- A compatibility delegate preserves direct callers of the historical nested
  path without maintaining duplicate behavior.
- Routing Make directly to the canonical path makes the supported operator
  workflow explicit.

Expected outcome:
- Make, dashboard, documentation, direct root invocation, and the legacy
  nested path all execute the same collector behavior.
- Future collector options and evidence semantics have one implementation
  point.
- Existing callers of the nested path remain functional.

Verification:
- Initial targeted command included nonexistent
  `tests/test_validate_script_paths.py`.
  - SHOWN: pytest stopped before collection with `no tests ran`; this was a
    command-path mistake, not a code failure.
- `./.venv/bin/python -m pytest -q tests/test_bootstrap_helper_adoption.py tests/test_run_paper_strategy_evidence_collector.py tests/test_dashboard_operator_service.py`
  - SHOWN: `35 passed in 0.78s`.
- `./.venv/bin/python scripts/validate_script_paths.py`
  - SHOWN: `OK: script paths validated`.
- `make -n collect-paper-strategy-evidence status-paper-strategy-evidence stop-paper-strategy-evidence`
  - SHOWN: all three commands use
    `scripts/run_paper_strategy_evidence_collector.py`.
- `scripts/data/run_paper_strategy_evidence_collector.py --help`
  - SHOWN: exits successfully and includes `--daily-loop` and
    `--session-strategy-id`.
- `git diff --check`
  - SHOWN: clean before the work-log entry.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2113 passed, 33 skipped, 13 warnings in 387.96s`.

Remaining risk:
- HIGH: this changes supported entrypoints for a managed background financial
  evidence job.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `b9c126656`.
- Accepted decision: retain the nested script only as a compatibility delegate
  and route supported Makefile operations through the canonical root
  collector.

## 2026-06-06T10:14:57Z - Open Current Master Integration Review

Active role: `AUDITOR`

Objective: replace the stale conflict-heavy master integration plan with a
current, reviewable path from `review-stabilized` to `master`.

What was found:
- SHOWN: `origin/master...origin/review-stabilized` is `0 / 19`.
- SHOWN: `origin/master` is an ancestor of `origin/review-stabilized`.
- SHOWN: the 2026-05-25 plan describing 25 merge conflicts no longer applies
  to the current branch tips.
- SHOWN: no open pull request already targeted `review-stabilized` into
  `master`.
- SHOWN: the aggregate change contains 30 files, 2,770 insertions, and 176
  deletions across 19 accepted commits.

What changed:
- Opened draft PR #49 from `review-stabilized` to `master`.
- Updated `REMAINING_TASKS.md` and the next-actions checkpoint with the current
  ancestry, PR, and review requirements.
- Retired the stale 25-conflict instructions from the active task index.
- Kept the exact `0 / 19` divergence as timestamped audit evidence here while
  using non-self-staling ancestry language in active task documents.

Why this change:
- Master integration is the highest-leverage structural task because accepted
  work is not canonical until it reaches `master`.
- Direct ancestry means a new conflict-resolution branch would add risk and
  complexity without solving a current problem.
- A draft PR preserves required independent review for the aggregate
  financial and background-job changes.

Expected outcome:
- Reviewers evaluate one current, conflict-free integration diff.
- The canonical branch can advance without reviving obsolete integration
  branches or manual conflict resolutions.
- No merge occurs until PR checks and aggregate independent review pass.

Verification:
- `git rev-list --left-right --count origin/master...origin/review-stabilized`
  - SHOWN: `0 19`.
- `git merge-base --is-ancestor origin/master origin/review-stabilized`
  - SHOWN: exit `0`.
- `git diff --check origin/master..origin/review-stabilized`
  - SHOWN: clean.
- `gh pr list --state open --head review-stabilized --base master`
  - SHOWN: no existing PR before creation.
- GitHub connector PR creation
  - SHOWN: failed with `403 Resource not accessible by integration`; no PR was
    created by that attempt.
- `gh pr create --draft --base master --head review-stabilized ...`
  - SHOWN: created
    `https://github.com/Ddthomas415/CryptKeep/pull/49`.
- Latest implementation-head full suite:
  - SHOWN: `2113 passed, 33 skipped, 13 warnings in 387.96s`.

Remaining risk:
- HIGH: PR #49 aggregates financial promotion-gate behavior, strategy
  baselines, monitoring semantics, and managed collector entrypoints.
- SHOWN: all eight GitHub checks passed on reviewed head `7e9d9cf34`,
  including CI sanity, CI validate, macOS and Windows builds, governance
  smoke, script-path integrity, and GitGuardian.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 for PR #49 at head `7e9d9cf34`.
- Accepted decision: advance the conflict-free aggregate integration to
  `master` under the documented operator/admin merge policy.

## 2026-06-06T10:38:36Z - Complete Master Integration

Active role: `ENGINEER`

Objective: merge accepted PR #49 and leave `master` and `review-stabilized`
aligned.

What was found:
- SHOWN: PR #49 remained conflict-free and mergeable after the acceptance
  record commit.
- SHOWN: all eight GitHub checks passed again on head `b7130ab52`.
- SHOWN: GitHub reported the ready PR as blocked only by the solo-admin review
  requirement documented in `docs/GITHUB_BRANCH_PROTECTION.md`.

What changed:
- Marked PR #49 ready for review.
- Merged PR #49 through the documented operator/admin bypass path.
- Fast-forwarded `review-stabilized` to the resulting master merge commit.
- Updated the active backlog and checkpoint to mark master integration
  complete.

Why this change:
- The aggregate had explicit independent operator acceptance and complete CI
  proof.
- Keeping both remote branches on the same merge commit avoids immediately
  recreating the branch-divergence problem after integration.
- A follow-up documentation-only PR preserves branch protection while making
  the active task state accurate.

Expected outcome:
- Accepted paper evidence, baseline, monitoring, and collector work is
  canonical on `master`.
- `master` and `review-stabilized` start the next cycle from the same commit.
- The stale conflict-resolution plan no longer appears as pending work.

Verification:
- `gh pr checks 49 --watch`
  - SHOWN: all eight checks passed on head `b7130ab52`.
- `gh pr view 49`
  - SHOWN: state `MERGED`, merge commit `5ab9732a2`, merged at
    `2026-06-06T10:37:05Z`.
- `git fetch origin master review-stabilized`
  - SHOWN: `origin/master` advanced to `5ab9732a2`.
- `git merge --ff-only origin/master`
  - SHOWN: `review-stabilized` advanced from `b7130ab52` to `5ab9732a2`
    without conflicts.
- `git push origin review-stabilized`
  - SHOWN: remote integration branch advanced to `5ab9732a2`.
- `git rev-list --left-right --count origin/master...origin/review-stabilized`
  - SHOWN: `0 0`.
- Paper evidence collector status:
  - SHOWN: PID `23879` remains alive, idle, and waiting for the next UTC day.

Remaining risk:
- LOW: this closure update is documentation-only.
- Acceptance state: `ACCEPTED`.

## 2026-06-06T10:58:00Z - Scope Shadow Gates to Active Shadow Evidence

Active role: `ENGINEER`

Objective: prevent a shadow readiness query from treating historical paper
records as shadow-stage proof.

What was found:
- SHOWN: canonical 2026-06-06 signal records contain `spread_bps`, and session
  records contain `ops_checks_passed=true`.
- SHOWN: before this change, `check_promotion_gates.py --stage shadow --json`
  evaluated 33,318 historical signals and 336 sessions even though the
  persisted strategy stage was still `paper`.
- SHOWN: the override selected shadow gate logic but did not establish a
  shadow evidence window, so paper history could produce false failures and
  contradictory operator details.
- SHOWN: schema validation, provenance, slippage, and retirement checks also
  used all-time paper evidence outside the visible shadow gate list.

What changed:
- Added an active-stage evidence selector that requires both an explicit
  `_stage=shadow` stamp and a timestamp on or after the persisted shadow
  `since_ts`.
- Made shadow readiness report `not_started` with five unknown gates when the
  persisted `current_stage` is not `shadow`.
- Scoped shadow schema validation, provenance, slippage, and retirement checks
  to the same active shadow evidence window.
- Kept `provenance_all_time` as a diagnostic field without allowing it to
  influence shadow readiness.
- Added exact count details for shadow trading days, spread/depth coverage,
  ops checks, fill/slippage evidence, and recovery proof.
- Added regression tests for a paper-stage override and for mixed paper/shadow
  evidence after an actual stage promotion.
- Documented the `--stage shadow` query semantics in the golden path and
  strategy specification.

Why this change:
- A command-line report override must not silently reclassify evidence from a
  different deployment stage.
- Shadow promotion is a time-bounded experiment; using pre-promotion paper
  records makes its operational and market-quality gates untrustworthy.
- Applying one evidence scope to gates and their auxiliary checks avoids a
  report where the visible gates and top-level readiness decision use
  different data.

Expected outcome:
- Before shadow promotion, operators see an honest `UNKNOWN/not_started`
  result rather than paper-derived shadow failures.
- After promotion, only contemporaneous shadow records can advance or block
  the shadow checklist.
- The recovery gate cannot pass until a deliberate shadow-stage restart and
  state-validation drill is recorded.

Verification:
- Initial worktree-local command:
  `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py`
  - SHOWN: did not run because the isolated worktree has no `.venv`.
- Shared verified environment:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py`
  - SHOWN: `41 passed in 0.79s`.
- Related regression slice:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_deployment_stage.py tests/test_es_daily_trend.py tests/test_paper_promotion_progress.py`
  - SHOWN: `95 passed in 1.32s`.
- Full suite:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  - SHOWN: `2110 passed, 33 skipped, 13 warnings in 206.39s`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python tools/repo_doctor.py`
  - SHOWN: supported baseline present, no non-canonical duplicate trees, and
    no suspicious top-level files.
- Canonical-state readiness query through the isolated source:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/check_promotion_gates.py --stage shadow --json`
  - SHOWN: `current_stage=paper`,
    `evidence_scope.status=not_started`, all scoped counts zero, and
    `0 pass / 0 fail / 5 unknown`.
- Canonical paper regression query:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: paper logic still reads the existing all-paper evidence scope and
    remains not ready.
- `git diff --check`
  - SHOWN: clean before and after documentation updates.
- Main paper evidence collector status:
  `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: PID `23879` alive, status `idle`, reason
    `waiting_for_next_day`, with the 2026-06-06 evidence cycle complete.
- GitHub PR #51 checks on implementation commit `7a9c94e78`:
  - SHOWN: macOS build, Windows build, CI sanity, CI validate, governance
    smoke, script-path integrity, and GitGuardian passed.

Remaining risk:
- HIGH: this changes financial promotion-gate evidence selection and
  readiness reporting.
- UNVERIFIED: no real shadow campaign exists yet, so production evidence
  accumulation after an actual paper-to-shadow transition remains unproven.
- UNVERIFIED: the deliberate shadow restart/recovery drill has not been run.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-06 after implementation commit `7a9c94e78` and all PR
  #51 checks passed.

## 2026-06-07T23:09:31Z - Explain Excluded Paper Promotion History

Active role: `ENGINEER`

Objective: make the shared paper promotion progress output explain why the
existing all-history paper round trips are visible diagnostically but do not
advance the paper promotion threshold.

What was found:
- SHOWN: canonical promotion progress on `.cbp_state` reported 33/30 days and
  0/10 qualified round trips while all-history paper history still showed 7
  closed round trips.
- SHOWN: JSONL fill evidence contains 10 fill rows; 9 lack or mismatch the
  required market-data provenance fields, and 1 provenance-qualified fill is
  not part of a complete qualified entry/exit round trip.
- SHOWN: the evidence model explicitly says fresh latest-window provenance
  does not retroactively qualify older unstamped fills.
- SHOWN: current paper-engine tests already prove new order/fill records carry
  provenance forward, so future qualified round trips can count without
  backfilling legacy evidence.
- SHOWN: backfilling the legacy fills would infer unsupported facts and rewrite
  audit history.

What changed:
- Added a structured `qualification_explanation` object to
  `paper_promotion_progress`.
- Appended the qualification explanation to the operator-facing promotion
  summary when all-history round trips are excluded, evidence fills fail the
  provenance contract, qualified fills do not form a complete round trip, or
  qualified evidence order IDs are missing from the journal.
- Added regression coverage for both excluded all-history paper fills and a
  fully qualified paper round trip.
- Documented the reporting-only explanation in `docs/EVIDENCE_MODEL.md`.

Why this change:
- The qualification rule was correct, but the shared monitor/dashboard summary
  did not answer the operator's direct question: why visible historical trades
  were not moving the 10-round-trip gate.
- Reporting the exclusion reason is safer than retroactive qualification
  because it preserves the accepted provenance boundary while making the gate
  state understandable.
- Keeping this in shared progress output makes the monitor, dashboard, and any
  future operator surfaces consume the same explanation.

Expected outcome:
- Operators see the exact blocker without manually inspecting JSONL/journal
  internals.
- The promotion gate remains strict: the current canonical state still reports
  0/10 qualified round trips, not 7/10.
- Future provenance-complete entry/exit cycles will count normally and will not
  be mislabeled as diagnostic-only history.

Verification:
- Targeted regression slice:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_promotion_progress.py tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py`
  - SHOWN: `20 passed in 0.42s`.
- Canonical-state shared progress query through the isolated source:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -c 'import json; from services.control.paper_promotion_progress import load_paper_promotion_progress; p=load_paper_promotion_progress(); print(json.dumps({"days_recorded":p["days_recorded"],"round_trips_recorded":p["round_trips_recorded"],"all_history_round_trips":p["all_history_round_trips"],"qualification_explanation":p["qualification_explanation"],"summary_text":p["summary_text"]}, indent=2))'`
  - SHOWN: `days_recorded=33`, `round_trips_recorded=0`,
    `all_history_round_trips=7`, `evidence_fills=10`,
    `unqualified_evidence_fills=9`,
    `incomplete_qualified_evidence_fills=1`, and summary text explaining that
    7 all-history round trips are diagnostic only.
- Canonical paper gate regression:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: still `ready=false`, `machine_ready=false`, and the 10-round-trip
    gate reports `0/10, 10 remaining`.
- Full suite:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  - SHOWN: `2111 passed, 33 skipped, 13 warnings in 204.44s`.
- Repo doctor:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python tools/repo_doctor.py`
  - SHOWN: supported baseline present, no non-canonical duplicate trees, and
    no suspicious top-level files.
- Main paper evidence collector status:
  `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: PID `23879` alive, status `idle`, reason
    `waiting_for_next_day`, with the 2026-06-07 evidence cycle complete.
- `git diff --check`
  - SHOWN: clean before the work-log update.
- Main workspace branch check:
  - SHOWN: `/Users/baitus/Downloads/crypto-bot-pro` remains
    `review-stabilized...origin/review-stabilized` with `0 0` divergence from
    `origin/master`.

Remaining risk:
- HIGH: this changes financial promotion reporting consumed by operator
  monitor/dashboard surfaces.
- UNVERIFIED: dashboard rendering was not browser-checked in this branch.
- UNVERIFIED: no future complete qualified round trip has occurred yet in the
  live paper campaign.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-07 after implementation commit `99d3bb749`.

## 2026-06-07T23:47:55Z - Breakout Donchian Stage 0 Isolated Proof

Active role: `ENGINEER`

Objective: run a one-shot isolated wiring proof for the `breakout_donchian`
challenger without changing canonical `sma_200_trend` evidence or the active
isolated `ema_cross` campaign.

What was found:
- SHOWN: before the proof, canonical `sma_200_trend` remained at 14 fills, 7
  all-history closed trades, and latest fill
  `2026-05-26T00:00:09.780106+00:00`.
- SHOWN: the isolated `ema_cross_default` daily loop remained alive and idle
  with 2 fills, 1 closed trade, and +0.20272406454938546 net realized PnL.
- SHOWN: `breakout_donchian` maps to preset `breakout_default`.
- SHOWN: the runner received live Coinbase public OHLCV on the 5-minute
  timeframe, selected `breakout_donchian`, and reported a visible
  `hold/inside_channel` reason.
- SHOWN: the observed close remained below the prior Donchian upper boundary,
  and the volume ratio remained below the configured confirmation floor, so no
  order was expected.

What changed:
- Ran a one-shot campaign under the isolated state directory
  `.cbp_state_challengers/breakout_default_stage0_20260607T233204Z`.
- Used `--strategies breakout_donchian`,
  `--session-strategy-id breakout_default`, `--symbol BTC/USDT`,
  `--venue coinbase`, `--signal-source public_ohlcv_5m`,
  `--runtime-sec 900`, and `--strategy-drain-sec 2`.
- No strategy source, preset, threshold, canonical `.cbp_state` artifact, or
  `ema_cross` challenger artifact was modified.

Why this change:
- `breakout_donchian` is the strongest current synthetic leaderboard
  candidate but had no real paper runtime proof.
- A one-shot isolated proof is the smallest safe step before considering a
  persistent challenger daily loop.
- Separate state preserves strategy evidence ownership and prevents challenger
  results from advancing the `es_daily_trend_v1` promotion gate.

Expected outcome:
- The breakout challenger has verified startup, public-data acquisition,
  strategy selection, monitoring, isolated evidence routing, and clean
  shutdown behavior.
- A no-trade result remains valid Stage 0 evidence because the signal reason is
  visible and consistent with the strategy rules.
- Persistent daily-loop operation remains blocked pending independent review
  of this Stage 0 proof.

Verification:
- One-shot command:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_stage0_20260607T233204Z ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --strategies breakout_donchian --session-strategy-id breakout_default --symbol BTC/USDT --venue coinbase --signal-source public_ohlcv_5m --runtime-sec 900 --strategy-drain-sec 2 --no-desktop-notify`
  - SHOWN: completed normally after `903.963011264801s` with
    `stop_reason=runtime_elapsed`, `runner_status=stopped`,
    `signal_action=hold`, `enqueued_total=0`, `fills_total=0`, and
    `closed_trades_total=0`.
- Runner status during the proof:
  - SHOWN: 279-280 live bars, populated market price, strategy
    `breakout_donchian`, preset `breakout_default`,
    `signal_source=public_ohlcv_5m`, and `signal_reason=inside_channel`.
- Final isolated session evidence:
  - SHOWN: start and end records both carry
    `market_data_source=public_ohlcv`, `ohlcv_sample_mode=false`,
    `ohlcv_timeframe=5m`, `ohlcv_venue=coinbase`, and
    `ohlcv_symbol=BTC/USDT`.
  - SHOWN: end record reports `campaign_status=completed`,
    `reconciliation_result=pass`, `ops_checks_passed=true`,
    `critical_error=false`, and `kill_switch_tested=true`.
- Isolation checks:
  - SHOWN: canonical `sma_200_trend` remained at 14 fills, 7 closed trades,
    and +35.75316899496567 net realized PnL.
  - SHOWN: isolated `ema_cross` remained at 2 fills, 1 closed trade, and
    +0.20272406454938546 net realized PnL.
- Final collector status:
  - SHOWN: `status=completed`, `pid_alive=false`, and no PID file remains for
    the one-shot proof.
- Git status before this work-log update:
  - SHOWN: clean `review-stabilized...origin/review-stabilized`; isolated
    challenger artifacts remain ignored.

Remaining risk:
- HIGH: financial strategy experimentation and potential future background-job
  operation.
- UNVERIFIED: no actionable breakout signal, order, fill, or round trip
  occurred during Stage 0.
- UNVERIFIED: persistent daily-loop lifecycle for `breakout_donchian` has not
  been started or proven.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-07 after commit `5b4ee9b3c`.

## 2026-06-08T00:09:59Z - Breakout Donchian Isolated Daily-Loop Start

Active role: `ENGINEER`

Objective: start the independently accepted `breakout_donchian` challenger as
a separate paper-only daily-loop campaign in isolated local state.

What was found:
- SHOWN: the dedicated daily challenger state
  `.cbp_state_challengers/breakout_default_daily` had no prior collector status
  before start.
- SHOWN: canonical `sma_200_trend` remained alive, idle, and unchanged at 14
  fills and 7 all-history closed trades.
- SHOWN: isolated `ema_cross_default` had already entered its 2026-06-08
  collection window and remained in its own state directory.
- SHOWN: the first detached `nohup` launch exited before writing collector
  status and wrote no evidence records; it left only an empty app log under the
  isolated breakout state.

What changed:
- Started the breakout challenger daily loop with:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily`.
- Used `--daily-loop`, `--strategies breakout_donchian`,
  `--session-strategy-id breakout_default`, `--symbol BTC/USDT`,
  `--venue coinbase`, `--signal-source public_ohlcv_5m`,
  `--runtime-sec 900`, `--strategy-drain-sec 2`, and
  `--poll-interval-sec 300`.
- Launched the successful collector in a managed long-running process session
  after the detached `nohup` attempt failed to initialize.
- No source code, strategy preset, gate threshold, canonical `.cbp_state`
  artifact, or `ema_cross` challenger artifact was modified.

Why this change:
- Stage 0 proved breakout startup, public OHLCV routing, monitoring, isolated
  evidence routing, and clean shutdown.
- A separate daily loop lets the strongest synthetic leaderboard strategy
  accumulate real paper observations without polluting `es_daily_trend_v1`
  evidence or the existing `ema_cross_default` challenger.
- Keeping the state path separate makes later comparison possible without
  coupling promotion gates.

Expected outcome:
- The breakout challenger runs one isolated public-OHLCV evidence window per
  UTC day.
- Any breakout orders, fills, watch reports, and decision artifacts are written
  only under `.cbp_state_challengers/breakout_default_daily`.
- Canonical `sma_200_trend` and isolated `ema_cross_default` continue
  independently.

Verification:
- Successful breakout status:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: `status=running`, `reason=collecting`, `pid=47262`,
    `pid_alive=true`, `strategies=["breakout_donchian"]`, and evidence path
    under `.cbp_state_challengers/breakout_default_daily`.
- Breakout runner status:
  - SHOWN: live 5-minute public OHLCV, `strategy_id=breakout_donchian`,
    `strategy_preset=breakout_default`, `signal_action=hold`,
    `signal_reason=inside_channel`, `pos_qty=0.0`, and `enqueued_total=0`.
- Canonical isolation:
  - SHOWN: `sma_200_trend` collector remains alive and idle with 14 fills, 7
    all-history closed trades, and unchanged promotion-qualified count.
- EMA challenger isolation:
  - SHOWN: `ema_cross_default` collector remains alive and running in its own
    2026-06-08 collection window.
- Git status before this work-log update:
  - SHOWN: clean `review-stabilized...origin/review-stabilized`; isolated
    challenger artifacts remain ignored.

Remaining risk:
- HIGH: financial strategy experimentation and background-job operation.
- RESOLVED: the first persistent breakout daily-loop window completed; see the
  2026-06-08T04:02:48Z entry below.
- UNVERIFIED: no actionable breakout signal, order, fill, or round trip has
  occurred in the daily loop yet.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-08 after commit `bcba08a6b`.

## 2026-06-08T04:02:48Z - Breakout Donchian First Daily-Loop Window Completion

Active role: `AUDITOR`

Objective: verify the first persistent `breakout_donchian` daily-loop window
completed cleanly after the accepted start.

What was found:
- SHOWN: `breakout_default` daily loop completed its 2026-06-08 window and
  returned to idle while keeping PID `47262` alive for the next UTC day.
- SHOWN: the completed result reported `runtime_sec=904.6953809261322`,
  `stop_reason=runtime_elapsed`, `runner_status=stopped`,
  `signal_action=hold`, `fills_total=0`, `closed_trades_total=0`, and
  `net_realized_pnl_total=0.0`.
- SHOWN: the session evidence contains start and end records with
  `market_data_source=public_ohlcv`, `ohlcv_sample_mode=false`,
  `ohlcv_timeframe=5m`, `ohlcv_venue=coinbase`, and
  `ohlcv_symbol=BTC/USDT`.
- SHOWN: the end record reports `campaign_status=completed`,
  `reconciliation_result=pass`, `ops_checks_passed=true`,
  `critical_error=false`, and `kill_switch_tested=true`.
- SHOWN: `paper_sim_monitor` sees `breakout_default` idle, flat, `fills=0`,
  `round_trips=0`, and `recommendation=continue`.
- SHOWN: canonical `sma_200_trend` completed its 2026-06-08 window with no new
  fills and remains not ready at `0/10` qualified round trips.
- SHOWN: isolated `ema_cross_default` completed its 2026-06-08 window with no
  new fills and remains at 2 fills, 1 closed trade, and +0.20272406454938546
  net realized PnL.

What changed:
- No source code, config, strategy preset, gate threshold, or canonical
  evidence was changed.
- This entry records the first-window completion proof for the accepted
  persistent breakout challenger.

Why this change:
- The accepted daily-loop start still had one open lifecycle risk: whether the
  first persistent window would complete and return to idle cleanly.
- Recording the completion proof keeps the governed work log aligned with the
  actual background-job state.

Expected outcome:
- `breakout_default`, `ema_cross_default`, and canonical `sma_200_trend` now
  continue as three isolated daily observation loops.
- Breakout evidence remains paper-only and isolated under
  `.cbp_state_challengers/breakout_default_daily`.
- Future actionable breakout signals, orders, fills, or position closes should
  be reviewed as challenger evidence only, not as `es_daily_trend_v1`
  promotion evidence.

Verification:
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: `status=idle`, `reason=waiting_for_next_day`, `last_completed_day=2026-06-08`, and `pid_alive=true`.
- `cat .cbp_state_challengers/breakout_default_daily/data/evidence/breakout_default/session_2026-06-08.jsonl`
  - SHOWN: public non-sample 5-minute Coinbase provenance on start/end session
    records and clean completed end state.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_sim_monitor.py --status`
  - SHOWN: idle, flat, `fills_observed=0`, `round_trips_observed=0`, and
    `recommendation=continue`.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state ./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: canonical paper gate remains not ready at `0/10` qualified round
    trips and 34/30 days recorded.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: `ema_cross_default` is idle, alive, and waiting for the next UTC
    day after a no-new-fill 2026-06-08 window.

Remaining risk:
- HIGH: ongoing financial strategy experimentation and background-job
  operation.
- UNVERIFIED: no actionable breakout order/fill/round trip has occurred yet.
- UNVERIFIED: no multi-day persistence proof exists yet beyond the first
  completed daily loop window.
- Acceptance state: `ACCEPTED`.

## 2026-06-08T15:12:00Z - Detached Paper Evidence Daily-Loop Launcher

Active role: `ENGINEER`

Objective: fix the operator workflow gap where a paper evidence daily loop
started from a Codex managed process session could die after the session ended.

What was found:
- SHOWN: the previously accepted `breakout_donchian` daily-loop collector PID
  `47262` was no longer alive even though its status file still reported
  `last_completed_day=2026-06-08`.
- SHOWN: canonical `sma_200_trend` PID `23879` and isolated
  `ema_cross_default` PID `8480` remained alive and parented to PID `1`.
- SHOWN: `scripts/run_paper_strategy_evidence_collector.py` exposed
  `--daily-loop`, `--status`, and `--stop`, but no authoritative detached
  top-level launch mode.
- SHOWN: existing service helpers use `start_new_session=True` for durable
  managed child processes, but the collector itself had no equivalent
  operator-facing launch path.

What changed:
- Added `--detach` to the authoritative
  `scripts/run_paper_strategy_evidence_collector.py` CLI.
- Scoped `--detach` to `--daily-loop` only; it cannot be combined with
  `--status` or `--stop`.
- The detached launcher:
  - refuses to start a duplicate collector when the selected `CBP_STATE_DIR`
    already has a live PID;
  - starts the same script without `--detach`;
  - inherits the selected environment, including `CBP_STATE_DIR`;
  - uses `start_new_session=True` on POSIX and detached process flags on
    Windows;
  - redirects child output to
    `<CBP_STATE_DIR>/runtime/logs/paper_strategy_evidence.log`;
  - waits briefly for the child to publish a matching live PID before reporting
    `detached_started`.
- Updated `docs/GOLDEN_PATH.md` and `scripts/SCRIPTS.md` to document
  `--daily-loop --detach` as the persistent operator path.
- Restarted only the isolated `breakout_donchian` challenger using the new
  detached path under
  `.cbp_state_challengers/breakout_default_daily`.

Why this change:
- The previous `nohup` attempt failed to initialize, and the successful
  managed-session launch did not survive as a durable background process.
- Adding the detached mode at the authoritative collector CLI keeps the
  operator workflow on one source of truth instead of adding another wrapper or
  service-manager fork.
- Duplicate-process protection and state-local logging make the launch auditable
  and safe for isolated challenger state directories.

Expected outcome:
- Future paper evidence daily loops can be started with
  `--daily-loop --detach` and survive the Codex session that started them.
- `breakout_donchian` continues as an isolated paper-only challenger and should
  wake on the next UTC day without manual polling.
- Canonical `sma_200_trend` and isolated `ema_cross_default` continue
  independently.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_run_paper_strategy_evidence_collector.py`
  - SHOWN: `10 passed in 0.25s`.
- `./.venv/bin/python -m pytest -q tests/test_run_paper_strategy_evidence_collector.py tests/test_dashboard_operator_service.py tests/test_bootstrap_helper_adoption.py`
  - SHOWN: `37 passed in 0.85s`.
- `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --help`
  - SHOWN: help exposes `--detach` and describes detached daily-loop startup.
- `git diff --check`
  - SHOWN: clean.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py ... --daily-loop --detach`
  - SHOWN: returned `ok=true`, `reason=detached_started`, `pid=10310`, and
    log file under the isolated breakout state directory.
- `ps -o pid=,ppid=,stat=,etime=,command= -p 10310,23879,8480`
  - SHOWN: breakout PID `10310`, EMA PID `8480`, and canonical PID `23879` are
    all alive with `PPID=1`.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: breakout status is `idle`, `reason=waiting_for_next_day`,
    `pid=10310`, `pid_alive=true`, `strategies=["breakout_donchian"]`, and
    evidence path remains under `.cbp_state_challengers/breakout_default_daily`.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: EMA remains idle/alive at PID `8480`.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: canonical `sma_200_trend` remains idle/alive at PID `23879`.

Remaining risk:
- HIGH: background-job operator workflow and financial strategy evidence
  collection.
- UNVERIFIED: no multi-day detached persistence proof exists yet; next proof is
  whether PID `10310` wakes and completes the next UTC daily window.
- UNVERIFIED: no actionable `breakout_donchian` order, fill, or round trip has
  occurred yet.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-08 after commit `c9e79eacd`.

## 2026-06-10 - Master Integration Handoff For Accepted Campaign Fixes

Active role: `GATE`

Objective: publish the accepted promotion-provenance visibility and detached
paper-loop changes for integration from `review-stabilized` into `master`.

What was found:
- SHOWN: the initial local comparison reported `review-stabilized` seven
  commits ahead of the stale local `master`.
- SHOWN: after fetching remote truth, `origin/master` already contained the
  five commits merged by PR `#52`; `review-stabilized` was three commits ahead
  and one merge commit behind.
- SHOWN: the branch diff is limited to promotion-progress explanation,
  detached collector startup, tests, operator documentation, and governed work
  records.
- SHOWN: no open `review-stabilized` to `master` pull request existed.
- SHOWN: canonical `sma_200_trend`, isolated `ema_cross_default`, and isolated
  `breakout_default` all completed the 2026-06-10 daily window and remained
  idle with live collector PIDs.
- SHOWN: the detached breakout collector completed daily windows on
  2026-06-08, 2026-06-09, and 2026-06-10.

What changed:
- Ran the full repository test suite to completion.
- Opened GitHub PR `#53`, `review-stabilized` to `master`:
  `https://github.com/Ddthomas415/CryptKeep/pull/53`.
- Merged current `origin/master` into `review-stabilized` with the `ort`
  strategy and no content conflicts or history rewrite.
- No campaign process, strategy configuration, gate threshold, order-routing
  behavior, or runtime evidence artifact was changed.

Why this change:
- The accepted fixes should not remain only on the review branch.
- A pull request preserves CI evidence and an explicit integration boundary
  before the canonical branch changes.
- Verifying campaign health before and after the suite ensures the integration
  proof did not interrupt active paper observation.

Expected outcome:
- GitHub CI evaluates the exact accepted branch tip.
- After required checks pass, PR `#53` can be merged into `master`.
- The three paper collectors continue independently while integration proceeds.

Verification:
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2118 passed, 33 skipped, 13 warnings in 393.84s`.
- `git diff --check`
  - SHOWN: clean.
- `git fetch origin master review-stabilized` followed by
  `git rev-list --left-right --count origin/master...review-stabilized`
  - SHOWN before synchronization: `1 3`.
- `git merge --no-edit origin/master`
  - SHOWN: clean `ort` merge with no content conflicts.
- GitHub PR `#53` checks on synchronized commit `f99ea206a`:
  - SHOWN: `CI validate`, `CI sanity`, macOS build, Windows build, both
    governance smoke checks, script-path integrity, and GitGuardian all passed.
- Collector status checks:
  - SHOWN: `sma_200_trend` PID `23879`, idle/alive, last completed
    `2026-06-10`.
  - SHOWN: `ema_cross_default` PID `8480`, idle/alive, last completed
    `2026-06-10`.
  - SHOWN: `breakout_default` PID `10310`, idle/alive, last completed
    `2026-06-10`.

Remaining risk:
- MEDIUM: administrative merge of PR `#53` into `master` remains pending.
- HIGH-risk implementation content in this PR was independently reviewed and
  accepted by the human operator before the integration handoff.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted implementation,
  clean local full suite, clean branch synchronization, and all GitHub PR
  checks passing on 2026-06-10.

## 2026-06-11T09:59:36Z - Count Held Bars By Market Timestamp

Active role: `ENGINEER`

Objective: stop the `breakout_donchian` and `ema_cross` paper runners from
consuming a bar-based time stop on repeated polling of the same market bar.

What was found:
- SHOWN: the isolated `breakout_donchian` campaign produced three round trips
  between `2026-06-11T00:03:20Z` and `2026-06-11T00:16:01Z` while consuming
  public Coinbase `5m` OHLCV.
- SHOWN: the first position-close monitor artifact reports
  `bars_held=60`, `exit_reason=strategy_exit:breakout_donchian:time_stop`, and
  `exit_stack_rule=time_stop` only about 162 seconds after entry.
- SHOWN: the isolated `ema_cross` position-close artifact also reports
  `strategy_exit:ema_cross:time_stop` after about 154 seconds.
- SHOWN: `ema_crossover_runner.py` incremented `bars_held` once per polling
  loop whenever a position was open, regardless of whether the latest OHLCV
  timestamp changed.
- SHOWN: the default `max_bars_hold` is `60`; therefore repeated polls of one
  five-minute candle could exhaust the configured limit in roughly 60 loops.
- SHOWN: the runner called `StrategyStateSQLite.delete(...)` during exit-state
  cleanup, but `storage/strategy_state_sqlite.py` did not implement `delete`;
  the resulting exceptions were swallowed.
- UNVERIFIED: the second and third breakout exits did not retain an exit reason
  in their captured monitor snapshots. Their timing is consistent with the
  same defect, but the exact cause of those two exits is not proven.

What changed:
- Added `_advance_held_bar_counter(...)` and a persisted
  `last_held_bar_ts:<venue>:<symbol>:<strategy>` state key.
- The runner now seeds the timestamp without incrementing, ignores repeated or
  older timestamps, and increments `bars_held` only when the market-data
  timestamp advances.
- Entry, flat-position, and sell cleanup now initialize or clear the timestamp
  key together with the existing entry, trailing-peak, and held-bar state.
- Added the missing `StrategyStateSQLite.delete(...)` operation so runner
  cleanup no longer silently fails.
- Added unit and runner-level regression tests proving repeated timestamps do
  not consume the time stop and genuinely newer timestamps still produce
  exactly one configured time-stop sell.

Why this change:
- `max_bars_hold` is a market-observation control, not a CPU-loop control.
  Counting poll iterations made exit timing depend on runner cadence and
  caused minute-scale churn on a five-minute strategy.
- Persisting the last counted timestamp preserves correct behavior across
  loops and process restarts without changing stop-loss, take-profit,
  trailing-stop, signal, order-routing, or gate thresholds.
- Implementing the store method used by the existing cleanup path is smaller
  and safer than continuing to suppress a broken interface contract.

Expected outcome:
- Public OHLCV campaigns count each candle timestamp once, so a 60-bar hold
  limit can no longer fire after 60 repeated polls of the same candle.
- Tick-derived sources count unique observation timestamps rather than raw
  loop iterations.
- Existing time stops still fire when the configured number of genuinely new
  market timestamps has elapsed.
- Stale runner exit state can be deleted when positions close or are flat.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_breakout_runner_exit_stack.py tests/test_exit_control_stack.py`
  - SHOWN: `31 passed in 0.76s`.
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_breakout_runner_exit_stack.py tests/test_exit_control_stack.py tests/test_ema_runner_risk_defaults.py tests/test_run_paper_strategy_evidence_collector.py tests/test_paper_strategy_evidence_service.py`
  - SHOWN: `65 passed in 1.11s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2117 passed, 33 skipped, 13 warnings in 214.60s`.
- `git diff --check`
  - SHOWN: clean.
- `ruff check` on the changed files
  - SHOWN: reports two pre-existing duplicate `sma_200_trend` dictionary keys
    at runner lines 64 and 75; neither finding is introduced or modified by
    this change.
- VERIFIED_ENV: all verification ran in the repository virtual environment
  from isolated worktree `/private/tmp/crypto-bot-pro-bar-hold-fix`.
- Collector status checks from the unchanged main workspace:
  - SHOWN: canonical `sma_200_trend` PID `23879` is idle/alive after completing
    the 2026-06-11 window.
  - SHOWN: isolated `ema_cross` PID `8480` is idle/alive after completing the
    2026-06-11 window.
  - SHOWN: isolated `breakout_donchian` PID `10310` is idle/alive after
    completing the 2026-06-11 window.

Remaining risk:
- HIGH: this changes financial strategy exit timing and background-runner
  state semantics.
- UNVERIFIED: no live paper campaign has run on this branch; active collectors
  remain on accepted commit `13cba446b` and were not restarted or modified.
- UNVERIFIED: sell intent metadata does not directly persist `exit_reason`, so
  later evidence may still require monitor snapshots to attribute an exit.
- SHOWN: the daily-loop collector launches `scripts/run_strategy_runner.py` as
  a fresh subprocess for each strategy window, so integration before the next
  UTC window applies the fix without restarting the collector parents.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-11 after commit `a0a1403de`.

## 2026-06-11T10:11:31Z - Integrate Accepted Market-Bar Time-Stop Fix

Active role: `GATE`

Objective: integrate the independently accepted strategy-runner correction
into `review-stabilized` without interrupting active paper campaigns.

What was found:
- SHOWN: `codex/fix-bar-hold-clock` was a clean two-commit descendant of
  `review-stabilized`; no conflict resolution or history rewrite was needed.
- SHOWN: the daily-loop collector launches a fresh strategy-runner subprocess
  for each UTC evidence window.
- SHOWN: canonical, EMA, and breakout collector parents had already completed
  the 2026-06-11 window and remained idle with live PIDs.

What changed:
- Merged accepted commits `a0a1403de` and `91fd74b50` into
  `review-stabilized` as merge commit `0efcd55c3`.
- After verifying the feature tip was an ancestor of `review-stabilized`,
  removed the temporary worktree and deleted the merged local and remote
  `codex/fix-bar-hold-clock` branches.
- No collector process, evidence artifact, strategy configuration, gate
  threshold, or current position was changed.

Why this change:
- The correction must be on the branch used by the next freshly launched
  strategy runner.
- Preserving the collector parents avoids an unnecessary campaign restart
  while still applying the accepted code on the next UTC window.

Expected outcome:
- The June 12 EMA and breakout strategy windows load the market-timestamp bar
  counter automatically.
- Repeated polling of one five-minute candle no longer consumes the 60-bar
  time stop.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_breakout_runner_exit_stack.py tests/test_exit_control_stack.py tests/test_ema_runner_risk_defaults.py tests/test_run_paper_strategy_evidence_collector.py tests/test_paper_strategy_evidence_service.py`
  - SHOWN: `65 passed in 1.14s`.
- `git diff --check origin/review-stabilized...HEAD`
  - SHOWN: clean.
- `git merge-base --is-ancestor codex/fix-bar-hold-clock review-stabilized`
  - SHOWN: returned success before branch cleanup.
- Collector status checks:
  - SHOWN: `sma_200_trend` PID `23879`, idle/alive.
  - SHOWN: `ema_cross` PID `8480`, idle/alive.
  - SHOWN: `breakout_donchian` PID `10310`, idle/alive.

Remaining risk:
- HIGH implementation risk was independently accepted before integration.
- UNVERIFIED: the corrected behavior has not yet completed a real paper
  window; the next proof point is the June 12 challenger evidence.
- Acceptance state: `ACCEPTED`.

## 2026-06-11T10:18:03Z - Re-enable Breakout Desktop Notifications

Active role: `ENGINEER`

Objective: restore desktop delivery for the existing breakout monitor watches
without changing campaign evidence, strategy settings, or other collectors.

What was found:
- SHOWN: canonical PID `23879` and EMA PID `8480` were launched with the
  default notification-enabled mode.
- SHOWN: breakout PID `10310` was explicitly launched with
  `--no-desktop-notify`.
- SHOWN: the June 11 canonical and EMA watch reports recorded
  `desktop_notification.sent=true`.
- SHOWN: the June 11 breakout investigate report recorded
  `attempted=false`, `sent=false`, and `reason=disabled`.
- SHOWN: all four breakout watches were active and writing report artifacts;
  only desktop delivery was disabled.

What changed:
- Requested a supported stop for idle breakout collector PID `10310`.
- Waited for the 300-second daily-loop poll boundary until status showed
  `stop_requested`, `pid_alive=false`, and no PID file.
- Started the same detached breakout daily-loop command in the same isolated
  state directory without `--no-desktop-notify`.
- The replacement collector is PID `32873`, idle and waiting for the next UTC
  day.

Why this change:
- The monitor and trigger layer already worked; replacing the parent launch
  flag is the smallest correction that restores user-visible notifications.
- The June 11 session was complete, so the supported stop/detach sequence
  avoided interrupting an active runner or duplicating the daily campaign.

Expected outcome:
- The next breakout fill, position close, investigate recommendation, or
  campaign-completed event writes its normal report and attempts local desktop
  delivery.
- The June 12 breakout strategy window also loads the accepted market-bar
  time-stop implementation from `review-stabilized`.

Verification:
- Old collector status:
  - SHOWN: PID `10310` stopped with `reason=stop_requested`,
    `pid_alive=false`, and `has_pid_file=false`.
- Replacement start:
  - SHOWN: detach returned `reason=detached_started`, PID `32873`.
  - SHOWN: status reports `idle`, `waiting_for_next_day`, `pid_alive=true`,
    and `last_completed_day=2026-06-11`.
- Process command inspection:
  - SHOWN: PID `32873` retains the breakout strategy, session ID, BTC/USDT,
    Coinbase, public 5-minute OHLCV, 900-second runtime, and 300-second daily
    poll settings.
  - SHOWN: PID `32873` does not contain `--no-desktop-notify`.
- Evidence integrity:
  - SHOWN: persisted paper history remains six fills, three closed trades, and
    `-0.38540687113248273` net realized PnL.
  - SHOWN: evidence inventory remains one fill file, one order file, four
    session files, and 20 total records.
- Isolation:
  - SHOWN: canonical PID `23879` and EMA PID `8480` remained alive with their
    original command lines.
- VERIFIED_ENV: commands ran from the synchronized `review-stabilized`
  workspace at `bf2aae822`.

Remaining risk:
- HIGH: this changed a persistent background monitoring job.
- UNVERIFIED: no new breakout watch event has fired after PID `32873` started,
  so actual desktop delivery from the replacement process is not yet shown.
- UNVERIFIED: the June 12 paper window has not yet exercised the accepted
  market-bar time-stop correction.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-11 after commit `7f3084f65`.

## 2026-06-11T12:53:51Z - Remove Stale Promotion Worktree Registration

Active role: `ENGINEER`

Objective: remove a dead worktree registration and its fully merged feature
branch so Git no longer advertises a nonexistent checkout.

What was found:
- SHOWN: `/private/tmp/cryptkeep-shadow-gate-evidence-scope` did not exist.
- SHOWN: `git worktree prune --dry-run --verbose` identified its registration
  as prunable because the gitdir target was missing.
- SHOWN: local and remote `codex/promotion-provenance-visibility` were each
  fully contained in `review-stabilized`; the comparison was 18 commits on
  `review-stabilized` and zero unique feature commits.

What changed:
- Pruned the stale worktree registration.
- Deleted the fully merged local
  `codex/promotion-provenance-visibility` branch.
- Deleted the corresponding fully merged remote branch.

Why this change:
- A dead worktree registration can block branch cleanup and create false
  branch-conflict signals.
- Ancestry was proven before deletion, so no unique commit was discarded.

Expected outcome:
- `git worktree list` reports only the active repository checkout.
- Future branch and worktree operations no longer encounter the stale
  promotion-provenance registration.

Verification:
- `git worktree list --porcelain`
  - SHOWN: only `/Users/baitus/Downloads/crypto-bot-pro` remains.
- `git branch -vv | rg 'promotion-provenance-visibility'`
  - SHOWN: no local branch remains.
- `git status -sb`
  - SHOWN: `review-stabilized` is clean and synchronized before this log
    entry.
- VERIFIED_ENV: Git cleanup ran in the canonical repository checkout.

Remaining risk:
- LOW: metadata and fully merged branch cleanup only.
- No runtime process, evidence artifact, source file, or strategy behavior was
  changed.
- Acceptance state: `ACCEPTED`.

## 2026-06-11T13:19:53Z - Persist Strategy Exit Attribution

Active role: `ENGINEER`

Objective: make strategy-driven sell reasons durable across paper intent,
order/fill evidence, reconciliation outcomes, and closed-trade summaries.

What was found:
- SHOWN: the June 11 breakout paper database contains three sell orders whose
  metadata has `exit_reason=None` and `exit_stack_rule=None`.
- SHOWN: the June 11 EMA paper database contains one sell order with the same
  missing attribution.
- SHOWN: the first breakout position-close monitor artifact temporarily
  reported `strategy_exit:breakout_donchian:time_stop`, but that reason was not
  copied into the queued intent or durable paper order.
- SHOWN: `paper_engine.py` copied only market-data provenance fields into order
  and fill JSONL evidence.
- SHOWN: both strategy outcome producers copied `signal_reason` but omitted
  `exit_reason` and `exit_stack_rule`.

What changed:
- Exit-stack and EMA-invalidation sells now add `exit_reason` to intent
  metadata; stack exits also add `exit_stack_rule`.
- Ordinary buy and signal-change intents remain unchanged and do not receive
  exit attribution fields.
- Paper order and fill JSONL evidence now preserves the two exit-attribution
  fields alongside existing market-data provenance.
- Paper intent reconciliation and execution-plan reconciliation now copy the
  fields into strategy outcome rows.
- Closed-trade summaries now expose both fields.
- Added unit and SQLite-backed integration coverage from queued sell intent
  through paper order, fill JSONL, reconciliation, and summary output.

Why this change:
- Exit attribution must survive beyond transient runner status to support
  strategy review, churn diagnosis, and performance analysis by exit type.
- Copying existing metadata is the smallest coherent fix; no order decision,
  side, quantity, venue, risk threshold, or execution route changes.

Expected outcome:
- Future strategy-driven paper exits can be classified as time stop, stop
  loss, take profit, trailing stop, or EMA invalidation from durable evidence.
- Operators no longer need a precisely timed monitor snapshot to determine why
  a position closed.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_paper_engine_integration.py tests/test_intent_reconciler.py tests/test_paper_strategy_journal_flow.py tests/test_outcome_summary.py`
  - SHOWN: `40 passed in 1.30s`.
- Broader paper execution and evidence regression slice:
  - SHOWN: `78 passed in 2.54s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2119 passed, 33 skipped, 13 warnings in 208.72s`.
- `git diff --check`
  - SHOWN: clean.
- `ruff check` on the non-runner changed files
  - SHOWN: reported only pre-existing import-order and unused-import findings
    at the top of `paper_engine.py`; no changed block introduced a lint
    finding.
- VERIFIED_ENV: all tests ran in repository virtual environment from isolated
  worktree `/private/tmp/crypto-bot-pro-exit-attribution`.
- Isolation:
  - SHOWN: canonical workspace remained clean on `review-stabilized`.
  - SHOWN: breakout collector PID `32873` remained idle/alive.

Remaining risk:
- HIGH: this changes financial evidence and execution-observability surfaces.
- UNVERIFIED: no real paper exit has yet written the new fields.
- Historical June 11 evidence is not backfilled; the change applies to future
  orders and fills only.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-11 after commit `493d9d76c`.

## 2026-06-11T13:36:56Z - Integrate Accepted Exit Attribution

Active role: `GATE`

Objective: integrate the independently accepted exit-attribution evidence
change without interrupting active paper collectors.

What was found:
- SHOWN: `codex/persist-exit-attribution` was a clean two-commit descendant of
  `review-stabilized`.
- SHOWN: the feature commit had full-suite proof of `2119 passed, 33 skipped`.
- SHOWN: all three collector parents had completed the June 11 window and were
  idle with live PIDs.

What changed:
- Merged accepted commits `493d9d76c` and `2ad46c2e6` into
  `review-stabilized` as merge commit `d270fe1dc`.
- No collector process, position, strategy configuration, evidence artifact,
  or historical record was modified.

Why this change:
- Future paper exits need durable reason attribution before the next strategy
  windows launch.
- Fresh runner and paper-engine subprocesses are launched for each UTC window,
  so collector-parent restarts are unnecessary.

Expected outcome:
- Future strategy-driven paper sell orders and fills preserve
  `exit_reason` and `exit_stack_rule`.
- Reconciled outcome rows and closed-trade summaries expose the same fields.

Verification:
- Merged execution/evidence regression slice:
  - SHOWN: `78 passed in 2.74s`.
- `git diff --check origin/review-stabilized...HEAD`
  - SHOWN: clean.
- Collector status:
  - SHOWN: canonical PID `23879`, idle/alive.
  - SHOWN: EMA PID `8480`, idle/alive.
  - SHOWN: breakout PID `32873`, idle/alive.

Remaining risk:
- HIGH implementation risk was independently accepted before integration.
- UNVERIFIED: no real post-integration paper exit has yet persisted the new
  attribution fields.
- Historical June 11 orders and fills remain unchanged.
- Acceptance state: `ACCEPTED`.

## 2026-06-12T09:43:25Z - Explain Excluded Paper Promotion History

Active role: `ENGINEER`

Objective: make the paper promotion gate explain why seven persisted round
trips no longer advance the provenance-qualified threshold.

What was found:
- SHOWN: the strict qualification rule introduced by `7ab11da59` requires both
  entry and exit fills to carry matching public OHLCV provenance.
- SHOWN: the canonical journal contains seven all-history round trips, but the
  JSONL evidence has nine fills with missing provenance and one qualified exit
  that is not paired with a qualified entry.
- SHOWN: April 20 signal prices materially diverge from contemporaneous paper
  fill prices, and the historical collector code explicitly supported sample
  OHLCV. Those trades cannot safely be relabeled as public-market evidence.
- SHOWN: the gate decision is therefore correct at zero qualified round trips;
  the defect is that the round-trip detail does not explain the exclusion.

What changed:
- Added diagnostic-only, unqualified-fill, and incomplete-qualified-fill
  context to the paper round-trip gate detail.
- Added regression coverage for missing JSONL history and the canonical
  `7 all-history / 9 unqualified / 1 incomplete` shape.
- Did not change qualification, threshold, expectancy, retirement, or
  promotion-ready calculations.

Why this change:
- Grandfathering or backfilling missing provenance would convert inference
  into promotion evidence and weaken the gate.
- Explicit reporting preserves the safety rule while preventing operators
  from interpreting `0/10` as lost or deleted trade history.

Expected outcome:
- `check_promotion_gates.py --json` continues to report zero qualified round
  trips, but states that seven all-history trips are diagnostic only and
  identifies the exact JSONL qualification gaps.

Verification:
- Canonical virtualenv targeted promotion tests:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py`
  - SHOWN: `44 passed in 0.93s`.
- Dashboard/monitor regression slice:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py tests/test_dashboard_page_runtime.py`
  - SHOWN: `37 passed in 1.05s`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  - SHOWN: `2120 passed, 33 skipped, 13 warnings in 209.18s`.
- Canonical gate-output inspection:
  - SHOWN: `ready=false`, `machine_ready=false`, and `7 pass / 2 unknown`
    remain unchanged.
  - SHOWN: the round-trip detail now reports seven diagnostic-only trips,
    nine of ten JSONL fills with missing or mismatched provenance, and one
    incomplete qualified fill.
- Old/new canonical JSON comparison:
  - SHOWN: after normalizing the intended round-trip detail, the only
    remaining difference was the per-run `evidence_scope.since_ts` timestamp.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m py_compile scripts/check_promotion_gates.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: clean.
- VERIFIED_ENV: implementation is isolated in
  `/private/tmp/crypto-bot-pro-provenance-audit`.

Remaining risk:
- HIGH: this is financial promotion-gate reporting, although decision logic is
  unchanged.
- Historical provenance remains unverified and is intentionally not backfilled.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-12 after commit `a8b12463e`.

## 2026-06-12T09:52:44Z - Integrate Accepted Provenance Explanation

Active role: `GATE`

Objective: integrate the independently accepted paper promotion-history
explanation while preserving existing audit records and active campaigns.

What was found:
- SHOWN: accepted branch `codex/explain-provenance-qualification` contained
  implementation commit `a8b12463e` and human-acceptance record `a2d20dea1`.
- SHOWN: `review-stabilized` had a pending, unrelated work-log entry for the
  previously accepted exit-attribution integration.
- SHOWN: canonical, EMA, and breakout collectors were idle/alive after
  completing their June 12 windows.

What changed:
- Preserved the pending exit-attribution integration record in commit
  `27b2e3a00`.
- Merged the accepted provenance-explanation branch into `review-stabilized`
  as `4ac757dfc`.
- Resolved the work-log conflict by retaining both chronological entries.
- No evidence artifact, campaign configuration, threshold, qualification
  decision, order route, or runtime process was changed.

Why this change:
- The accepted reporting fix must be visible on the canonical review branch.
- Keeping both work-log entries preserves the governed audit trail rather than
  choosing one branch's documentation over the other.

Expected outcome:
- Operators see why seven historical round trips are diagnostic only while the
  promotion gate continues to count zero provenance-qualified round trips.
- Active collectors continue without restart or evidence mutation.

Verification:
- Merged promotion, monitor, and dashboard regression slice:
  - SHOWN: `81 passed in 1.87s`.
- Accepted branch full suite:
  - SHOWN: `2120 passed, 33 skipped, 13 warnings in 209.18s`.
- Canonical gate output:
  - SHOWN: `ready=false`, `machine_ready=false`, `7 pass / 2 unknown`.
  - SHOWN: detail reports seven diagnostic-only trips, nine unqualified fills,
    and one incomplete qualified fill.
- `git diff --check`
  - SHOWN: clean before merge completion.
- VERIFIED_ENV: integration and verification ran in the canonical repository
  checkout.

Remaining risk:
- Historical provenance remains unverified and intentionally does not count
  toward promotion.
- No real post-integration exit has yet verified durable exit attribution.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human acceptance on 2026-06-12, followed by GATE
  integration commit `4ac757dfc`.

## 2026-06-12T09:55:27Z - Scope Monitor Promotion Progress

Active role: `ENGINEER`

Objective: prevent challenger paper monitors from displaying the canonical
`es_daily_trend_v1` promotion gate.

What was found:
- SHOWN: `paper_sim_monitor._promotion_progress_snapshot()` unconditionally
  called `load_paper_promotion_progress()` with canonical defaults.
- SHOWN: EMA and breakout monitor artifacts therefore displayed the SMA
  strategy's evidence directory, `0/30` days, and `0/10` round trips.
- SHOWN: the repo defines promotion thresholds only for
  `es_daily_trend_v1` / `sma_200_trend`; no accepted threshold policy exists
  for `ema_cross_default` or `breakout_default`.
- SHOWN: the Operations page rendered every false readiness value as
  `not_ready`, so a monitor-only change would still leave misleading UI text.

What changed:
- The monitor now passes the active preset, strategy, and symbol into the
  promotion-progress resolver.
- Canonical SMA campaigns continue loading the existing paper promotion gate.
- Noncanonical campaigns return `status=not_configured`,
  `applicable=false`, no blockers, and an explicit informational summary.
- Runtime normalization exposes `promotion_thresholds_applicable`.
- Operations renders `not_configured` instead of `not_ready` for challengers.
- Added monitor and dashboard-runtime regression coverage.

Why this change:
- Reusing one strategy's gate for another strategy misstates both evidence and
  policy.
- Inventing challenger thresholds in this patch would be an unsupported policy
  decision; explicit non-applicability is the smallest correct behavior.

Expected outcome:
- EMA and breakout campaign summaries show their own trade metrics without
  claiming progress against the SMA promotion gate.
- Canonical `es_daily_trend_v1` monitoring and gate calculations remain
  unchanged.

Verification:
- Canonical virtualenv targeted monitor, dashboard, and promotion slice:
  - SHOWN: `84 passed in 1.41s`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  - SHOWN: `2123 passed, 33 skipped, 13 warnings in 206.42s`.
- Real-state read-only `collect_once` snapshots:
  - SHOWN: canonical `es_daily_trend_v1` returned `applicable=true` and retained
    its existing qualified promotion summary.
  - SHOWN: `ema_cross_default` returned `status=not_configured`,
    `applicable=false`, and its own strategy ID.
  - SHOWN: `breakout_default` returned `status=not_configured`,
    `applicable=false`, and its own strategy ID.
- Python compilation:
  - SHOWN: monitor, dashboard runtime, and Operations page compiled cleanly.
- `git diff --check`
  - SHOWN: clean.
- VERIFIED_ENV: implementation is isolated in
  `/private/tmp/crypto-bot-pro-monitor-progress`.

Remaining risk:
- HIGH: this changes financial operator-status reporting.
- No challenger promotion policy is added; that remains a separate governance
  decision.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-12.

## 2026-06-12T10:07:48Z - Integrate Accepted Monitor Promotion Scoping

Active role: `GATE`

Objective: integrate the accepted challenger monitor promotion-policy scoping
without restarting active paper collectors.

What was found:
- SHOWN: accepted commit `038d5afe3` was a clean descendant of the current
  `review-stabilized` tip.
- SHOWN: canonical, EMA, and breakout collectors remained idle/alive after
  completing their June 12 windows.
- SHOWN: the operator requested that no additional full-suite tests run.

What changed:
- Merged `codex/scope-monitor-promotion-progress` into `review-stabilized` as
  `833b27f6d`.
- No collector process, evidence artifact, strategy threshold, campaign
  configuration, or order path was changed during integration.

Why this change:
- The accepted fix removes false canonical-gate status from challenger monitor
  and Operations surfaces.
- Targeted verification is sufficient for integration because the accepted
  branch already had full-suite proof and the operator explicitly stopped
  further full-suite runs.

Expected outcome:
- Canonical `es_daily_trend_v1` monitoring continues to show its configured
  promotion gate.
- EMA and breakout monitoring show `not_configured` rather than canonical SMA
  gate progress or `not_ready`.

Verification:
- Merged monitor, dashboard, and promotion regression slice:
  - SHOWN: `84 passed in 1.89s`.
- Python compilation:
  - SHOWN: monitor, dashboard runtime, and Operations page compiled cleanly.
- Real-state read-only snapshots:
  - SHOWN: canonical returned `applicable=true`.
  - SHOWN: EMA returned `applicable=false`, `status=not_configured`.
  - SHOWN: breakout returned `applicable=false`, `status=not_configured`.
- `git diff --check`
  - SHOWN: clean.
- Full suite was not rerun after acceptance at the operator's direction.
- VERIFIED_ENV: integration verification ran in the canonical repository
  checkout.

Remaining risk:
- Challenger promotion thresholds remain intentionally undefined pending a
  separate governance decision.
- Active monitor subprocesses will load the integrated code on their next
  daily campaign window; no parent restart was performed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human acceptance on 2026-06-12, followed by GATE
  integration commit `833b27f6d`.

## 2026-06-13T17:29:35Z - Restore Paper Collectors After Host Restart

Active role: `GATE`

Objective: verify the paper campaigns after a host restart and restore the
accepted detached daily loops without duplicating the completed June 13
evidence windows.

What was found:
- SHOWN: `review-stabilized` was clean and synchronized with
  `origin/review-stabilized` at `e18512637`.
- SHOWN: the canonical, EMA, and breakout status artifacts each reported
  `last_completed_day=2026-06-13`, but their recorded pre-restart PIDs were no
  longer alive.
- SHOWN: the completed June 13 windows recorded no new fills:
  canonical remained at 14 fills and 7 all-history closed trades, EMA remained
  at 4 fills and 2 closed trades, and breakout remained at 6 fills and 3
  closed trades.
- SHOWN: the current paper promotion gate counts 0 provenance-qualified round
  trips, not the 7 diagnostic all-history round trips. Nine of ten JSONL fills
  lack or mismatch required provenance, and the one provenance-qualified fill
  is not part of a complete qualified round trip.

What changed:
- Restarted the canonical detached daily loop with `sma_200_trend`,
  `es_daily_trend_v1`, `BTC/USDT`, Coinbase, `public_ohlcv_1d`, a 20-second
  strategy window, and a 300-second poll interval.
- Restarted the isolated EMA detached daily loop with `ema_cross`,
  `ema_cross_default`, `public_ohlcv_5m`, a 900-second strategy window, and a
  300-second poll interval.
- Restarted the isolated breakout detached daily loop with
  `breakout_donchian`, `breakout_default`, `public_ohlcv_5m`, a 900-second
  strategy window, and a 300-second poll interval.
- No strategy configuration, evidence record, promotion threshold, source
  code, or historical trade record was edited.

Why this change:
- The host restart terminated the accepted background processes even though
  their latest daily windows had completed successfully.
- The collector's built-in `--daily-loop --detach` path is the authoritative
  restart mechanism and checks the existing session file before running, so it
  preserves one evidence window per UTC day.
- Keeping each challenger under its dedicated `CBP_STATE_DIR` preserves
  evidence isolation.

Expected outcome:
- All three collectors remain idle for the rest of June 13 and wake for their
  next evidence window after the UTC date changes to June 14.
- Canonical and challenger evidence continue to accumulate independently.
- Promotion output continues to distinguish diagnostic all-history trades from
  provenance-qualified gate evidence.

Verification:
- Canonical status:
  - SHOWN: PID `7795`, `pid_alive=true`, `status=idle`,
    `reason=waiting_for_next_day`, and `last_completed_day=2026-06-13`.
- EMA status:
  - SHOWN: PID `7630`, `pid_alive=true`, `status=idle`,
    `reason=waiting_for_next_day`, and `last_completed_day=2026-06-13`.
- Breakout status:
  - SHOWN: PID `7628`, `pid_alive=true`, `status=idle`,
    `reason=waiting_for_next_day`, and `last_completed_day=2026-06-13`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: 39/30 calendar days, 0/10 provenance-qualified round trips, 7
    diagnostic all-history round trips, and `manual_review_required=true`.
- No test suite was run because this was an operational restart with no source
  changes and the operator previously directed that full-suite runs stop.
- VERIFIED_ENV: commands ran from the clean synchronized canonical checkout.

Remaining risk:
- HIGH: persistent financial evidence-collection background jobs were
  restarted.
- UNVERIFIED: the replacement processes have not yet crossed a UTC boundary
  and completed their first post-restart windows.
- The canonical promotion gate still requires ten complete
  provenance-qualified round trips; historical unqualified fills cannot
  satisfy that gate.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-13 after commit `8fa0a542a`.

## 2026-06-13T17:36:55Z - Idempotent Paper Campaign Recovery Command

Active role: `ENGINEER`

Objective: reduce post-reboot recovery from three manually reconstructed
collector commands to one explicit, idempotent, auditable operator command.

What was found:
- SHOWN: the June 13 host restart terminated all three detached collector
  parents even though their daily evidence windows had completed.
- SHOWN: the repo's canonical supervisors manage bot/runtime services but do
  not own the canonical and isolated paper evidence campaigns.
- SHOWN: the collector already provides the authoritative
  `--daily-loop --detach` startup path and duplicate-process protection.
- SHOWN: the paper promotion gate's 0/10 qualified result is intentional,
  independently accepted provenance policy from `7ab11da59`, not a new
  counting defect. The seven historical round trips remain diagnostic.

What changed:
- Added `configs/paper_evidence_campaigns.json` as the explicit manifest for
  the accepted canonical SMA, isolated EMA, and isolated breakout campaigns.
- Added `services/analytics/paper_campaign_recovery.py` to validate the
  manifest, query each isolated status surface, start only dead collectors,
  and verify replacement process state.
- Added `scripts/restore_paper_campaigns.py`; read-only status is the default,
  while `--restore` is required to start background jobs.
- Added `make status-paper-campaigns` and `make restore-paper-campaigns`.
- Added focused service/CLI tests and documented the recovery workflow in the
  Golden Path, script index, and `docs/PAPER_CAMPAIGN_RECOVERY.md`.
- Did not add OS-login auto-start and did not add paper campaigns to a generic
  live-adjacent supervisor.

Why this change:
- Reusing the existing collector preserves one process owner, one duplicate
  guard, and the accepted per-state evidence isolation.
- A manifest prevents strategy parameters from being reconstructed from memory
  after every reboot.
- Explicit restore is safer than automatic login startup because it does not
  launch financial background jobs merely because the desktop app opened.
- Extending a generic supervisor would broaden process-control scope and
  create additional stop/status semantics without being required for recovery.

Expected outcome:
- `make status-paper-campaigns` reports all configured campaigns and exits
  nonzero when any collector is not alive.
- `make restore-paper-campaigns` leaves live collectors unchanged, restores
  only dead collectors, and reports verified replacement PIDs.
- Repeated restore calls do not create duplicate collectors.
- Canonical and challenger evidence continue to use their existing isolated
  `CBP_STATE_DIR` paths and accepted signal-source/runtime parameters.

Verification:
- Targeted recovery, collector, and bootstrap regression slice:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py tests/test_run_paper_strategy_evidence_collector.py tests/test_bootstrap_helper_adoption.py tests/test_no_duplicate_script_bootstrap.py`
  - SHOWN: `35 passed in 0.97s`.
- Python compilation:
  - SHOWN: `paper_campaign_recovery.py` and
    `restore_paper_campaigns.py` compiled cleanly.
- CLI help:
  - SHOWN: exposes `--status`, `--restore`, repeatable `--campaign`, and
    `--config`.
- Make target dry run:
  - SHOWN: `status-paper-campaigns` invokes the read-only status mode and
    `restore-paper-campaigns` invokes explicit restore mode.
- `git diff --check`
  - SHOWN: clean.
- Canonical collector status from the untouched primary checkout:
  - SHOWN: PID `7795` remained alive and idle for the completed June 13
    canonical window during isolated implementation.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: implementation and verification ran in isolated worktree
  `/private/tmp/crypto-bot-pro-paper-restore`, based on synchronized commit
  `9ba375654`; active collectors in the canonical checkout were not restarted
  or modified.

Remaining risk:
- HIGH: this command starts persistent financial evidence-collection
  background jobs.
- UNVERIFIED: a real dead-process restore has not been executed from this
  feature branch because doing so would replace currently healthy accepted
  collectors.
- UNVERIFIED: post-reboot use still requires one explicit operator command;
  OS-login automation remains intentionally out of scope.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-14 after implementation commit `1b23f67b7`.

## 2026-06-15T02:15:41Z - Accepted Paper Campaign Recovery Integration

Active role: `GATE`

Objective: integrate the independently accepted paper campaign recovery
command into `review-stabilized` and verify the merged operator surface
without restarting active collectors.

What was found:
- SHOWN: accepted implementation commit `1b23f67b7` and acceptance record
  `5233c10d4` were merged into `review-stabilized` as `833a33ecb`.
- SHOWN: the integrated read-only status command reports all three configured
  collector parents alive: canonical SMA, EMA crossover, and Donchian
  breakout.
- SHOWN: each collector reports the June 15 window as completed and is idle
  until the next UTC day.
- SHOWN: the status payload does not prove the June 15 market-data window was
  valid; that health classification remains a separate campaign-lifecycle
  concern.

What changed:
- Recorded the accepted merge and post-merge verification in the governed
  work log.
- No runtime process, campaign configuration, evidence artifact, or trading
  behavior was changed during integration.

Why this change:
- The work log must preserve the accepted feature's transition from isolated
  branch proof to the primary review branch.
- Read-only verification confirms that the merged command observes the
  existing processes without replacing them.

Expected outcome:
- Future operators can trace the recovery feature from implementation through
  human acceptance, merge, and integrated verification.
- `review-stabilized` exposes one auditable command for status and explicit
  post-reboot restore.

Verification:
- `./.venv/bin/python scripts/restore_paper_campaigns.py --status`
  - SHOWN: `all_running=true`, `running_count=3`, `campaign_count=3`.
  - SHOWN: PIDs `7795`, `7630`, and `7628` remain alive.
- `./.venv/bin/python -m pytest -q tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py`
  - SHOWN: `12 passed in 0.16s`.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: commands ran from the primary
  `/Users/baitus/Downloads/crypto-bot-pro` checkout at merge `833a33ecb`.

Remaining risk:
- HIGH: the command can start persistent financial evidence-collection
  background jobs when invoked with `--restore`.
- UNVERIFIED: no dead-process restore was performed during integration because
  all accepted collectors were healthy.
- SHOWN: campaign process liveness is distinct from market-data validity; the
  latter requires a separate fail-closed lifecycle fix.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: implementation independently reviewed and accepted by
  the human operator on 2026-06-14; integrated without runtime changes on
  2026-06-15.

## 2026-06-15T02:28:02Z - Fail-Closed Public OHLCV Campaign Health

Active role: `ENGINEER`

Objective: prevent managed paper evidence campaigns from reporting successful
daily completion when the strategy runner receives no public OHLCV market data.

What was found:
- SHOWN: the canonical SMA, EMA, and Donchian collector parents were alive
  after the host restart.
- SHOWN: June 15 runner logs repeatedly reported Coinbase OHLCV fetch failure
  and `note=no_public_ohlcv`.
- SHOWN: no June 15 signal evidence files were produced, but each campaign was
  recorded as `status=completed`, `reason=completed`.
- SHOWN: `_run_strategy_window` replaced the last meaningful runner note with
  the runner's final `stopped` payload.
- SHOWN: the daily loop treated any non-empty session file, including a
  start-only or failed attempt, as a completed day.
- SHOWN: governance `INVALID` is terminal and therefore inappropriate for a
  recoverable infrastructure outage.

What changed:
- Preserved runner observations made during the current strategy window and
  classified a full public-OHLCV window with no observed market price as
  `stop_reason=no_public_ohlcv`.
- Made `run_campaign` return `ok=false`, `status=failed`, and skip leaderboard
  evidence persistence for that condition.
- Added `campaign_reason` to session-end evidence; failed runs now retain the
  existing `critical_error=true` and failed reconciliation classification.
- Changed daily completion detection to require a `phase=end`,
  `campaign_status=completed` session record.
- Added a bounded same-day retry policy: one initial attempt plus one retry,
  followed by failed status until the next UTC day.
- Added `max_daily_attempts` to the canonical campaign manifest and recovery
  launch contract, with a backward-compatible schema-v1 default of `2`.
- Documented that process liveness and campaign health are separate and that
  restore does not replace an alive collector that owns a pending retry.

Why this change:
- A market-data outage is retryable infrastructure failure, not valid strategy
  evidence and not terminal evidence contamination.
- `failed` preserves operator visibility and promotion-gate blocking without
  requiring manual repair of terminal governance state.
- Two attempts permit one transient recovery opportunity while preventing
  indefinite API retry loops and duplicate daily evidence campaigns.
- Keeping retry ownership in the existing parent preserves the accepted
  duplicate-process boundary.

Expected outcome:
- Public-OHLCV outages cannot create false completed campaign days.
- Failed windows create critical session evidence and cannot be mistaken for
  promotion-quality operation.
- Status and recovery output can show `running=true` with `ok=false`, making
  alive-but-unhealthy campaigns visible.
- A transient outage receives one bounded retry; a persistent outage remains
  failed until the next UTC day.
- Successful campaign and evidence-persistence behavior remains unchanged.

Verification:
- Targeted service, collector, and recovery slice:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_strategy_evidence_service.py tests/test_run_paper_strategy_evidence_collector.py tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py`
  - SHOWN: `54 passed in 0.67s`.
- Paper simulation monitor contract:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_run_paper_sim_monitor.py`
  - SHOWN: `21 passed in 0.33s`.
- Promotion-gate session-health contract:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py`
  - SHOWN: `42 passed in 0.95s`.
- Python compilation:
  - SHOWN: the collector, recovery service, and evidence service compiled
    cleanly.
- Collector CLI help:
  - SHOWN: `--max-daily-attempts` is exposed.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: verification used the primary virtual environment against the
  isolated worktree `/private/tmp/crypto-bot-pro-ohlcv-fail-closed` based on
  synchronized `review-stabilized` commit `f8e93e2ba`.

Remaining risk:
- HIGH: this changes financial evidence background-job lifecycle, retry
  behavior, and promotion-gate session inputs.
- UNVERIFIED: no live Coinbase outage/recovery cycle was induced; runtime proof
  is limited to existing logs plus deterministic tests.
- UNVERIFIED: existing collector processes still run the previously loaded
  code and must not be restarted onto this change before independent review.
- SHOWN: the already-written June 15 false-completion records are not mutated;
  a later healthy UTC day will supersede them in the latest-window gate.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-15 after implementation commit `9bd30e8bb`.

## 2026-06-15T02:31:21Z - Accepted Fail-Closed OHLCV Integration

Active role: `GATE`

Objective: integrate the independently accepted public-OHLCV fail-closed
lifecycle into `review-stabilized` without restarting active collectors.

What was found:
- SHOWN: implementation `9bd30e8bb` and human acceptance record `8467a821b`
  were clean and synchronized before integration.
- SHOWN: merge `9a6c3e08a` completed without conflicts.
- SHOWN: the canonical SMA, EMA, and Donchian collector parents remained alive
  at PIDs `7795`, `7630`, and `7628`.
- SHOWN: those existing processes still expose their pre-merge June 15 idle
  status; merging source code does not reload persistent Python processes.

What changed:
- Merged the accepted branch into `review-stabilized`.
- Recorded integrated verification and the explicit non-restart boundary.
- Did not alter runtime state, evidence files, process ownership, or campaign
  configuration outside the reviewed source changes.

Why this change:
- The merge makes the accepted fail-closed behavior canonical on the review
  branch while preserving the currently running evidence campaign.
- Deferring process restart avoids introducing a mid-day lifecycle change into
  active campaigns.

Expected outcome:
- New or intentionally restarted collectors use bounded retry and failed
  campaign classification for missing public OHLCV.
- Current collectors continue undisturbed until the next approved restart.

Verification:
- Integrated service, collector, and recovery slice:
  - SHOWN: `54 passed in 0.67s`.
- Integrated monitor and promotion-gate slice:
  - SHOWN: `63 passed in 0.98s`.
- Read-only campaign status:
  - SHOWN: `all_running=true`, `running_count=3`.
- `git diff --check`
  - SHOWN: clean.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: commands ran from the primary checkout at merge `9a6c3e08a`.

Remaining risk:
- HIGH: active collectors have not yet executed the accepted code.
- UNVERIFIED: the first real outage or healthy window after an approved
  collector restart has not occurred.
- SHOWN: June 15's previously written false-completion records remain
  historical and were not rewritten.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: implementation independently reviewed and accepted by
  the human operator on 2026-06-15 and integrated as `9a6c3e08a`.

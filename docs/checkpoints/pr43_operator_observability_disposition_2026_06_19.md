# PR #43 Operator Observability Disposition Audit - 2026-06-19

Active role: AUDITOR

## Objective

Convert PR #43 from a dirty aggregate runtime branch into an explicit rebuild
plan against current `master`.

## Evidence Basis

SHOWN:
- PR #43 is open, targets `master`, is not draft, and reports
  `mergeStateStatus=DIRTY`.
- `origin/master...origin/fix/p1-pre-live` reports `232 / 98`.
- `git cherry -v origin/master origin/fix/p1-pre-live` shows 96 patch-unique
  commits and 2 patch-equivalent commits already represented on `master`.
- Patch-unique history contains 95 non-merge commits and 1 merge commit.
- Current `master` already has the accepted paper simulation monitor path:
  `scripts/run_paper_sim_monitor.py` and
  `services/analytics/paper_sim_monitor.py`.
- Current `master` does not have the old PR #43 AI alert/oversight files:
  `scripts/run_ai_alert_monitor.py`, `scripts/run_ai_oversight_watch.py`,
  `services/ai_copilot/alert_monitor.py`, or
  `services/ai_copilot/oversight_watch.py`.
- Current `master` does not have the old PR #43 managed-symbol config files:
  `services/runtime/managed_symbol_config.py` or
  `services/runtime/managed_symbol_selection.py`.

UNVERIFIED:
- This audit does not prove behavioral equivalence between PR #43 and current
  `master`.
- This audit does not validate any PR #43 implementation by running the old PR
  branch.

## Disposition Key

`superseded`:
- Equivalent, newer, or intentionally different current-master work exists.
- Do not cherry-pick the old commit.

`rebuild`:
- The idea is still useful, but the old commit must be rebuilt from current
  `master` as a focused PR with targeted tests.

`drop`:
- The commit is stale planning, merge metadata, test-only timestamp churn, or an
  obsolete artifact that should not be carried forward.

## Commit Disposition Table

| Commit | Disposition | Reason |
|---|---|---|
| `02b3ed8d` | rebuild | AI oversight watch is not present on current `master`; rebuild as read-only operator monitoring. |
| `db032231` | rebuild | Pipeline-loop error isolation is runtime-supervision behavior and needs a focused current-master PR. |
| `4ee1f81c` | rebuild | Safe pipeline wrapper is absent on current `master`; rebuild separately from live execution changes. |
| `46549f9d` | rebuild | Start-bot safe-consumer routing affects startup topology; rebuild only with startup tests. |
| `8a2dd118` | rebuild | AI alert monitor files are absent on current `master`; rebuild read-only alerting first. |
| `a2be80f6` | rebuild | Atomic runtime status writes are useful but should be rebuilt narrowly against current file utilities. |
| `32b327fa` | rebuild | Bot converge self-stop behavior touches runtime supervision; rebuild with `run_bot_runner` tests. |
| `287fd125` | rebuild | Paper venue alignment in bot runner touches runtime config; rebuild from current runner. |
| `09bb58f1` | rebuild | Copilot safety context should read current canonical runtime files if the alert monitor is rebuilt. |
| `45430d04` | rebuild | Duplicate paper executor starts are runtime/concurrency behavior; rebuild with locking tests. |
| `ae9d2e4f` | rebuild | AI alert monitor lifecycle with bot runtime is useful but absent on current `master`. |
| `25507b84` | rebuild | Multi-symbol architecture docs should be rebuilt with current runtime constraints. |
| `82f2ef20` | rebuild | Supervised multi-symbol path remains useful planning but must align with current campaign ownership. |
| `953902cb` | rebuild | Runtime truth narrative should be refreshed only if the associated runtime rebuild lands. |
| `b67b99df` | rebuild | Managed multi-symbol paper runtime files are absent on current `master`. |
| `cde84dd0` | rebuild | Scanner-managed paper symbols are absent on current `master`; rebuild after data-quality gates. |
| `a0b20c0c` | rebuild | Scanner symbol preservation bounds belong with the managed-symbol rebuild. |
| `ef71b8b1` | rebuild | Start-bot topology convergence is runtime behavior and should be split from observability. |
| `81b67ca1` | rebuild | AI monitor loop status belongs with the alert-monitor rebuild if still needed. |
| `200d577c` | rebuild | AI monitor report metadata belongs with the alert-monitor rebuild if still needed. |
| `c23d3823` | rebuild | Bot converge symbol-order handling belongs with managed-symbol runtime if rebuilt. |
| `c50a2af5` | rebuild | Managed symbol order canonicalization belongs with managed-symbol runtime if rebuilt. |
| `54019392` | rebuild | Supervised soak status report is absent on current `master`; rebuild as read-only reporting. |
| `a643a622` | superseded | Paper-soak gate interpretation has since been replaced by current paper-gate docs. |
| `d8f2863b` | drop | Old dashboard-audit todo is stale planning; use current checkpoint list instead. |
| `423b3419` | drop | Old full-repo audit master todo is stale planning. |
| `e4f26e7f` | superseded | Safe-worktree/soak guidance has been replaced by current branch-alignment and campaign docs. |
| `2210c9fb` | superseded | Resume/live-enabled behavior was handled by accepted audit fixes on current `master`. |
| `91bce943` | superseded | Campaign governance enforcement was handled by accepted audit fixes on current `master`. |
| `612382a5` | superseded | Deployment-stage transition checks were handled by accepted governance fixes. |
| `23f0bcbb` | superseded | Control-kernel governance wiring was handled by accepted audit fixes. |
| `76183c61` | superseded | Dashboard role guarding was handled by accepted VIEWER/OPERATOR boundary fixes. |
| `08e5a714` | superseded | Paper reconciliation OPERATOR gating was handled by accepted auth-boundary fixes. |
| `318a2ccb` | superseded | Automation save OPERATOR gating was handled by accepted auth-boundary fixes. |
| `1d597a15` | superseded | Settings save OPERATOR gating was handled by accepted auth-boundary fixes. |
| `39bd28dc` | superseded | Signals direct-origin guard wiring was handled by accepted security fixes. |
| `6f68adb9` | superseded | Evidence direct-origin guard wiring was handled by accepted security fixes. |
| `28a81e35` | superseded | GateIO client-id behavior was handled by accepted exchange-client fixes. |
| `60fff68f` | superseded | OHLCV timeout/retry behavior was handled by accepted signal-replay fixes. |
| `c72abada` | superseded | Dashboard save role requirements were handled by accepted auth-facing fixes. |
| `5863c4f0` | superseded | Campaign governance enforcement was handled by accepted evidence-service fixes. |
| `7c869b1c` | superseded | Patch-equivalent restore-live-enable behavior already exists on current `master`. |
| `d9b8d8a6` | superseded | Missing live-guard fail-closed behavior was handled by accepted live-guard fixes. |
| `c8401f93` | superseded | Patch-equivalent ES evidence mapping already exists on current `master`. |
| `18126e68` | superseded | Direct-origin auth gate behavior was handled by accepted auth-gate fixes. |
| `226ca164` | rebuild | Soak observability scripts are not fully present on current `master`; rebuild read-only if still needed. |
| `e8b9d379` | rebuild | Canonical soak runtime truth belongs with the supervised-soak reporting rebuild. |
| `a0539ce9` | rebuild | AI alert monitor runtime parity belongs with the alert-monitor rebuild. |
| `f4f5605a` | rebuild | Paper runtime symbol truth belongs with managed-symbol runtime if rebuilt. |
| `626bdd82` | rebuild | Safe-idle runtime status belongs with safe-wrapper/supervised-soak rebuilds. |
| `1e656327` | drop | Timestamp-only test refresh has no standalone product value. |
| `b233580a` | superseded | Unknown strategy fail-closed behavior was handled by accepted strategy-registry fixes. |
| `b0dbffd2` | rebuild | Supervised soak truth in Operations belongs with supervised-soak reporting rebuild. |
| `db551ebd` | superseded | Paper gate truth in home digest has since been rebuilt and accepted on current `master`. |
| `9f79dc3b` | superseded | Automation badge truth has been handled by current dashboard runtime work. |
| `12d4d475` | superseded | Settings provider status labeling has been handled by current dashboard view work. |
| `e1d0cbfe` | superseded | Dashboard trade provenance labeling has been superseded by current evidence provenance work. |
| `3e755a38` | drop | Old test isolation for operations soak warnings has no standalone product value. |
| `e7f0cede` | superseded | Paper soak gate policy has been superseded by current paper-gate provenance docs. |
| `53fcf2b5` | drop | Runtime integration expectation adjustment is stale test churn unless a current failure reproduces. |
| `5f4c5866` | superseded | OHLCV retry throttling has been handled by current strategy-runner stability work. |
| `32477091` | superseded | Daily OHLCV cache prewarm has been handled by current strategy-runner stability work. |
| `56ba0f9a` | superseded | Paper campaign latch reset has been handled by current evidence-service work. |
| `9a14a4d0` | superseded | Cached-price fallback has been handled by current runner stability work. |
| `1346bb71` | superseded | Campaign cooldown clearing has been handled by current evidence-service work. |
| `854ea007` | superseded | First ES signal-trade enablement has been superseded by current campaign/gate evidence work. |
| `4606b3e1` | superseded | First ES signal-trade flag export has been superseded by current campaign/gate evidence work. |
| `bbab3f87` | superseded | Strategy-state delete behavior exists on current `master` through accepted storage work. |
| `f0257a8a` | drop | Deferred AI copilot monitor task is stale planning now captured in this disposition. |
| `56ed7a66` | superseded | Canonical ES evidence in collector status is handled by current gate/provenance reporting. |
| `f5df9027` | superseded | Managed live consumer routing was handled by accepted safe-wrapper/canonical module fixes. |
| `9fcb2439` | superseded | Execution submit/fill ordering has been handled by accepted execution/funnel fixes. |
| `2099a782` | superseded | Direct consumer entrypoint alignment has been handled by accepted execution wrapper fixes. |
| `24a81616` | drop | Ambient-state test isolation has no standalone product value unless a current failure reproduces. |
| `dd0dc829` | drop | Old live-start prep sheet is stale planning. |
| `82133ea1` | superseded | Paper simulation monitor has been rebuilt and accepted on current `master`. |
| `30ebc6f5` | superseded | Paper sim watch reports have been rebuilt and accepted on current `master`. |
| `be10d0db` | superseded | Paper sim Operations surface has been rebuilt and accepted on current `master`. |
| `41e1809b` | superseded | Paper sim supervision during evidence runs has been rebuilt and accepted on current `master`. |
| `21aef052` | superseded | Paper sim local watch notifications have been rebuilt and accepted on current `master`. |
| `3620f0a0` | superseded | Paper sim notification configurability has been rebuilt and accepted on current `master`. |
| `0763ad84` | superseded | Paper sim notification status in Operations has been rebuilt and accepted on current `master`. |
| `1de38518` | superseded | Paper sim watch reports in copilot reports have been rebuilt and accepted on current `master`. |
| `7606fa42` | superseded | Dashboard controls for paper sim watches have been rebuilt and accepted on current `master`. |
| `975ad6da` | drop | Old 2026-05-15 decision record/temp runtime helper should not be revived from this branch. |
| `c384dfa5` | superseded | Default paper sim watch seeding has been rebuilt and accepted on current `master`. |
| `fdb2e074` | superseded | Paper watch seed health surface has been rebuilt and accepted on current `master`. |
| `9b245c16` | superseded | Initial paper sim false-positive suppression has been rebuilt and accepted on current `master`. |
| `c4b5bb93` | superseded | Paper sim current-window scoping has been rebuilt and accepted on current `master`. |
| `6f5a6b66` | superseded | Campaign latest-fill scoping has been rebuilt and accepted on current `master`. |
| `97a2b289` | superseded | Sample-backed paper sim fill handling has been rebuilt and accepted on current `master`. |
| `13f71aab` | superseded | Temp-state decision-record isolation has been rebuilt and accepted on current `master`. |
| `b6d5f4e4` | superseded | Default watch-state reset per campaign has been rebuilt and accepted on current `master`. |
| `6391bd86` | superseded | Current-run watch report retention has been rebuilt and accepted on current `master`. |
| `38fad8eb` | superseded | Sample-mode paper tick advancement has been rebuilt and accepted on current `master`. |
| `822e7f48` | superseded | In-window paper round-trip reporting has been superseded by current provenance-qualified gate reporting. |
| `480935bd` | drop | Stale persisted live-arm rejection test expectation has no standalone product value. |
| `ac72eec7` | drop | Merge commit metadata; do not preserve as history. |

## Recommended Rebuild Groups

1. AI operator alerting and oversight:
   `02b3ed8d`, `8a2dd118`, `09bb58f1`, `ae9d2e4f`, `81b67ca1`,
   `200d577c`, `a0539ce9`.

2. Safe runtime wrappers and bot topology:
   `db032231`, `4ee1f81c`, `46549f9d`, `a2be80f6`, `32b327fa`,
   `287fd125`, `45430d04`, `ef71b8b1`, `626bdd82`.

3. Managed multi-symbol paper runtime:
   `25507b84`, `82f2ef20`, `953902cb`, `b67b99df`, `cde84dd0`,
   `a0b20c0c`, `c23d3823`, `c50a2af5`, `f4f5605a`.

4. Supervised soak reporting:
   `54019392`, `226ca164`, `e8b9d379`, `b0dbffd2`.

## Closure Recommendation

Do not merge PR #43.

After this disposition is independently accepted:
- Close PR #43 with a comment linking this checkpoint.
- Close PR #42 as superseded by PR #43's accepted disposition.
- Rebuild only the commits marked `rebuild`, grouped above, from current
  `master`.
- Do not rebuild commits marked `drop` unless a fresh current-master failure
  reproduces.
- Do not cherry-pick commits marked `superseded`; compare current-master
  behavior only if a specific gap is raised.

## Risk

HIGH:
- PR #43 touches runtime supervision, bot startup, AI monitoring, dashboard
  operator surfaces, live-guard/auth surfaces, evidence collection, and paper
  campaign behavior.
- This document is audit planning only and does not prove any implementation.

Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
independent review sign-off.

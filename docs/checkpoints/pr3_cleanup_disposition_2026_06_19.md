# PR #3 Cleanup Disposition Audit - 2026-06-19

Active role: AUDITOR

## Objective

Preserve the useful information from PR #3 without directly merging a stale,
dirty branch into current `master`.

## Evidence Basis

SHOWN:
- PR #3 is open, targets `master`, is not draft, and reports
  `mergeStateStatus=DIRTY`.
- `origin/master...origin/cleanup/import-collection-failures` reports
  `283 / 54`.
- The branch-only history contains 52 non-merge commits and 2 merge commits.
- The branch touches high-risk execution, reconciliation, live intent queue,
  paper engine, and storage surfaces.
- Current `master` already contains related surfaces including
  `services/execution/intent_lifecycle.py`, `scripts/run_paper_scenario.py`,
  `tests/test_execution_claim_race.py`,
  `tests/test_live_intent_queue_integrity.py`,
  `tests/test_paper_queue_authority.py`, and
  `tests/test_live_queue_submit_owner_authority.py`.
- Current `master` already contains phase1 research-copilot skip guards and
  pre-release sanity skip semantics.

UNVERIFIED:
- This audit does not prove behavioral equivalence between PR #3 and current
  `master`.
- This audit does not validate any PR #3 implementation by running the old PR
  branch.

## Disposition Key

`superseded`:
- Equivalent or newer surface exists on current `master`.
- Do not cherry-pick the old commit.
- If closure is challenged, compare behavior from current `master`, not the old
  branch.

`rebuild`:
- The commit may contain still-useful safety or runtime behavior.
- Do not merge the old commit directly.
- Rebuild as a narrow PR from current `master` with targeted tests.

`drop`:
- The commit is an old test/CI workaround, stale compatibility patch, or merge
  metadata with no standalone product value.
- Do not preserve unless a fresh failure reproduces on current `master`.

## Commit Disposition Table

| Commit | Disposition | Reason |
|---|---|---|
| `5229387e` | superseded | Current phase1 research-copilot tests already include explicit skip guards for absent sidecar modules. |
| `b1d36aa6` | superseded | Current phase1 config/smoke tests already skip when the sidecar package is absent. |
| `17e3f1fe` | rebuild | Touches `services/security/role_guard.py`; any role normalization must be reviewed as a fresh auth-facing change. |
| `b5af1a6b` | rebuild | Touches runtime control and live execution adapter surfaces; do not merge from stale branch. |
| `20e43ba0` | drop | Broad stale-test compatibility patch; current CI is green and individual failures should be handled directly if they reappear. |
| `bb0f46ba` | superseded | Docs/governance alignment is now maintained in current checkpoint and work-log artifacts. |
| `1442b260` | rebuild | Intent claim race hardening is valuable but touches execution state ownership; rebuild narrowly with `test_execution_claim_race`. |
| `dce20b9d` | rebuild | `paper_stop` import-time mutation risk is valid to check, but the stale patch should not be merged directly. |
| `cb13f5ab` | rebuild | Companion test update for intent claim race; keep with the narrow race-hardening rebuild if needed. |
| `5c275193` | superseded | Dashboard facade seams have changed substantially; current dashboard tests should be the source of truth. |
| `97ad661e` | superseded | Maintenance/live-gate path alignment should be checked against current scripts, not the old branch. |
| `d4f9d4e5` | rebuild | Live reconciler error-transition behavior is high risk and needs a focused current-master PR if still missing. |
| `60e1e83b` | superseded | Current `master` already has `services/execution/intent_lifecycle.py`; compare behavior only if a fresh gap is found. |
| `82c1e68d` | rebuild | Execution store lifecycle rules are high-risk storage behavior; rebuild with current storage tests if needed. |
| `4c0d321c` | rebuild | Live intent queue transition guarding is high-risk live execution state behavior. |
| `68a8be1f` | rebuild | Sandbox-mode propagation through live execution must be reviewed against current live-arming contracts. |
| `a1714841` | rebuild | Live reconciler authority routing is high-risk and should be rebuilt only with focused reconciler tests. |
| `2b1cf4f4` | rebuild | Paper intent queue status transition guards touch execution queue semantics. |
| `607884ae` | rebuild | Bot runner reconciliation behavior touches supervisor runtime truth; rebuild only if current tests expose the gap. |
| `1997e5e3` | drop | Maintenance import cleanup is stale unless current `scripts/maintenance.py` reproduces the import problem. |
| `c7914f11` | rebuild | Queue authority consolidation across execution paths is broad and high-risk; split before any implementation. |
| `92a052e9` | superseded | Current `master` already has `scripts/run_paper_scenario.py` and `tests/test_paper_scenario_roundtrip.py`. |
| `f0d7d46c` | drop | Old skip/ruff workaround; do not preserve unless current sanity checks fail. |
| `86689515` | drop | Old phase1/mypy skip workaround; current skip semantics already exist. |
| `9c1eaea9` | drop | Old phase1 skip/mypy repair; current master should be the source of truth. |
| `6e9e1e90` | rebuild | Paper queue authority context affects execution ownership and needs narrow validation. |
| `67129d85` | rebuild | Held-intent transition repair is execution state behavior and should be evaluated against current held-intent tests. |
| `77e100ae` | rebuild | Paper runner import-time venue capture is a valid runtime concern; rebuild only if current code still captures import-time state. |
| `e2afafd5` | drop | Manual audit script interpreter selection is stale unless current audit scripts fail. |
| `4dbae09b` | drop | Companion manual-audit selector export; no standalone value without a current failure. |
| `154aebfe` | drop | Old CI ruff scoping workaround; current workflows are passing. |
| `47755277` | drop | Old legacy-risk ruff exclusion; current workflow should not inherit stale exclusions by default. |
| `5fbd1a0e` | rebuild | Paper engine evaluation in direct submit path is execution behavior and needs focused current-master review. |
| `f8a5c508` | rebuild | Authority context routing in consumers affects execution queue ownership. |
| `2e86485a` | drop | Old CI ruff scope workaround; no direct product behavior. |
| `ca590b9c` | rebuild | Held-intent transitions through state authority are high-risk queue state behavior. |
| `ab846b23` | rebuild | Intent writer queue mirror failure surfacing is useful but affects execution bridge behavior. |
| `56ad4cab` | drop | Old validate ruff scope workaround. |
| `ef43d64f` | drop | Old bootstrap sanity ruff exclusion. |
| `ce5e7864` | drop | Old strict ruff narrowing workaround. |
| `edb25ce0` | drop | Old CI assertion adjustment; keep only if a current signal-aware order assertion failure reproduces. |
| `5c555105` | rebuild | Exception narrowing in execution consumers/reconciler is high-risk fail-closed behavior. |
| `c2a342fe` | rebuild | Companion lint repair for exception narrowing; keep with the focused exception-handling rebuild if needed. |
| `846ac9ef` | rebuild | Reconciler authority context is execution reconciliation behavior. |
| `4aa75f7c` | rebuild | Atomic lock acquisition and live consumer control file isolation are concurrency/cancellation-sensitive. |
| `f40ef886` | rebuild | Atomic paper fill application affects fill accounting and strategy evidence. |
| `d4cad6d9` | rebuild | Intent queue upsert/status guarding affects execution state integrity. |
| `ee57b3b0` | rebuild | TOCTOU lock replacement is concurrency-sensitive; current code already has some `open(..., "x")` usage but equivalence is unproven. |
| `4dde5811` | rebuild | Atomic risk-claim transaction is financial risk-control behavior. |
| `9808f21e` | superseded | Current `storage/paper_trading_sqlite.py` already uses `INSERT OR IGNORE` for paper orders. |
| `ada2f942` | rebuild | Live reconciler crash paths are high-risk fail-closed behavior. |
| `eae84871` | superseded | Current `intent_lifecycle` already includes terminal `cancelled` and `error` states; verify only if queue storage behavior differs. |
| `408286f4` | drop | Merge commit metadata for old PR #14; contents are represented by branch commits and should not be merged as history. |
| `12530037` | drop | Merge commit metadata for old PR #19; contents are represented by branch commits and should not be merged as history. |

## Recommended Rebuild Groups

1. Queue lifecycle and authority:
   `1442b260`, `cb13f5ab`, `2b1cf4f4`, `c7914f11`, `6e9e1e90`,
   `67129d85`, `ca590b9c`, `d4cad6d9`.

2. Live reconciler and live intent safety:
   `d4f9d4e5`, `4c0d321c`, `68a8be1f`, `a1714841`, `f8a5c508`,
   `846ac9ef`, `4aa75f7c`, `ee57b3b0`, `4dde5811`, `ada2f942`.

3. Paper execution and evidence safety:
   `5fbd1a0e`, `77e100ae`, `f40ef886`.

4. Runtime/script hardening:
   `b5af1a6b`, `dce20b9d`, `607884ae`, `ab846b23`.

5. Drop-only CI/test cleanup:
   `20e43ba0`, `f0d7d46c`, `86689515`, `9c1eaea9`, `154aebfe`,
   `47755277`, `2e86485a`, `56ad4cab`, `ef43d64f`, `ce5e7864`,
   `edb25ce0`.

## Closure Recommendation

Do not merge PR #3.

After this disposition is independently accepted:
- Close PR #3 with a comment linking this checkpoint.
- Rebuild only the commits marked `rebuild`, grouped as above, from current
  `master`.
- Do not rebuild commits marked `drop` unless a fresh current-master failure
  reproduces.
- Do not cherry-pick commits marked `superseded`; compare behavior from current
  `master` only if a specific gap is raised.

## Risk

HIGH:
- PR #3 touches live execution, order/intent lifecycle, reconciliation,
  concurrency, and risk-control behavior.
- This document is audit planning only and does not prove any execution fix.

Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
independent review sign-off.

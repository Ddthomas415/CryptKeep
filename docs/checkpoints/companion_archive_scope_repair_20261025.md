# Archival probe scope repair, October 25

Role: ENGINEER. Risk: HIGH. Separately ACCEPTED_WITH_RISK, offline scope only.
Runtime/explanation remains INCOMPLETE. No service operation authorized here.

## Demonstrated mismatch and chosen boundary

V6e returned five citations; three recorded document-ID hashes had no match in
the frozen archive. The exact remote first failure remains UNVERIFIED because
the old receipt omitted the verifier result. The existing article-view CTE
allows eligible non-archive database rows, while the archival verifier requires
all cited IDs to belong to the approved snapshot. Controlled handler tests
reproduce that incompatibility; they are not replay of missing live prose.

The repair changes only the existing single-cited-query archival proof profile.
Ordinary live retrieval keeps the identical SQL CTE, live-row eligibility, query,
ranking and limits. General intelligence/news/context capability is preserved.
No verifier predicates, approved witnesses, archive files or source lineage are
relaxed, replaced or silently extended. No current-cause or profitability claim.

## Changes

- `phase1_research_copilot/memory_retrieval/article_view.py`: factor the original
  CTE into repair and live branches; default CTE bytes remain identical. An
  explicit strict Boolean `frozen_only` selects the repair-only CTE before the
  caller's ranking and LIMIT. The same SQL statement validates live source
  lineage and selects the archived projection, including empty results.
- `phase1_research_copilot/memory_retrieval/main.py`: require the approved archive
  when the request-local probe is active; apply frozen scope to all five document
  queries (recent/past/future/vector/keyword). Ordinary requests retain live
  scope, including ordinary missing-archive behavior. Startup/settings alone
  do not silently enable the archival restriction.
- `scripts/research/companion_installer.py`: record only fixed-key Boolean
  verifier outcomes and shape validity before the existing gate. Exceptions or
  timeouts yield a fixed label with no exception text. False means not established
  or not evaluated, not five independently disproven properties. Receipt-write
  failure still prevents query acceptance and follows existing recovery.
- Tests: add 22 focused cases; retain the existing multi-service ASGI flow,
  replacing its now-invalid missing-archive probe fixture with an explicit
  synthetic archived view. That fixture is not real archive/runtime proof.

The recovered service tree is not tracked in this checkout. The explicit
`repair.diff` below captures its source changes even where normal git diff does
not display them. No git history or unrelated dirty changes were reset.

## Preserved evidence and diff

Directory: `docs/review_artifacts/companion_archive_scope_repair_20261025/`.

- `pre_change_sources.tar` SHA256
  `a02dd1774b91a448335589bef015184b6fb64dfa718a71fd0baee151dd48b5d3`:
  exact three source files and the existing test before this repair.
- `repair.diff` SHA256
  `dadea0055a3ab6475b2e5c5310e397d55fd633ed1b24e39295162bcf350b5634`:
  minimal delta against that backup plus the new test file.
- `report.json` SHA256
  `7ff14e8f8f46ee30aa17d526fe670c01bd952dd54155fdc517447d05207dfd6d`:
  thirteen source/input bindings, preservation hashes and verification results.

Old runtime receipts, outcome, reviews, archive manifest/body/snapshot and
topical approvals remain unchanged. Prior source-bound runtime packets now
deliberately fail current-source checks; no old packet is rebased or activated.
Both V6e operations remain consumed; removed prepared IDs cannot be reused.

## Verification

VERIFIED_ENV, isolated offline command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_archive_probe_scope.py tests/test_companion_article_view.py tests/test_companion_probe_policy.py tests/test_companion_running_update.py tests/test_companion_evidence_checks.py
```

SHOWN: 285 passed in 13.29 seconds; 140 existing FastAPI startup deprecation
warnings. New scope file contains 22 cases. The preceding behavior reproduction
was 2 failed/1 passed: probe admitted synthetic live-only ID 9001; verifier
exception diagnostic was absent; ordinary live behavior already passed.
Three earlier missing-API failures are test scaffolding, not additional empirical
behavior findings. Intermediate 280-case pass preceded five extra adversarial
cases; it is not independent confirmation.

Tests use synthetic SQL/storage responses, ASGI handlers without lifespan,
real response-builder functions and the unchanged pure evidence evaluator.
They confirm SQL construction and control-flow composition, not actual PostgreSQL
execution, native containers, installed code or current persistence. Network and
subprocess tripwires are enabled. Full suite not run. No token/settings-reader,
Docker/native, live HTTP/DB, startup/cutover, scheduler or trading operation.

## Handoff

Sources/tests/report/diff remain frozen after independent review. Do not infer a successful
explanation or unique historical cause. The new receipt will distinguish returned
checks from an operation exception; it still will not expose the remote first
failing predicate when the verifier collapses all failures to false.

No new runtime packet, approval or attempt is created by this repair. Further
operational work needs new source bindings and independent review, fresh-state
evidence and separate bounded authorization. No automatic retry or reset.

## Independent review and closeout

Separate GATE ACCEPTED_WITH_RISK, no blocking findings. Review SHA256
`4747ffdc6f86e549bdc703dd5ee017456ae221ad456b7b97d84828d11dbe5f35`
at `independent_review.json` in the repair artifact directory. Reviewer compared
the backup members to current files, reproduced the exact diff, verified all
13 report bindings and independently ran 124 tests in 2.91 seconds:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_archive_probe_scope.py tests/test_companion_probe_policy.py tests/test_companion_running_update.py
```

Parent read the entire review and verified 16 unique source/input/artifact
bindings. No reviewed source/test/report/diff changed afterward. No new test run,
service operation or packet generation was needed for this recording step.

Important retained limitation: Qdrant limits its vector candidates before SQL
hydration. Frozen SQL excludes outside-archive candidates, but may underfill
vector results. This repair does not archive-filter Qdrant ranking or guarantee
recall. "Before limits" above means the five document SQL queries' own ranking
and limits, not every upstream selection operation. No vector change is proposed
as a prerequisite or silently added to this repair.

Offline implementation and review are complete. Runtime remains INCOMPLETE.
Next safe scope is fresh source-bound integration inputs for the existing
mechanism, not reuse of the consumed V6e attempt or a blind service retry.

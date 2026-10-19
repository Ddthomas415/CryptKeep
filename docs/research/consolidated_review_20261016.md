# CryptKeep consolidated review - October16, 2026

Active role: AUDITOR. Overall engineering/economic readiness: INCOMPLETE.
Scope: current dirty checkout, active research/index documents, saved ES
endpoint evidence, multi-symbol E10 artifacts, integrity archive, local runtime
availability, public Git remote refs and test execution. No implementation,
trading, deployment, service restart, configuration change or strategy rerun.

This is not a claim to have freshly read every historical attachment or every
line of the repository. Historical family coverage is reused with its original
limits:437 entries,396 full-content reads,4 structural-only,1 partial,6 supplied
outputs compared and30 historical diffs. Reading, independent review, tests,
publication, operating proof and profitability remain separate.

## Findings In Priority Order

### 1. Reused history is still presented as an untouched holdout

SHOWN: RESEARCH_BRIEF.md lines77/86 direct candidate work to treat2024-26 as a
holdout. Its own line92, symbol_coverage.csv and correction C8 acknowledge
selection on those years. E10's one-run registration does not make those prices
unseen. This can produce invalid confidence in the next result.

Action: correct the active instruction, preserving original studies. Historical
reruns remain reproduction/sensitivity evidence, not fresh confirmation. New
confirmatory work needs rules frozen before its genuinely unseen observations.

### 2. The mandatory brief contradicts the adopted universe and current status

SHOWN: its line8 says all25 symbols trade on Coinbase, but the mandate records
MATIC delisting and24 current products. Line45 says other symbols are untested
despite E10's ten-symbol results. Line65 says tracker v2 is unscheduled with23
tests; saved automation is ACTIVE, the README records27 tests and separate
review, and first delivery is October18 20:47 New York. The maker/taker row also
points to v2 although the accepted design direction is preserved in draft v3.

Action: one evidence-linked summary correction, not another strategy build or
duplicate schedule. Project scope remains25 symbols; venue availability,
research coverage and trading eligibility must stay distinct.

### 3. Delivery is not currently equivalent to implemented capability

SHOWN now: Docker's configured local socket is absent; the documented
127.0.0.1:8002/healthz endpoint refuses the connection. The current intelligence
deployment is therefore unavailable through that inspected route, despite older
successful integration records. Other uninspected endpoints remain UNVERIFIED.

SHOWN: local config has no alerts block or Slack webhook, dispatcher defaults
to disabled, and the last saved dispatch says alerts_disabled. A working Slack
channel/delivery has not been demonstrated. Do not interpret ok/skipped as sent.

In contrast, the existing context collector's PID exists and its04:53UTC status
reports all6 source checks passing,775 writes and2 cumulative errors; paper
collector PID exists with October16 completed and waiting-for-next-day status.
These are point-in-time liveness/status observations, not continuous-health or
process-identity certification. No collectors were restarted.

Action: restore the existing intelligence path and verify a cited user query;
configure the already-chosen Slack channel securely and prove delivery after
authorization/configuration. Do not build replacement infrastructure first.

### 4. Numerical reproduction does not resolve E10's selection/data limitations

Separate auditors verified saved predicates: the equal-weight ten-symbol
portfolio FAIL and all ten standalone classifications match the registered
metrics. ETH/AVAX/DOT CANDIDATE means relative Sharpe/drawdown improvement over
holding that same asset, not established positive net profit. DOT's saved
standalone endpoints are926.92 in D and592.63 in H from1000 each.

SHOWN: surviving-symbol selection remains unmeasured. load_api silently filters
nonpositive prices and collapses duplicate days; missing observations are not
classified as venue suspension versus acquisition failure. Registered freezes
are models, not proof prices were executable throughout a gap. The no-frozen-
holdings summary concerns the trend portfolio, not every benchmark.

Action: keep the original FAIL and scoped classifications. Before any new
experiment, pin a point-in-time universe, grid audit, missingness classifications,
cash/no-leverage rule, sizing, turnover and benchmark-specific frozen exposures.
Do not retune E10 or generalize it to the untested15 symbols or other families.

### 5. Integration and preservation remain unfinished

SHOWN: the inventory contains49 modified tracked files and3648 untracked files;
the index is empty. Current GitHub master is
be34a18a3f7b78941cddb4eabe373b33788526ce, while the checkout's cached origin/master
is97c24c8e4. No pull/reset/staging was performed. Dirty work is not a defect by
itself, but it is not a reproducible published release boundary.

Integrity auditor verified239 checksum comparisons over88 distinct archive
files, with no missing manifest-listed files. Perturbed input inventories are
not the input datasets themselves. The separate E6 raw backup is recorded as
one Mac copy, not an off-machine backup; its external package was not rechecked
in this review. Hash agreement does not certify source authenticity/completeness.

Action: package one dependency-closed reviewed research slice against current
master, preserving all unrelated changes and raw archives. Establish a verified
off-machine data copy using the operator's selected destination. Do not push the
whole dirty checkout or replay the entire old series as if fully accepted.

### 6. The documented local test environment does not execute the whole suite

SHOWN: test_companion_article_body cannot collect because bs4 is missing from
the root environment; beautifulsoup4==4.12.3 is declared in the companion's
requirements. Other companion tests explicitly skip missing feedparser or
pydantic_settings. The manual audit helper also selects/usr/local/bin/git,
an x86_64-only binary, and logs Bad CPU type in executable on this ARM Mac.
Its collection subprocess fails on the missing dependency too. This is not
evidence of an application regression or of a passing release baseline.

Action: make the supported test environment reproducible with explicit native
tool selection and the declared companion test dependencies in an isolated
environment. Do not hide collection errors or automatically change the running
environment. No dependencies were installed during this audit.

## Boundaries That Remain Open

- Local config retains live_enabled=true and stored armed=true. That does not
  prove orders can currently fire; absence of running live execution is also
  UNVERIFIED. Process arming overrides, kill gates and actual venue state were
  not inspected. No live setting or private account was changed.
- Product-specific all-in Coinbase fees and maker/taker arrival/coverage contract
  remain unfinished. Do not freeze the execution study from account-tier data.
- CMC diagnostic capture is useful, but its primary market inference method and
  primary integration remain INCOMPLETE. More elapsed days alone do not fix it.
- E7-E9 reproduction preserves FAIL verdicts; sizing/cash/turnover specification
  gaps must be fixed prospectively, not rewritten in frozen registrations.
- Future January/February/April study endpoints cannot be completed today.
- The zero-wager lottery diagnostic found no demonstrated advantage; it is not
  an income alternative established by these artifacts.

## What Is Already Closed

Do not reopen the canonical stored-fill-evidence defect: the four-line correction
and two SQLite regressions independently passed52 tests and were accepted with
risk. Source SHA2561ced865c36cbf568d72a52310cb117bdfd9a3f5fe70b73e9d3025f897c518fff
is unchanged in this audit. That is not deployment or real-cost verification.

The ES endpoint report is independently accepted with risk:30 completed daily
sessions,331/331 replayed captured signals, zero orders/fills/positions and0USDT
paper trading PnL. The service stopped at the fixed endpoint. Trading efficacy
remains INCOMPLETE; no automatic extension, reset or promotion follows.

## Verification

VERIFIED_ENV: local .venv Python3.12, current files and temporary test state.
repo_doctor --strict --json passed. check_repo_alignment --json passed25 guard
tests. git diff --check passed. These are structural checks, not readiness proof.

Full-suite attempt with CBP_SKIP_SLOW=1 stopped at collection: parser test imports
bs4, absent in the root environment but declared in the companion requirements.
No tests ran in that first attempt. A continuation using the explicit
--continue-on-collection-errors option completed:4679 passed,2 failed,76 skipped,
1 collection error,35 warnings in459.05seconds. Command:

`CBP_STATE_DIR=<temporary-directory> CBP_SKIP_SLOW=1 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest tests -q -p no:cacheprovider --continue-on-collection-errors --junitxml=/private/tmp/cryptkeep_review_20261016_continued.xml`

Failure triage:

- test_environment_proxy_never_receives_companion_bearer: sandbox denied binding
  the temporary127.0.0.1 listener. The exact test passed1/1 in1.21seconds under
  approved loopback access, temporary state and a fresh PYTHONPYCACHEPREFIX.
  It uses a fixture token, not a real credential or external endpoint.
- test_manual_repo_audit_writes_required_artifacts: its generated failure file
  records git_status/git_log exit126 from the incompatible Intel Git binary,
  plus pytest_collect exit2 from the missing dependency. It was not repaired or
  rerun broadly. The helper writes audit artifacts under the repository's
  .cbp_state/audit_reports despite the temporary CBP_STATE_DIR; those artifacts
  were preserved and no trading state was deliberately changed.
- test_companion_article_body: bs4 collection error remains unresolved.

The76 skips include declared slow loops, missing optional dependencies/sources
and opt-in integration tests; not all execution/integration paths ran. No clean-
master comparison was performed, so no claim that failures equal an old baseline.
The broad result is NOT a passing full-suite or production-readiness verdict.

## Recommendation

Preserve CryptKeep as a multi-symbol research and decision-support project;
neither abandon it from scoped failures nor describe it as an income system.
The immediate delivery batch is accurate active instructions plus a working
existing intelligence/alert path and one reproducible reviewed release slice.
Those are concrete usability/integrity repairs, not a mandate for more layers.

The next economic research objective should be one bounded prospective
multi-symbol comparison, with the population, sizing, costs, cash benchmark and
missingness rules fixed before outcomes. Choose its research subset for data
feasibility and mechanism, not this history's winners. Existing failed experiments
stay failed; untested symbols remain untested until evaluated. No capital,
campaign, schedule or project-scope decision is made by this audit.

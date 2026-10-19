# Research-path repair: scoped handoff

Date: 2026-10-16. Active role: AUDITOR after scoped ENGINEER stages.
Overall operating research path: INCOMPLETE. No profitability/readiness claim.

## What Changed

1. `RESEARCH_BRIEF.md`: removed the directive to treat reused2024-26 history as
   untouched holdout; retained original D/H labels and registered verdicts as
   historical facts. Separated the25-symbol scope from the dated24-product
   Coinbase observation, E10 relative classifications from positive profit,
   account-tier fees from product fees, saved scheduling from unattended proof,
   and source/fixture proof from operating endpoint availability. Updated maker/
   taker draft-v3 and ES endpoint references; did not rerun either study.
2. `scripts/manual_repo_audit.sh`: now honors `CBP_STATE_DIR` for audit output,
   validates `GIT_BIN`, and prefers `/usr/bin/git` on Apple Silicon when no
   override is supplied. It does not rewrite global PATH, hide collection
   failures or change its existing report-only exit convention.
3. `tests/test_manual_repo_audit_paths.py`: replaced recursive full-repository
   auditing inside a unit test with temporary fixture trees/fake executables.
   Eight cases cover output location, native/explicit Git, invalid overrides,
   and retained Git/collection failures. A fixture pass is not a real broad audit.
4. `tests/test_research_source_slice.py`: added one offline two-market controls
   fixture through the existing archive runner, with frozen prefixes, carried
   cash/positions, read-only archive checks and explicit missing-market refusal.
   It changes no strategy, sizing or frozen experimental criterion.
5. `docs/review_artifacts/research_path_repair_20261016/`: preserved pre-edit
   sources, generated diffs, selected test XMLs, dependency-overlay inventory,
   an explicit39-file source allowlist/archive and SHA256 manifest. No credentials
   or real market/account database is bundled. Existing25-symbol mandate and
   coverage CSV remain byte-identical. No original result is overwritten.

## Existing Explanation Path: Diagnosis

SHOWN in current source:
`dashboard/services/views/market_view.py::get_research_explain` first requests
the configured backend `/api/v1/research/explain`, then the companion
`/v1/explain`, and otherwise returns a labeled fallback. Default ports are8000
and8002 in `_shared_http.py`. The companion orchestrator/parser/memory source
has been restored; earlier documents saying these directories are empty describe
an older checkpoint, not current source absence.

SHOWN in this check: unauthenticated curl health probes of127.0.0.1 ports8000
and8002 both returned exit7, connection refused. No listener or service was
started. This does not prove the effective environment of a running dashboard,
an external deployment, every port, or the underlying storage state.

SHOWN in local fixture tests: imported ASGI routes, auth refusal, article parsing,
question forwarding and evidence/citation construction work under the selected
test conditions. They do not run service lifespans, durable database/object/vector
integration, external inference or live news collection. No restored auth code
or credential configuration was changed in this batch.

Operational usability remains UNVERIFIED until a separately authorized startup/
reconnection of the existing backend produces a real cited query. No requirement
to build a replacement platform follows from the unavailable endpoint.

## Verification And Failure Triage

VERIFIED_ENV: Python3.12.10, local source, fixture token only, temporary state,
no plugin autoload/cache writes, fresh bytecode lookup for final proof runs.
No root `.venv` package was modified. Optional companion test dependencies were
installed only into a disposable `/private/tmp` overlay, with its resolved
versions saved. This does not certify the deployment dependency environment.

| Proof | Result | Limit |
| --- | --- | --- |
| Parser, restored ASGI routes, orchestrator/tools and pipeline adapter |42 passed,96 deprecation warnings| Fixtures, no lifespan/storage/network activation |
| Dashboard explanation/client selection, excluding listener fixture |13 passed,56 deselected| Explicitly not a new proxy-listener safety pass |
| Audit helper syntax and deterministic tool tests |8 passed; `bash -n` passed| Real broad audit not rerun |
| Existing harness plus new two-market controls fixture |33 passed| Synthetic source/accounting proof only |
| Same39-file source archive extracted to an empty directory |33 passed;39 hashes matched| Existing interpreter, no original source PYTHONPATH |
| Final V3 in a clean pytest-only Python3.12 venv |33 passed;39 hashes matched; exact archive membership| No root site-packages or original source PYTHONPATH |
|25-symbol registry regressions |4 passed| Coverage consistency, not trading eligibility |
| Existing trial-ledger manifests |6 files matched| Identity, not exhaustive count accuracy |
| `/usr/bin/git --version` |Apple Git2.39.2 works| No remote/publish operation |
| `git diff --check` |passed| Whitespace only |

Commands and selected outputs are recorded in the artifact README and XMLs.
The prior broad run remains **4,679 passed,2 failed,76 skipped,1 collection error**.
There was no new full-suite run; do not subtract targeted passes from that result
and declare it green.

- **Collection error:** `bs4` is absent in root `.venv`, already declared in
  companion requirements. Its six article-body tests now collect/pass in the
  disposable overlay. Root behavior is deliberately not silently altered.
- **Manual-audit failure:** incompatible PATH Git and recursive test-wide
  collection were environment/workflow defects. Source tool selection and test
  isolation are repaired; eight controlled cases pass, including failed
  collection reporting. A real full-repo quick audit was not rerun.
- **Proxy test failure:** sandbox loopback bind denial reproduced. An attempted
  absolute-node exclusion did not match, so its13-pass/1-fail receipt is kept.
  The corrected keyword selection deliberately excludes this one case. Prior
  separately authorized out-of-sandbox1/1 proof remains historical; no listener
  was started successfully and no new operational authorization was inferred.

Initial fixture/dependency-layout failures are also retained in the artifact
README. No failed receipt is relabeled as a pass.

Independent review caught24 additional AppleDouble metadata files in the first
archive and remaining broad table/E7-summary wording. The final brief now scopes
those claims and correctly reports E7's unchanged D drawdown versus modest H
improvement without altering FAIL. `source_slice_v3.tar.gz` is the current package;
the two earlier archives remain superseded history. Final V3 has exactly39
allowlisted regular members, no extra metadata or links, and matches its separate
`source_slice_v3_SHA256SUMS`. The original source manifest is not silently reused
for the corrected brief. New-venv pip DNS failure was worked around with locally
downloaded public wheels and an offline install; no authentication action.

## Review And Next Boundary

The tool correction was implemented by a separate bounded worker and checked by
the parent with the eight tests and diff inspection. The brief and synthetic
fixture/source package were separately reviewed. After the named metadata and
brief corrections, the auditor confirmed **ACCEPTED_WITH_RISK** for the bounded
docs/fixture/V3 source package, including the corrected V3 verification command.
It independently reproduced the initial33 extracted tests and checked final
V3 membership/hashes and the saved clean33-test receipt. No full-series,
operational, financial-efficacy or deployment acceptance is inferred.

The package reproduces the current **independent per-symbol/arm** archive runner,
not a shared-cash allocation engine. It preserves the historical three-preset,
five-market contract but uses only generated candles in this verification. It
does not run that contract on historical market data, introduce an experiment
or expand the25-symbol mandate.

Step5 is intentionally not started: a new prospective comparison should be
proposed only after the existing operating research path is usable and its
universe, missing-data/status rules, carry-forward sizing/cash, fees, benchmarks
and evaluation criteria are fixed. Historical outcomes already viewed do not
become untouched by changing the harness or author.

Any next operational proposal must name the existing backend target, exact
startup/reconnection scope, dependency/volume handling, query proof and rollback,
then obtain separate authorization. This handoff authorizes no Docker use,
service/server change, account or credential access, schedule change, trading,
new experiment, merge, commit or push.

# Treatment-only candidate handoff

Active role: ENGINEER. Risk HIGH (financial accounting and concurrency).
Acceptance: READY_FOR_INDEPENDENT_REVIEW. Not publication or deployment approval.

## Candidate

Base: 620bc8dbeee71cca327042902759e219e18f30b6.
Patch: docs/review_artifacts/treatment_candidate_20261007/treatment.patch.
Manifest records all ten source/test SHA256 identities and patch SHA256.
Builder: docs/review_artifacts/build_treatment_candidate.py.

Candidate contains only durable reconciler delivery, symbol-loss exactly-once
cutover, execution-average/quantity evidence protections, compatibility tests,
and optional research-root recognition. Unrelated strategy, feedback, governance,
research and campaign changes are not included. Original Git index untouched.
This handoff supplies operator limitations; prior mixed documentation changes
were deliberately not imported wholesale into the source patch.

## Shown proof

- All ten selected files match the recorded green working-snapshot inventory.
- Disposable candidate assembled from Git archive of the stated base, then
  only those ten files overlaid. No original worktree changes or staging.
- Candidate git diff --check and reverse patch applicability check pass.
- Seven-file targeted slice: 66 passed, 16 existing datetime warnings, 1.58s.
  JUnit preserved alongside patch. VERIFIED_ENV: sandbox denies network and
  operator-home contents/writes except dependency reads; clean environment,
  null keyring, disposable SQLite/state. No real exchange or account invoked.

The earlier 3,889-pass full suite includes unrelated working changes and is
NOT a full-suite result on this candidate. Candidate CI/full suite not run.

## Review required

Independently inspect atomic fill/outbox persistence, durable completion,
counter marker transaction, cutover preservation, terminal-status refusal on
missing evidence, and competing real/synthetic quantity bounds. Verify tests
cover failure/retry/restart without accepting synthetic source assumptions as
venue proof. Check candidate independently of unrelated working changes.

## Release constraints

Preserve historical counters; no bulk replay or historical restatement.
Stop old accounting writers before an explicitly authorized cutover deployment.
Missing partial VWAP/fees, untracked historical fills, other execution callers,
real exchange concurrency and power-loss remain outside demonstrated coverage.
Human acceptance of earlier bounded changes remains recorded, but this new
publication candidate is not independently accepted or deployed.
No push, merge, config/account/credential/cohort/process/order changes occurred.

Next: independent review of this exact patch, then isolated full-suite/CI on
the exact candidate before a release decision. Do not silently include unrelated
work or use a passing local slice as live authorization.

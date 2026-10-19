# Treatment release checkpoint - 2026-10-07

Active role: AUDITOR. Acceptance: INCOMPLETE for release.

## Shown

- Current HEAD is 620bc8dbeee71cca327042902759e219e18f30b6, with substantial
  tracked and untracked working changes. Publication must not silently include
  unrelated work. Tested working-source identity is captured in the isolated
  suite inventory, not represented by HEAD alone.
- The completed isolated suite has 3,889 passed, 38 skipped, zero failures.
  See research_layout_treatment_20261007.md and the preserved inventory/JUnit.
- A fresh read-only GitHub API query returned three completed failed runs:
  37589712825, 37434813186 and 37279885984, all on
  97c24c8e4884629347a5492ae848133becd9027b. These are not treatment CI proof.
- Latest run 37589712825 failed its macOS and Windows nightly build steps.
  Failure causes were not inspected; no treatment regression is inferred.
- Current .github/workflows/ci.yml uses Python 3.11 and CBP_SKIP_SLOW=1.
  Its core lane is not equivalent to the unskipped isolated local suite.

## Next bounded release action

Prepare an exact treatment-only publication candidate from the tested inventory,
preserving unrelated changes. Verify its source identity and patch applicability,
then obtain review/release authorization before publishing it. Run CI on that
exact published candidate; do not attribute historical build failures to it.
Do not broaden this into nightly packaging repair without causal evidence.

Before deployment, verify target-host access and loaded source, stop old
accounting writers under explicit operational authorization, and preserve the
approved historical cutover contract. Neither a local pass nor CI authorizes
database migration, collector restart, live arming or historical replay.

## Boundaries

VERIFIED_ENV: local inspection and fresh read-only GitHub API access.
Initial local CLI/path and sandbox-network failures were not credential failures;
the read query succeeded outside the sandbox with the system Git search path.
No login or credential mutation was required.
Remote-host/runtime source, candidate CI, optional companion integration and
economic value remain UNVERIFIED. No tests were rerun at this checkpoint.
No financial source, configuration, account, process, order, push, merge or
deployment changed. This document is a release prerequisite record, not approval.

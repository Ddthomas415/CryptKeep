# GitHub Branch Protection

`master` must be protected in GitHub settings. These settings are not stored in
the repository, so this file is the source-of-truth runbook for configuring and
auditing the external control.

## Required `master` Settings

- Require a pull request before merging.
- Require status checks to pass before merging.
- Require branches to be up to date before merging.
- Block force pushes.
- Block branch deletion.
- Do not require linear history while this repository intentionally uses merge
  commits for audited integration PRs.

## Required Status Checks

Require only checks that run on every pull request:

- `CI validate`
- `CI sanity`
- `Governance smoke`
- `Build (macos-latest)`
- `Build (windows-latest)`
- `GitGuardian Security Checks`

Do not globally require `script-path-integrity`; that workflow is path-filtered
and only runs when scripts, the `Makefile`, or its workflow file change.

## Audit Context

PR #45 proved the gap: GitHub allowed `master` to advance while the main
`validate` workflow was still pending. The check later passed, but the merge
ordering showed that `master` had no enforced protection at that time.

Workflow check names are intentionally explicit so branch protection can require
the main CI jobs without ambiguity.

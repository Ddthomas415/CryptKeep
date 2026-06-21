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
- Allow administrator bypass in the GitHub rule for the repo owner/admin.
  This is intentional for this solo-project workflow: the review requirement is
  meant to prevent AI agents and non-admins from self-merging, not to require a
  second human reviewer when none exists.
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

`CI validate`, `CI sanity`, and the PyInstaller build checks keep stable check
names on every pull request, but may internally fast-pass docs-only changes.
Do not replace this with workflow-level path filters for required checks;
GitHub can leave skipped required workflows in an expected/pending state.

## Audit Context

PR #45 proved the gap: GitHub allowed `master` to advance while the main
`validate` workflow was still pending. The check later passed, but the merge
ordering showed that `master` had no enforced protection at that time.

Workflow check names are intentionally explicit so branch protection can require
the main CI jobs without ambiguity.

## Admin Bypass Policy

Admin bypass is allowed only through the visible GitHub UI/admin path after the
audit cycle has completed and the human operator accepts the work. Do not use
CLI admin-bypass flags from an AI-agent workflow.

Human acceptance in chat is review evidence; it is not, by itself,
authorization for an AI agent to run `gh pr merge --admin`. If a pull request is
blocked only by the owner-self-review rule, the AI agent should stop and direct
the human repo admin to complete the visible GitHub UI bypass.

When admin bypass is used, record an audit note on the PR explaining:
- why normal review could not satisfy the rule, such as owner-authored PRs in a
  solo project
- that required checks were passing before merge
- that the bypass was performed by the human repo admin, not an AI agent

If the project adds a second human reviewer, consider tightening the rule by
enabling "Do not allow bypassing the above settings" and requiring external
review even for administrators.

## Post-Merge Branch Alignment

After a human-admin merge from `review-stabilized` to `master`, keep
`review-stabilized` aligned with `master` before starting the next change.
GitHub may create a new merge commit on `master` even when the file tree is
identical to the PR head. That leaves the two branch names pointing at different
commits with the same content, which creates recurring navigation noise.

Use this alignment only when all of the following are true:

- PR checks passed before merge.
- The PR is already merged to `master`.
- `git diff --name-status origin/master..origin/review-stabilized` is empty.
- `git rev-parse origin/master^{tree} origin/review-stabilized^{tree}` reports
  the same tree hash for both refs.

Safe alignment procedure:

```bash
git fetch origin master review-stabilized
git diff --name-status origin/master..origin/review-stabilized
git rev-parse origin/master^{tree} origin/review-stabilized^{tree}
git rebase origin/master
git push --force-with-lease origin review-stabilized
git rev-parse HEAD origin/master origin/review-stabilized
```

Do not use this procedure if there are file differences between `master` and
`review-stabilized`. In that case, stop and open a normal PR or ask for a human
branch decision.

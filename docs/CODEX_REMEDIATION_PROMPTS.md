# Codex Remediation Prompts

This file records corrective operating prompts for repeated workflow failures.
Use it before starting new repo work when the same failure pattern appears.

## GitHub Auth And Publishing

### Failure Pattern

Codex repeatedly misclassified GitHub publishing failures by treating sandbox
network errors, `gh auth status` output, and git credential-helper state as the
same problem.

Observed bad outcomes:

- Repeated browser-login prompts.
- Claims that auth was fixed before proving the durable state.
- Treating sandbox DNS failures as token failures.
- Treating a successful push as proof that all `gh` status paths were clean.
- Waiting or asking instead of switching to a verified publish path.

### Corrective Rule

Before asking the operator to authenticate again, Codex must separate four
states:

1. **GitHub API auth:** `gh api user --jq '.login'`.
2. **Git credential helper:** `git config --show-origin --get-regexp 'credential.*helper'`.
3. **Remote git capability:** `git ls-remote --heads origin <branch>`.
4. **PR API capability:** `gh pr view <number> --json number,url,state`.

If a command fails inside the sandbox with DNS or network errors, rerun the
same non-mutating check outside the sandbox before calling it an auth failure.

Do not call GitHub auth "permanently resolved" unless all relevant checks pass
in the execution context that will be used for publishing.

### Corrective Prompt

Use this prompt when GitHub auth or publishing breaks:

```text
Active role: ENGINEER.

Do not ask for browser login yet. First classify the failure:

1. Run `gh api user --jq '.login'` outside sandbox if network is restricted.
2. Run `gh auth status` outside sandbox and treat sandbox-only DNS failures as
   inconclusive, not invalid credentials.
3. Inspect git credential helpers with
   `git config --show-origin --get-regexp 'credential.*helper'`.
4. Verify remote branch read capability with
   `git ls-remote --heads origin <branch>` outside sandbox if needed.
5. If push works, create the PR and report the PR URL.
6. If the token is truly invalid, state the exact failing command and stop at
   the smallest required auth action. Do not loop auth flows.

Do not say "fixed" unless push or PR creation has been proven. If only helper
wiring was changed, say "helper wiring changed; token validity still requires
verification."
```

## CI And Next-Work Flow

### Failure Pattern

Codex repeatedly waited on CI or turned CI status into a blocker when the
operator wanted continued progress.

### Corrective Rule

After opening a PR, check CI once. If checks are pending and the user has not
asked to wait, move to the next safe local task that does not modify the same
branch or conflict with the pending PR.

### Corrective Prompt

```text
Active role: ENGINEER.

Check PR CI once. If pending, record the pending checks and continue with the
next safe, non-overlapping backlog task. Do not idle on CI unless the operator
explicitly asks to wait or merge.
```

## Repeated Backlog Findings

### Failure Pattern

Codex repeated old findings as new work, creating the appearance of invented
problems and slowing forward progress.

### Corrective Rule

Before adding a backlog item or presenting a finding, check current repo docs
and the visible work log for prior resolution.

Minimum checks:

- `REMAINING_TASKS.md`
- `docs/ROADMAP_TRACKING_CHECKLIST.md`
- `docs/work_log/review_stabilized_work_log.md`
- Any directly relevant decision record or runbook.

### Corrective Prompt

```text
Active role: AUDITOR or ENGINEER as appropriate.

Before naming a problem as open, search the backlog and work log for the same
surface and exact failure mode. Classify it as:

- already fixed,
- fixed with residual follow-up,
- still open,
- or unclear with the missing evidence named.

Do not restate a fixed issue as a new blocker.
```


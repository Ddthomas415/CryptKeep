# Codex Remediation Prompts

This file records corrective operating prompts for repeated workflow failures.
Use it before starting new repo work when the same failure pattern appears.

## Scope Impact Checkpoint

Operator-selected interaction, 2026-09-29: "Show the impact and recommendation;
get my decision before changing scope. Routine fixes continue."

### When to interact

Before removing, disabling, archiving, untracking, or materially narrowing an
agreed capability, present the checkpoint below. This includes making a required
capability optional or indefinitely deferring it. Do not disguise scope reduction
as cleanup. A defect in an implementation is not evidence to abandon its purpose.

Routine fixes, tests, and research within accepted scope continue without another
scope approval. Existing security, review, deployment, and trading authorizations
remain applicable. Already-authorized emergency protections remain applicable;
record any resulting capability loss rather than silently treating it as retirement.

### Interaction

Use one short message, then one focused question:

```text
Objective: [accepted user outcome and source]
Proposed change: [specific change]
Capability impact: [what remains, stops, or becomes optional]
Evidence: [SHOWN facts; UNVERIFIED claims explicitly separated]
Recommendation: [repair / isolate / replace / retire, and why]
Alternative and recovery: [preservation option and rollback where meaningful]
Decision needed: [explicit scope choice, not a generic request to continue]
```

Offer preservation/repair, the recommended change, and defer where meaningful.
Do not preselect an answer as authorization. Silence or an unrelated "continue"
does not authorize a scope reduction. If the answer is ambiguous, clarify only
the affected change and continue useful non-conflicting work.

The operator may say **show the impact** at any time. Pause the disputed change,
show its scope and evidence, and leave unrelated authorized work moving.

### Durable record and handoff

Use the existing docs/work_log/review_stabilized_work_log.md, not a second ledger.
Record a dated decision ID, objective/source, proposal, affected capabilities,
evidence, alternatives, the user's actual decision and scope, verification,
remaining limitations, and any superseded decision ID. Never fabricate a quote.
If the decision changes the project direction, update docs/PROJECT_DIRECTIONAL_PLAN.md
in the same branch. Preserve historical entries rather than rewriting approvals.

Before implementation, check the latest relevant decision and current Git diff.
Approval covers only its recorded scope; materially changed proposals need a new
decision. Do not reopen resolved issues without new contradictory evidence.
Handoff distinguishes implemented, locally tested, deployed, operating, and
economically validated; none implies the next. These are evidence dimensions,
not replacements for AGENTS.md acceptance states.

Documentation tests preserve this checkpoint's presence, not agent compliance
or operating capability. No claim of permanent prevention follows from them.

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

Never call authentication permanently resolved. Report the verified operation,
host/context and time. Persistence requires a fresh-process or later-session
check; even that cannot guarantee future token validity or network availability.
Do not publish merely to test authentication. Read checks establish read access,
not write capability; publishing requires the user's applicable authorization.

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
5. If publishing is authorized, use the verified path and report the actual
   push/PR result. Otherwise stop at read-only diagnostics; do not test by writing.
6. If the token is truly invalid, state the exact failing command and stop at
   the smallest required auth action. Do not loop auth flows.

State exactly what was verified. A successful push does not prove PR API access
or persistence across sessions. If only helper wiring changed, say "helper wiring
changed; token validity still requires verification."
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

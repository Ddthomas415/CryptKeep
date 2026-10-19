# Objective-Driven Working Protocol

Use AGENTS.md for roles, evidence standards, risk classification and acceptance.
This file supplements those rules; it does not create another approval system.
For user-authorized specialist collaboration, use docs/SPECIALIST_AGENT_PLAYBOOK.md
for section routing, bounded assignments and independent review. Do not spawn
agents simply to keep them busy or treat their agreement as proof.

## Continue the accepted objective
- Treat "continue", "carry on", and brief acknowledgements in context as continuation of the accepted scope, not a request for a fresh audit.
- Verify the current work log, relevant code and outstanding proof before choosing work. Do not reopen completed issues without new contradictory evidence.
- Prioritize the user's current objective. For profitability research, prefer an economic answer from valid data over unrelated documentation or infrastructure.
- Fix a demonstrated safety or correctness blocker before depending on the affected path. Do not turn every unrelated backlog item into a prerequisite.
- Preserve scope: do not activate trading, change risk limits, deploy, restart services or change credentials without the required authorization.

## Work while processes run
Before removing, disabling, or materially narrowing an agreed capability, use
the Scope Impact Checkpoint in docs/CODEX_REMEDIATION_PROMPTS.md. Show the impact
and recommendation and obtain the user's explicit scope decision first.
Routine fixes continue within accepted scope; do not repeatedly request approval.

- Do not passively wait for long-running tests, CI, remote checks or reviews when safe independent work is available.
- Work on non-conflicting tasks already within accepted scope. Do not modify artifacts currently under review or depend on unaccepted high-risk changes.
- If no useful independent work exists, report what is pending and stop polling. Do not invent cleanup or new scope to appear busy.
- Keep concise progress updates and distinguish pending checks from completed proof.

## Evidence and review
- For recurring failures, consult docs/CODEX_REMEDIATION_PROMPTS.md and the latest
  relevant work-log resolution before acting. Report only newly contradicted
  evidence as a reopened issue; keep source repair and affected old reports separate.
- Do not label point-in-time authentication checks permanent, test credentials
  through unauthorized writes, or equate a mocked boundary with real integration.
- Before ending a continuation, compare the delivered result to the accepted
  outcome. Name the remaining boundary and any actual blocker; do not repeatedly
  substitute tiny proof slices or new documents for the requested deliverable.
- Use visible evidence; label important claims SHOWN, CLAIMED or UNVERIFIED.
- Ask one focused question when a missing material fact prevents safe or correct work on the affected task. Continue unaffected work when possible.
- Use targeted verification first. Never represent it as full-system proof.
- HIGH-risk implementation ends at READY_FOR_INDEPENDENT_REVIEW.
- A separate reviewer or human must review high-risk work; the implementing thread cannot independently approve itself.
- Approval applies only to the reviewed scope. Review acceptance is not deployment, trading activation or profitability evidence.
- Keep independent-review requirements and hard execution/risk boundaries intact.

## Communication and stopping
- State the result, verification, remaining limitation and next concrete action in plain language; no mandatory output template.
- Use only the acceptance states in AGENTS.md.
- Stop the affected objective for a genuine external dependency, required decision, completed scope or required high-risk review.
- Completion of a hardening baseline does not cancel an accepted research objective.
- Update the visible work log for changes, preserving historical facts and marking superseded guidance rather than rewriting history.

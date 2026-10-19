# Claims reconciliation - 2026-10-01

AUDITOR. User objective: recheck past claims and work, not add features.

## Coverage and limits

Current tracked inventory command `git ls-files docs '*.md' | wc -l` returned
364 paths (mixed documentation inventory, not 364 reviewed claims). Visible
work log is 42,044 lines at inspection. This first pass covers the recent impact
review, recovery tests, workflow corrections, PR602/603 and ETH research report.
It is NOT an exhaustive review of all commits, agent conversations, attachments,
GitHub comments, deleted branches, historical artifacts or deployed state.
Git authorship alone cannot establish which agent authored or authorized a claim.

## Claim ledger

## Recurrence audit extension - 2026-10-01

User scope is ALL recorded recurring failures, not only auth, waiting and
reopened findings. This extension inspected the complete remediation prompts,
mistakes-impact review, this reconciliation, runtime protocol and recent work-log
entries. Historical GitHub discussions, all 42k+ work-log lines, attachments and
all deployments have NOT been exhaustively reviewed. Older PR states below are
dated observations, not refreshed remote status.

| Behavior family | Current evidence and treatment |
|---|---|
| Auth misclassification and durability claims | SHOWN: remediation allowed permanent-resolution wording after checks. Removed; require operation/context/time and distinguish later-session persistence. No credentials changed. |
| Unauthorized mutation during diagnosis | SHOWN: auth prompt said push/create PR without explicit authorization check. Corrected to read-only diagnostics unless publishing authorized. |
| Passive waiting / repeated partial handoffs | SHOWN: recent log records multiple small recovery slices while full pipeline stays incomplete. Individual tests are useful, but no end-to-end delivery follows. Require outcome comparison at handoff; do not invent busywork. Actual elapsed idle time not measured. |
| Reopening resolved defects | Published fixes in the impact review remain closed at source level; host uptake and historical affected reports are distinct residuals. No new contradictory source evidence in this pass. |
| Scope drift / capability removal | Original-direction and scope-impact records remain controlling. No new capability retirement authorized by this audit. |
| Overstated test/integration evidence | SHOWN: earlier fixed search stub and dictionary-only feed tests missed real boundary behavior. Stateful index, real local persistence and actual feed parser added; networked pipeline still unproven. |
| Approval and review confusion | SHOWN: human approval preceded later teardown findings. Work log now distinguishes original approval, changed test and re-review. Approval never implies activation. |
| Process cleanup / safety | SHOWN: reviewer found startup/close cleanup gaps; corrected and bounded review accepted. Stop/status failure handling is still not exhaustively tested. |
| Profitability / accounting / budget claims | Keep actual vs modeled, gross vs net, initial capital vs monthly contributions distinct. Prior report-impact tracing remains incomplete; this audit creates no profit evidence. |
| Publication / reproducibility | Existing local artifact and publication distinctions remain; no fresh remote-state verification in this pass. Do not label local files delivered remotely. |
| Agent expertise / enforcement claims | Specialist playbooks are instructions, not training or guaranteed compliance. Text guards protect wording only; separate reviews have caught actual defects. |
| Missing proactive information | Handoffs must disclose limitations, changed evidence and remaining outcome before another generic continuation. No evidence of exhaustive historical disclosure review yet. |

This is a coverage inventory and correction record, not a claim that every
recurrence is prevented. Next audit work: trace unresolved historical findings
to affected artifacts/decisions, rather than reopen repaired code or add another
general architecture plan. Overall audit INCOMPLETE.

## Earlier claim ledger

| Claim or implication | Evidence and current disposition | Consequence |
|---|---|---|
| Net-win correction is unpublished | STALE in September 30 impact review; GitHub #603 now merged at 97c24c8e4. Added dated supersession. | Do not repeat it as an unresolved implementation defect. Host deployment still unverified. |
| Local replay suite success establishes CI readiness | NOT ESTABLISHED. Python3.12 local 3813-pass record versus Python3.11 CI code-mismatch failure; #602 remains open. | No merge-readiness or crossover activation claim. |
| Recovered news pipeline works end to end | UNVERIFIED, promised deliverable incomplete. Tests compile selected function bodies with substitutes; models imported separately. Parser/storage/retrieval not exercised together. | Nine unit tests must not imply persistence, semantic retrieval or operational awareness. |
| Event awareness is a new requirement | CONTRADICTED by original directional-plan commit 92f754e8f and historical companion source. | Recovery must preserve original purpose; avoid duplicate architecture. |
| More intelligence features caused crashes | UNSUPPORTED in inspected records; companion removal described as orphan cleanup, not demonstrated crash causality. | No technical justification for removing capability follows. |
| All historical defects are still open | CONTRADICTED by published signal-quality corrections and #601/#603. | Reopen only exact residuals supported by new evidence. |
| ETH result is live profit or independent holdout | CONTRADICTED by es_eth_transfer_20260929.md at research commit b44b85902: CF-MODELLED, reused dates, assumed costs, concentrated returns. | Not evidence to increase capital or activate trading. |
| A 1,000USDT initial simulation matches a 1,000-dollar monthly budget | UNVERIFIED equivalence; report uses initial cash and no monthly cash-flow model. | Scenario is not a personal funding plan or monthly-income forecast. |
| Research artifact package is fully published/reproducible remotely | NOT ESTABLISHED: research worktree has untracked results/ referenced by reports. | Local evidence must be packaged or made available before remote reproduction claims. |
| Interaction policy prevents all future drift | UNVERIFIED; docs/tests only preserve text, not agent compliance. | Actual scope decisions and follow-through remain necessary. |

## Priority treatment

First resolve #602 code-identity discrepancy without weakening verification.
Separately keep the unfinished news integration proof explicitly open. The
historical audit still needs affected-report/decision tracing, not just source
fix confirmation. No new trading hypotheses, campaign resets or blanket pause
are authorized by this reconciliation. No profitability finding is upgraded.

Verification in this pass: GitHub PR state reads, code/test inspection, research
report and worktree status. No tests rerun; prior results above are historical
records, not new proof. State INCOMPLETE for the overall requested audit.

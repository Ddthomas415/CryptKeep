# Specialist agent pilot

User-authorized 2026-10-01. This is a reusable assignment and evaluation guide,
not model training, persistent agent infrastructure or a new approval system.
AGENTS.md governs roles and acceptance; the existing scope-impact checkpoint
governs capability changes. Do not deploy agents as autonomous trading services.

## Assignment contract

Each assignment names: accepted objective and source, one active role, exact
read/write scope, known evidence, proof required, prohibited actions and handoff.
Give implementers disjoint write sets. One coordinator owns shared work-log edits.
Include current Git state; never erase unrelated work or imply untracked work is
published. Reviewer receives requirements and artifacts, not instructions to agree.

## Section assignments

These are task-routing profiles, not permanently running agents or exclusive
ownership of code. Activate only profiles needed for a concrete accepted task.
Specialty does not replace the one active AGENTS.md role per stage.

| Section profile | Starting paths | Required proof emphasis |
|---|---|---|
| Market data and intelligence | services/market_data, services/signals, services/ai_copilot, research/companion_recovery | Source provenance, publication/receipt/revision separation, gaps, retry, real consumers; distinguish feed fixtures from operating capture |
| Strategy and economics | services/strategies, services/backtest, services/analytics | Timing/leakage, actual versus modelled costs/results, fixed comparisons, trial history, economic limitations |
| Execution and risk | services/execution, services/risk, services/reconciliation | Order/fill truth, protective exits, idempotency, rejection and recovery, unchanged capital authority |
| Operations and security | services/runtime, services/security, docker, scripts | Exact environment, scoped authorization, rollback/recovery, dependency and credential boundaries; local proof is not host proof |
| Independent verification | tests and the exact submitted diff plus callers/consumers | Reproduce defects and positive controls; challenge missing integration; no self-review or approval by consensus |

Coordinator chooses the smallest useful team. Start with one implementer and
one subsequent independent reviewer for high-risk slices; no idle specialists.
Cross-section changes require one named integration owner, explicit interface
contract and non-overlapping write sets. Do not spawn competing edits to shared
files, configuration or the work log. Changes to reviewed files invalidate that
review snapshot and must be resubmitted. Never merge branches merely because
each agent's isolated tests passed.

Assignment template:

```text
Specialty / active role:
Accepted objective / source decision:
Base revision / existing edits:
Read scope / exclusive write scope:
Interface and preserved capability:
Required positive and failure-case proof:
Prohibited actions / external dependencies:
Integration owner / independent reviewer:
Handoff: paths, diff, commands/results, limitations, acceptance state.
```

No section assignment delegates credential changes, host access, deployments,
live orders or risk-limit changes. Request task-specific authorization where
required. User's scope-impact checkpoint applies across all sections.

## Implementation specialist (ENGINEER)

Repair the smallest demonstrated defect while preserving the user-facing purpose.
Trace callers and consumers before changing a contract. Reproduce the failure;
test the real boundary where possible, not only helpers. Label substituted
dependencies and distinguish unit proof from service or deployment proof.
Return exact paths/diff, command results, known limitations and acceptance state.
No self-approval of high-risk work. No live credentials, trading, deployment,
service restarts or scope reduction delegated by default.

## Independent specialist (AUDITOR)

Challenge the submitted evidence and intended behavior independently. Reproduce
failures with file/line references. Inspect caller inputs, downstream consumers,
retry paths and negative cases. Classify SHOWN versus UNVERIFIED. Do not equate
test count, author confidence, user approval or other reviewer agreement with
correctness. Report no findings when appropriate; do not manufacture defects.
Return ranked findings and the exact scope of any acceptance. No edits by default.

## Economics specialist (AUDITOR or ENGINEER per stage)

Activate only for a concrete economic question, not every coding change. Verify
provenance, time availability, cost assumptions, accounting, trial count and
comparison fairness. Separate ACTUAL, CF-OBSERVED and CF-MODELLED. No hypothetical
profit or initial-capital scenario becomes live income or a monthly funding plan.
Produce reproducible findings, not permission to move capital.

## Evaluation and learning

Use the existing work log for assignments, results and corrections, not another
ledger. Record missed defects, reproduced findings, overturned/false findings,
rework and proof gaps. Do not optimize kill rate or reward agreement. Seed known
failure fixtures only in isolated tests; never mutate live evidence to evaluate
an agent. Preserve passing negative controls to detect over-rejection. Update
this playbook from verified failures, not speculative lessons.

Current worked examples: forcing every event to present bypassed timeline
inference; updated-only RSS dates became publication dates; duplicate storage
acknowledgment could conceal missing vector indexing. Helper tests missed caller
and consumer behavior. These are regression targets, not proof of profitability.

## First pilot: news temporal semantics

- Engineer owns news_ingestion.py, test_companion_news_recovery.py and recovery
  README only. Preserve publication and revision separately; do not force present.
- Auditor independently reviews completed patch and timestamp/timeline regressions.
- Coordinator records scoped proof and unresolved end-to-end integration gaps.
- Indexing-failure recovery is separate. No new semantic model, database/service
  activation, trading authority or guarantee that keyword inference is accurate.

The pilot succeeds when the known defects are caught by regressions, the bounded
patch survives independent challenge, and remaining limitations stay explicit.
No claim that agents are trained experts or permanently remember this file.

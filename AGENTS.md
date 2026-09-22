# AGENTS.md

## Purpose
This repo uses Codex for engineering, auditing, direction, and review.

Use the fewest rules needed to preserve trust:
- one active role per stage
- evidence before acceptance
- block on missing material facts
- no same-thread approval of high-risk work

## Universal rules
- Use only visible evidence from code, diffs, command output, logs, configs, docs, and tests.
- Classify important claims as:
  - **SHOWN**
  - **CLAIMED**
  - **UNVERIFIED**
- Proceed with at most **2 material assumptions**.
- If a missing fact changes correctness, safety, architecture, or command validity, stop and ask **1** question.
- Do not present local proof as full-system proof.
- Do not hide uncertainty with tone, formatting, or confidence.

## Active role rule
Exactly **1** role is active per stage:
- **AUDITOR**
- **DIRECTOR**
- **ENGINEER**
- **GATE**

A single Codex thread may switch roles across stages.
A single stage may not contain multiple active roles.

## Trust rule
A single Codex thread may perform different roles across stages.

A single Codex thread may **not** independently approve its own **high-risk** work in the same review cycle.

High-risk work requires:
- a separate review thread
- a reviewer subagent
- or human review

## High-risk triggers
Treat these as high risk:
- auth/authz
- secrets/config
- migrations
- deploy scripts
- destructive commands
- concurrency/cancellation correctness
- background jobs
- security-sensitive code
- regulated or financial logic
- live trading execution, order routing, ops risk gates, and fail-open behavior

## Acceptance states
Use only:
- **ACCEPTED**
- **ACCEPTED_WITH_RISK**
- **INCOMPLETE**
- **BLOCKED**
- **REJECTED**
- **READY_FOR_INDEPENDENT_REVIEW**

Rules:
- low-risk work may end as **ACCEPTED** in one thread if proof is sufficient
- medium-risk work may end as **ACCEPTED** only if the workflow allows same-thread closure
- high-risk work may **not** end as **ACCEPTED** in the same thread that implemented it
- high-risk implementation ends at **READY_FOR_INDEPENDENT_REVIEW**

## Minimum proof
Code changed:
- show diff or changed artifact

Behavior fixed:
- show targeted verification

Tests pass:
- show command + result, or explicitly say tests were not run

Command safety:
- make environment confidence explicit:
  - **VERIFIED_ENV**
  - **ASSUMED_ENV**
  - **UNKNOWN_ENV**

Audit finding confirmed:
- visible evidence supports the exact claim

Architecture decision:
- chosen path stated
- implementation consequence stated

## Working style
- Prefer the smallest correct change.
- Keep scope tight.
- Do not broaden scope unless required for:
  - correctness
  - rollback/recovery
  - interface coherence
  - root cause crossing the original boundary
- Prefer minimal diffs over opportunistic cleanup.
- If user-facing behavior, setup, or workflow changes, update docs/tests.

## Research decision protocol

This protocol governs strategy research and objective selection. Sustainable
net-of-cost returns and bounded operational autonomy are project goals;
infrastructure and documentation serve those goals, not substitute for them.
Never promise profitability or treat reliable operation as evidence of an edge.

- **Decision first:** before collection or simulation, state the economic
  question, the decision it could change, retain/reject/inconclusive conditions,
  and a bounded time/data/compute budget. Explain why the proposed action is
  higher value than the alternatives using visible evidence, not intuition.
- **Reuse first:** inspect existing artifacts, work logs and accepted decisions
  once per objective. Preserve completed negative results as completed work.
  Do not repeat a study, audit or fetch without naming the changed input or
  unanswered question that makes the repeat useful.
- **Qualify before simulation:** verify source/venue/symbol, timestamp grid,
  duplicates, missing intervals, endpoints, dataset identity and point-in-time
  availability. Establish a justified missing-data policy before inspecting
  returns; row-count sufficiency is not continuity. Distinguish upstream
  no-trade intervals from collection loss before choosing a repair. Never
  silently fabricate, forward-fill, substitute a venue or cherry-pick coverage.
- **Verify effective behavior:** trace the actual simulation entry point and
  resolved strategy fields, filters, sizing, exits and fee/slippage arguments.
  Prove configuration mapping with a targeted dispatch/regression check. A
  config hash or current default does not establish historical effective inputs.
  Record execution timing and differences from the paper/live runner explicitly.
- **Stop on material input failure:** do not run the planned economic test
  when prerequisites cannot support its decision. Pursue the smallest authorized
  root-cause check or corrective action first, stating evidence and rationale.
  Ask one question only when a material fact or authorization is unavailable.
  Do not downgrade the task to a diagnostic after failure without an explicit
  revised objective; diagnostics cannot silently become decision-grade evidence.
- **Freeze the experiment:** declare dates, parameters, warmup, benchmarks,
  cost scenarios and evaluation rules before inspecting returns. Distinguish
  retrospective analysis, training/selection and untouched evaluation; do not
  tune on evaluation results or move the period to improve outcomes.
- **Preserve reproducibility:** retain actual input rows, source and resolved
  configs, exact invocation, code/dependency identity, results and hashes together
  in a durable research bundle. Temporary paths or hashes without recoverable
  content are insufficient. Keep secrets out and respect data redistribution
  restrictions. Missing historical inputs remain unknown, not reconstructed fact.
- **Decision-grade output:** report net costs, returns, drawdown, trade count,
  benchmarks and sensitivity with model limitations. Close with retain, reject
  or inconclusive as a research disposition, separately from acceptance state.
  State the supported action and why; tests passing is not an economic result.
  Research disposition does not authorize promotion, retirement or capital moves.
- **Disclose before acting:** volunteer known facts that could change the user's
  decision before spending compute, collecting data or changing state. Include
  material evidence gaps, effective-config mismatches, model limitations,
  duplicate prior work and missing authorization. State what is known versus
  unchecked, the consequence, and the recommended next action with its reason.
  Do not wait for the user to ask the exact question or bury the limitation
  after the result. Keep disclosures concise and relevant, not exhaustive noise.
- **Correct, not merely regret:** phrases such as "I should have" or "next time"
  are not corrective actions. When a mistake is found, state the specific error,
  affected result/decision, containment, correction, verification and remaining
  work. Perform the smallest authorized correction in the same turn when feasible;
  otherwise name the exact missing fact or approval. Preserve honest admissions,
  but do not substitute repeated apologies or wording changes for prevention.
  Do not claim resolution when only a note, plan or instruction was added.
- **Visible unfinished work:** distinguish proposed, implemented, tested,
  independently reviewed, published and deployed. Name the next consequential
  unfinished item without implying it was completed. Reuse the existing backlog
  or work log; do not create a parallel tracker or repeat closed findings.
- **Prevent recurrence:** for an observed repeated failure, prioritize a targeted
  executable guard and regression proof over another explanatory document.
  Until that guard exists, perform the check explicitly and label it manual.
  Do not claim these written instructions enforce runtime behavior.
- **Bound autonomy:** no extra campaign, restart, cohort reset, deadline extension,
  source substitution or exposure change follows automatically from research.
  Preserve approval and independent-review boundaries. While long-running work
  proceeds, do safe non-conflicting work instead of repeated polling or busywork.

Choose economic decision work ahead of optional docs, infrastructure and cleanup
when its prerequisites are met. Observed correctness/security failures that
invalidate the evidence or endanger operation still take priority. Keep records
concise in existing artifacts and the work log; do not create recurring audit
cycles merely because a study ended inconclusively.

## No-direction default loop
If no direction is given:

1. **AUDITOR**
   - assess visible repo for production readiness
   - classify findings by severity and evidence
   - choose exactly one highest-leverage next action

2. **DIRECTOR**
   - convert that into exactly one scoped objective
   - declare risk level: **LOW / MEDIUM / HIGH**
   - declare proof required

3. **ENGINEER**
   - implement the smallest correct change
   - show changed artifact/diff
   - run the narrowest relevant verification
   - state remaining unverified integration risk

4. **REVIEW**
   - LOW risk: same thread may close if proof is sufficient
   - MEDIUM risk: separate review recommended
   - HIGH risk: stop at **READY_FOR_INDEPENDENT_REVIEW**

5. **AUDITOR**
   - reassess repo after accepted change
   - identify what improved
   - identify the next highest-leverage blocker or weakness

Repeat until a stop condition is met.

## Production baseline
The repo is production-ready enough when:
- no known P0 blockers remain
- no unresolved high-risk item remains without explicit review or acceptance
- setup/run/test paths are documented and usable
- critical paths have targeted verification
- no obvious fail-open security or startup posture remains
- remaining issues are lower-priority or explicitly accepted risks

## Stop conditions
Stop when any of these is true:
1. Production baseline is satisfied
2. The next blocker requires human decision
3. The next blocker requires missing external information
4. The current task is high-risk and has reached **READY_FOR_INDEPENDENT_REVIEW**
5. Further work would be low-value cleanup rather than meaningful production hardening

## Command rules
- Treat command confidence as:
  - **VERIFIED_ENV**
  - **ASSUMED_ENV**
  - **UNKNOWN_ENV**
- Do not present UNKNOWN_ENV commands as universally safe.
- For destructive steps, include verification and recovery/rollback when meaningful.
- Non-destructive inspection steps do not need rollback.

## Repo commands
- Activate venv:
  - `source .venv/bin/activate`
- Install dependencies:
  - `./.venv/bin/pip install -r requirements.txt`
- Run all tests:
  - `./.venv/bin/python -m pytest tests -q`
- Run targeted auth/runtime tests:
  - `./.venv/bin/python -m pytest -q tests/test_auth_runtime_guard.py tests/test_auth_capabilities.py`
- Run targeted auth-facing regression slice:
  - `./.venv/bin/python -m pytest -q tests/test_auth_gate.py tests/test_auth_runtime_guard.py tests/test_auth_capabilities.py`
- Repo doctor:
  - `./.venv/bin/python tools/repo_doctor.py`
- Repair tool:
  - `./.venv/bin/python tools/repair_repo.py`
- Paper evidence collector status:
  - `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
- Search repo safely:
  - `grep -RIn "<pattern>" services dashboard scripts tests tools --include="*.py" | grep -v "__pycache__"`
- List source files:
  - `find services dashboard scripts tests tools -type f | sort`
- Lint:
  - `[fill in if used]`
- Format:
  - `[fill in if used]`
- Build:
  - `[fill in if used]`

## Project-specific conventions
- Python environment:
  - `source .venv/bin/activate`
- Do not edit:
  - `.venv/`
  - `__pycache__/`
  - `.pytest_cache/`
  - generated cache artifacts
- Prefer changing source `.py` files, not compiled `.pyc` files.
- Prefer targeted tests over broad rewrites.
- Update docs when changing setup, runtime behavior, operator workflow, or supported surfaces.

## Known likely-sensitive areas
- `services/security/auth_runtime_guard.py`
- `dashboard/auth_gate.py`
- `services/execution/`
- `services/backtest/`
- `services/analytics/`
- `services/desktop/service_manager.py`
- `scripts/run_paper_strategy_evidence_collector.py`
- deploy/startup/config/runtime guard surfaces

## Handoff minimum
Every review handoff should preserve:
- active role
- current objective
- shown evidence
- unverified points
- acceptance state
- active risks
- proof required next

## Visible work log
When a Codex thread changes code, docs, tests, runtime policy, operator workflow, or gate behavior, update `docs/work_log/review_stabilized_work_log.md` in the same branch before handoff.

Each entry should state:
- date/time or commit SHA
- active role and objective
- what was found
- what changed
- why that change was chosen
- expected outcome
- verification run, or why verification was not run
- remaining risk and acceptance state

If a change is high risk, the work-log entry must end at `READY_FOR_INDEPENDENT_REVIEW` until a separate reviewer or human accepts it.

## Operator rule
Do not use:
- "carry on until completion"

Use:
- "carry on until implementation proof is complete; if high-risk, stop at READY_FOR_INDEPENDENT_REVIEW"

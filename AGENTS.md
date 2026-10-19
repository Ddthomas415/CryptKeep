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

## No-direction default loop
First continue the user's accepted objective. Brief acknowledgements do not
restart a general production-readiness audit. Consult current code and the work
log; do not reopen completed issues without new contradictory evidence.
Use `runtime_prompt.md` for continuation and safe work during pending processes.

If no accepted objective remains, use this selection loop:

1. **AUDITOR**
   - assess current evidence against the user's objective
   - classify findings by severity and evidence
   - choose exactly one highest-leverage next action; for research, prioritize a meaningful economic answer

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
   - reassess progress toward the objective after accepted change
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
1. The accepted objective is complete (for a hardening objective, the production baseline is satisfied)
2. The next blocker requires human decision
3. The next blocker requires missing external information
4. The current task is high-risk and has reached **READY_FOR_INDEPENDENT_REVIEW**
5. Further work would be low-value cleanup rather than meaningful progress on the accepted objective

These stops apply to the affected objective. While tests, CI or independent
review are pending, continue safe non-conflicting work within accepted scope.
Do not modify the reviewed artifacts or use unaccepted changes as dependencies.
Do not invent new work solely to avoid waiting; report pending proof when no
useful independent work remains.

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
- Before any strategy, edge or backtest research, read `docs/research/RESEARCH_BRIEF.md` (results to date, costs, research rules).
- CryptKeep is multi-symbol: follow `docs/research/MULTI_SYMBOL_MANDATE.md`. Keep `research/symbol_coverage.csv` current, and keep project scope, research evidence and trading eligibility separate.
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

## Research questions
- Restate the question in one line using repo context. In this repo "edge" means
  a trading advantage, not a company or product name. Ask one question only when
  two readings would lead to materially different research.
- Open each primary source before citing it, and label claims SHOWN, CLAIMED or
  UNVERIFIED. Vendor marketing and press releases are CLAIMED at best. Never
  include advertisements or sponsored results as findings.
- Separate legal information advantages from material non-public information.
  Never propose obtaining or using confidential or misappropriated information.
- Check fit before depth: state data, infrastructure and time costs against the
  operator's capital and the data the repo already collects. Say plainly when
  costs exceed plausible returns.
- Answer first, then at most one table, then sources. Stop after the first
  useful answer and ask whether to go deeper; do not keep expanding on "carry on".
- Turn any surviving idea into a candidate hypothesis for pre-registration
  (signal, data, costs, pass/fail). Run nothing on market data without approval.

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

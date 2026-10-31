# AGENTS.md

## Primary Objective Protection (POP) - adopted 2026-10-30 by operator decision; revised the same day; failure-diagnosis,
## evidence and cross-review rules added 2026-10-31 at the owner's direction
Read this section first, then `docs/PROJECT_STATE.md`. POP controls which work is done and in what order.
It never narrows what the system can trade or research: the supported universe and
`docs/research/MULTI_SYMBOL_MANDATE.md` stay in force, and no change may remove symbol support from
code, config or tests without an explicit operator decision.

**Objective.** Build and validate the best risk-controlled multi-symbol trading system the evidence
supports, and run it with real money only if it is worth running at the owner's capital and costs.
"No viable system yet" is an acceptable answer.

**Classify every result.** On forward or paper data registered in advance, after costs, a strategy shows:
- a return edge: higher net return than holding BTC;
- a risk-adjusted edge: higher Sharpe than a fixed BTC/ETH/cash mix of similar drawdown;
- a diversification benefit: adding it to the current portfolio improves the portfolio's Sharpe or drawdown;
- risk reduction: smaller drawdowns without a better risk-adjusted return; or
- no demonstrated advantage.
Any claimed advantage must also pass the deflated Sharpe at the trial count in the ledger. Historical
results are labelled in-sample or exploratory, not as an edge. Report costs at the confirmed account tier
and at 0.90% per side, plus a measured-execution scenario once real fills have been measured (labelled
exploratory until then), and state at which cost levels the result holds. Report per symbol and for the combined portfolio.
None of these categories alone means profitable or worth running live.
**Worth running live** also requires expected net gain above infrastructure cost at the planned capital,
the live-safety items done, and the owner's approval.

**Diagnose every failure.** A failed or inconclusive result is not closed until its cause is classified, with
evidence, as one or more of: ineffective signal; execution costs; entry or exit implementation; regime
recognition; allocation; data or backtest limits; engineering defect; insufficient evidence. For each
correctable cause, propose the smallest investigation or correction as a queue proposal. Do not reject a new
idea by reusing an assumption never tested for it (a cost level, an exit model, a data source). Never weaken
risk controls or narrow the symbol universe to make a result pass.

**Evidence and omissions.** For every report, including on an agent's own earlier work:
- Report material findings, favourable or not, when found. Never wait for the owner to discover one.
- Label each material claim SHOWN (file or command), CLAIMED (by whom) or UNVERIFIED. Never state an
  assumption as fact; list the assumptions that could change the result.
- Before building on a question, search the repo (docs, work log, branches) for earlier work on it and cite it.
- When new evidence contradicts or narrows an earlier conclusion, yours or another agent's, say so in the same
  report and add a dated correction to the earlier document. Never correct a material mistake silently.
- Record why approved work was delayed, deprioritised or redirected.
- Before closing an item, list the open questions that could change its conclusion.
- Before calling material work done, state: the evidence the question needs; what was inspected (files, code paths,
  configuration, runtime state, logs); what was not or could not be inspected, and how that limits the conclusion;
  and what could overturn it.
- Keep evidence types apart: source code, default configuration, runtime configuration, runtime state, execution
  logs, backtests, paper results. A claim about the bot names the types it rests on.
- When implementing a list of requirements, report each item as done, partly done or not done.
- Every research report written from 2026-11-01 states, near the top, one line "Bot relation:" with one label
  (STANDALONE, SIGNAL_ONLY, BOT_RULES or BOT_PAPER; see `docs/research/result_labels_20261031/`) and whether the
  runtime configuration was checked. The weekly status lists reports without it.
- A pre-registration states sizing, turnover, missing-data and cost conventions before anything runs; a review does
  not accept it otherwise.
- End every report with: "What do I know that could change the owner's decision that I have not yet said?"

**Cross-review.** No agent certifies its own work as verified. Codex independently checks Claude's material
research conclusions against the files, scripts and results; Claude reviews the strategic implications of
Codex's engineering decisions. Until the other agent, or a separate reviewer that did not produce it, has
checked a conclusion, label it "self-checked". The reviewer works from the underlying files, not the author's
summary, and actively looks for missing configuration, untested assumptions, contradicting evidence, wrong execution
models and work that passes tests without meeting its objective.

**Configuration inspection** (owner-approved 2026-10-31). To establish what the bot actually does, agents may read
runtime trading configuration (`config/user.yaml`, `.cbp_state/runtime/config/user.yaml`, presets, campaign settings)
with a script that prints only whitelisted trading settings (strategy, preset, symbols, venue, signal source,
timeframe, window, loop interval, order size and type, stop, take-profit, trailing stop, hold limit, risk limits) or
redacted values. API keys, passwords, tokens and private keys are never printed, copied, committed or sent; `.env*`,
`.browser-access-token` and `.browser-compose-override.json` stay unread. Reading never permits changing: any
configuration change needs separate owner approval. A claim about what the bot does must state whether the runtime
configuration and the runner's own rules were checked; if not, label it INCOMPLETE.

**Omission register.** Every material omission found, by any agent or the owner, gets one row in the register in
`docs/PROJECT_STATE.md`: what was omitted; when it should have been found; which agent or review missed it; whether it
changed a decision or result; why it was missed (instruction, evidence discovery, configuration visibility,
implementation, research method, verification, reporting, or scope or priority drift); the conclusions affected and
the status of each; how it was found (agent review, agent during owner-requested work, or owner); the control that
prevents recurrence; whether that control has been tested. Finding an omission also means reviewing the conclusions
that depended on it.

**Queue.**
- `docs/PROJECT_STATE.md` is the single source of truth for priorities, decisions and status. Do not
  create other tracking documents or task systems.
- Two queues: engineering (Codex) and research (Claude). The owner orders them; agents propose changes,
  they do not make them. At most one active item per agent; finish, park (with approval) or hand back
  before starting another.
- The next queue item is the "accepted objective" for the No-direction default loop below. Use the loop's
  roles inside that item; use its selection step only to propose new items, never to start them.
- "continue", "do what's needed" or "carry out next steps" means: do the next queue item.
- If your queue is empty, or its next item waits on an owner decision, stop and ask. Do not start new work,
  and do not use the selection loop or the production baseline to create work. After an item is accepted,
  take the next queue item; do not expand into further hardening or cleanup.

**Task card.** The work-log entry that starts a queue item states, one line each: decision it serves;
done when (acceptance criteria); budget (sessions or work-log entries); stop rule; and the searches run for
earlier work with the documents found. A task is done only
when its acceptance criteria are demonstrated. If the budget runs out first, stop, report what is done
and what remains, and ask the owner to extend, cut or park it. Running out of budget is not completion.

**Parking lot.** Work found along the way goes into PARKED in `docs/PROJECT_STATE.md` as one line (what,
why, decision it would serve). It is not started until the owner moves it into a queue. Exception: a
defect that could lose money, data or credentials is reported at once, and fixed only with owner
approval, except stopping or disabling something already running.

**No silent abandonment.** Agents may sequence work and recommend changes, but may not remove, park,
indefinitely postpone or replace an approved strategic objective or experiment (including multi-symbol
research and the 25-symbol comparison) without stating why, the evidence, what replaces it, and getting
the owner's approval.

**No reopening.** A closed item is reopened only with a one-line statement of the new evidence.

**Initiative.** Agents should discover, investigate within approved tasks, challenge assumptions and
recommend new directions. They may not change strategic priorities on their own.

**Review.** Risk levels, high-risk triggers and review rules in this file are unchanged by POP.
Safety-critical work blocks live trading; it does not block paper testing or research that cannot place
orders or move funds. A safety fix is accepted only with a test that fails on the code before the fix and passes after.

**Reporting.** One weekly status (a recurring scheduled task): what materially advanced the objective; what
failed and why (cause class above); new evidence that contradicts earlier conclusions; what remains unknown;
what was omitted or overlooked earlier; drift from the approved objective or time used without a reason;
universe coverage; the next owner decisions (at most 3 open); omission-register counts, split into caught by
agents and caught by the owner; rework (accepted work later corrected); three measures (does the bot execute what the research says it executes; does every
position get exit management; did independent review find mistakes before the owner did); and the closing question
above. It is
one message plus one work-log entry, not a separate document. Between weeks, report only a fault, a
finished queue item or a needed decision.

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

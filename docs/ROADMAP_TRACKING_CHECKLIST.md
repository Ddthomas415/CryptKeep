# CryptKeep Roadmap Tracking Checklist

Created: 2026-08-02. Execution guide updated: 2026-10-01.

## Current Execution Contract

This section controls current task selection. Older tracking tables below are
reference material, not instructions to restart completed hardening or prioritize
paper waiting over delivery. AGENTS.md and the user's latest decision govern.

Highest-priority outcome: credible positive net economic gain within approved
risk limits. E01 is the first active lane and does not wait for R01-I04 or
intelligence deployment. Restore the existing intelligence path in parallel only
where it addresses a demonstrated evidence or operator-usefulness gap.
Keep the broader recurrence audit active through concrete affected-artifact
tracing, not repeated architecture reviews. No live activation is authorized.

Unchecked means completion proof is not established here, not that code is absent.
Inspect and reuse existing implementations before assigning a new build.
Role assignments below are responsibilities, not claims that agents are running.
Coordinator names an implementer and separate reviewer at dispatch using
docs/SPECIALIST_AGENT_PLAYBOOK.md. Coordinator owns this checklist and work log.

### Ordered Assignments

| ID / check | Assignment and responsible profile | Dependency | Completion evidence |
|---|---|---|---|
| R01 [ ] | AUDITOR: reconcile original capabilities with local, published and operating evidence | Independent supporting lane; must not block E01 | Caller-to-consumer map for explanation, feeds, archive, memory and research; each marked working, partial, disconnected or unverified with evidence. Verify whether an external backend already exists before rebuilding. |
| R02 [ ] | AUDITOR: trace all recorded recurrence families to affected artifacts/decisions | Parallel to R01; disjoint work | Reviewed coverage inventory; closed defects remain closed; each unresolved consequence has exact artifact, owner and correction. Unavailable history explicit; no claim of exhaustive review without coverage. |
| I01 [ ] | DIRECTOR: select smallest repair to existing explanation path | R01 | Named backend/interface, preserved capabilities, exact write scope, positive/failure acceptance tests. Obtain scope-impact decision only if capability is removed or narrowed. |
| I02 [ ] | ENGINEER, intelligence: connect curated feed parsing to durable storage/retrieval | I01; existing reviewed fixes reused | One authentic source record flows through actual selected boundaries; dates, source and content identity survive storage/retrieval; outage/retry does not invent success. Fixtures and real operations distinguished. |
| I03 [ ] | ENGINEER, intelligence: connect market observation and available archive/event context | I01; may parallel I02 with disjoint files | Timestamped market observation plus traceable source records for one asset; unavailable/stale archive and future context explicitly unavailable, not fabricated. No claim this completes all future-event modeling. |
| I04 [ ] | ENGINEER, interface: return cited answer through existing dashboard API | I02, I03 | One reproducible query displays actual retrieved evidence, as-of time, source links and limitations; static demo content unmistakable; no unsupported causal claim or order submission. |
| V01 [ ] | AUDITOR, independent verification: challenge integrated flow | I04 | Success, missing source, stale data, invalid dates, auth rejection, duplicate retry and teardown tests at actual boundaries; reviewed diff tied to revision/hash. No same-thread high-risk acceptance. |
| D01 [ ] | ENGINEER, delivery: publish reviewed bounded artifact | V01 and applicable publishing authorization | Scoped commit/PR, reproducible evidence, CI disposition; unrelated dirty work excluded. Pending CI does not stop unrelated accepted work. |
| D02 [ ] | ENGINEER, operations: deploy and verify only if authorized | D01 and explicit target/deployment authorization | Rollback plan, target version, health and actual user query checked. No automatic campaign reset, service restart or live trading activation. |
| E01 [ ] | AUDITOR, economics: reconcile existing strategy evidence and costs | FIRST PRIORITY; existing valid artifacts, no intelligence prerequisite | Current results classified actual/modelled, complete rules and cost assumptions, cash/buy-and-hold comparisons where appropriate, drawdown/exposure, capital basis, infrastructure cost and evidence limitations. No extra data collection unless needed. |
| E02 [ ] | DIRECTOR then ENGINEER, economics: one frozen context comparison | E01 plus usable context evidence | Predeclared hypothesis, eligible signals, primary metric, sample feasibility and end condition; compare unchanged baseline, include rejected opportunities and report STOP/REVISE/ADVANCE or insufficient evidence honestly. |
| E03 [ ] | GATE: decide next investment from evidence | E02 and independent review | Explicit continue/revise/retire decision with costs and risks; no parameter rescue on same holdout, automatic promotion or capital increase. |

### Preserved Later Capabilities

These remain part of direction, not canceled by the first vertical slice.
Schedule only after evidence identifies the next valuable increment:

- [ ] Explicit event dates, claim type, revisions/cancellations and outcome links.
- [ ] Source registry, archive discovery and source-quality evaluation.
- [ ] Additional supported assets/venues with isolated evidence and feasibility checks.
- [ ] Operator alerts, conversational/voice access and explanations without execution authority.
- [ ] Validated adaptation/champion-challenger research, portfolio integration and
  stocks/options feasibility under the existing linked roadmaps.

### Per-Assignment Discipline

- [ ] Name objective, current evidence, task ID, implementer, reviewer and exact write scope.
- [ ] Check prior resolution and current diff; do not reopen without contradictory evidence.
- [ ] Declare missing material facts and environment; obtain only required authorizations.
- [ ] Reproduce the defect or record the absent capability before modifying it.
- [ ] Test the real affected boundary; disclose mocks, skips and unverified deployment.
- [ ] Record commands/results, artifact revision and remaining risk in the existing work log.
- [ ] Separate implemented, tested, reviewed, published, deployed, operating and economic evidence.
- [ ] Compare outcome to acceptance criteria before marking complete; no permanent-fix guarantees.
- [ ] While proof runs, do safe non-conflicting accepted work; otherwise report pending proof once.

Completion updates cite the work-log entry and reviewed artifact. Human acceptance
does not establish deployment or operating evidence. New contradictory review
findings reopen only the affected scope. Dates are estimates only after sample
rates and external dependencies are known; no artificial deadlines or idle agents.

## Purpose

This is the operator-facing roadmap index for the current repo.

It organizes the existing backlog and roadmap files into one execution view.
It does not replace `REMAINING_TASKS.md`, close proof, authorize live trading,
or change campaign, gate, risk, execution, data-fetch, or deployment behavior.

## Source Of Truth

| Area | Source |
|---|---|
| Current system diagram | `docs/CURRENT_SYSTEM_DIAGRAM.md` |
| Repo layout/orientation | `docs/REPO_LAYOUT.md` |
| Backlog content | `REMAINING_TASKS.md` |
| Safe batching lanes | `docs/BACKLOG_EXECUTION_LANES.md` |
| Governance/risk lanes | `docs/OPERATOR_GOVERNANCE_LANES.md` |
| Launch readiness | `docs/LAUNCH_CHECKLIST.md` |
| Strategy expansion | `docs/research/strategy_expansion_roadmap.md` |
| Symbol selection boundary | `docs/strategies/symbol_selection_current_boundary.md` |
| Derivatives/intraday boundary | `docs/research/derivatives_intraday_roadmap.md` |
| Stock/options boundary | `docs/research/stock_options_requirements.md` |
| GitHub auth/publish boundary | `docs/GITHUB_AUTH_RUNBOOK.md` |
| Work evidence | `docs/work_log/review_stabilized_work_log.md` |

## Current Phase

Current operating phase: paper-evidence collection and read-only research.

The deterministic trading/risk engine remains the only authority that may move
capital. AI, research, archive, pattern, and roadmap work are advisory until a
separate reviewed runtime/gate change is accepted.

## Directional Plan

1. Keep existing paper campaigns running and monitor gate velocity.
2. Produce operator proofs that do not require code changes.
3. Run archive-backed research and record artifacts with hashes and explicit
   cost assumptions.
4. Use research results to choose candidate strategy work, not to auto-promote
   strategies.
5. Move to shadow only after the accepted paper/shadow checklist and required
   evidence are present.
6. Treat capped-live work as deferred until launch evidence, risk gates,
   reconciliation, rollback, secrets, and drill packets are accepted.

## Active Tracking Checklist

| Track | Current action | Primary command or artifact | Risk lane |
|---|---|---|---|
| Roadmap health | Verify this checklist links the accepted trackers and commands | `make roadmap-tracking-status-json` | Planning/reporting |
| Operator status bundle | Show the combined roadmap, backlog, research, read-only command, and proof status | `make operator-status-json` | Planning/reporting |
| Paper gate | Track `es_daily_trend_v1` qualified round trips and bars | `make status-paper-gate-velocity-json` | Passive/operator evidence |
| Paper campaigns | Confirm local campaign health after restarts | `make status-paper-campaigns` | Passive/operator evidence |
| Operator proofs | Record host/drill/proof packets called out by backlog markers | `make operator-proof-status-json` | Passive/operator evidence |
| Read-only command inventory | Verify operator helper commands are discoverable and wired | `make operator-read-only-command-status-json` | Planning/reporting |
| Next actions | Pull concrete executable rows only | `make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20` | Planning/reporting |
| Backlog batching | Select one lane before coding | `make backlog-lane-status-json` | Planning/reporting |
| Cost assumptions | Check local paper fee/slippage cost assumptions before trusting evidence | `make check-cost-assumptions-json` | Medium-risk read-only |
| Edge cadence | Check stored crypto-edge cadence before depending on funding/OI history | `make check-edge-cadence-json` | Medium-risk read-only |
| Research | Run accepted read-only archive/funding/strategy reports | `make research-pipeline-status-json` and `make research-command-status-json` | Medium-risk read-only |
| Research artifacts | Inspect accepted research artifact hashes and missing artifact rows | `make research-artifact-inventory-json` | Medium-risk read-only |
| Pullback candidate | Keep Stage 0 proof artifact visible; decide only after evidence review | `make pullback-stage0-verify` | Passive/operator evidence |
| Funding candidate | Keep funding research and price-join artifacts separate from promotion | `make funding-stage0-verify` when preconditions are met | Passive/operator evidence |
| Launch | Do not arm live until checklist is complete | `docs/LAUNCH_CHECKLIST.md` | High-risk/deferred |

## Remaining Task Snapshot

Historical snapshot only. Counts and projections below must not select current
work or establish current blockers. Continue the accepted objective under
`runtime_prompt.md`; verify relevant code and later work-log dispositions.

Last updated: 2026-08-25T03:31:56Z.

Generated check-in reports currently show 28 operator-proof actions. The
actionable queue remains dominated by host-side evidence, capped-live proof, and
coverage markers, not missing read-only command wiring:

- Passive operator-evidence tracking shows 15 rows: 9 satisfied and 6 waiting
  on future thresholds or explicit operator events.
- 25 proof-ready markers remain in the source summary. These require review,
  merge, recorded acceptance, host output, or explicit proof artifacts; they are
  not automatically new coding tasks.
- 28 host-side markers remain in the source summary. 21 remaining
  proof-or-coverage markers still require host output, proof artifacts, coverage
  evidence, or explicit acceptance.
- After excluding `host_side_reference`, `remaining_capped_live_proof`, and
  `remaining_coverage`, the immediate local next-action queue returns 0 rows.
- Backlog lane, research pipeline, research artifact, research command, roadmap
  tracking, and operator read-only command wiring currently report zero
  missing-action rows.

## Coding Batch Rules

- Batch only items from the same lane.
- Do not mix unrelated docs/tests with live/risk/execution changes. Include the
  targeted tests and documentation required to verify and explain each change.
- Do not rebuild proof-ready or accepted items unless current source code lacks
  them.
- If a low-risk batch discovers a high-risk surface, split the work and stop the
  high-risk part at `READY_FOR_INDEPENDENT_REVIEW`.
- If a task does not improve evidence velocity, profitability discovery, cost
  measurement, safety, recovery, or operator wake-up quality, defer it.

## Do Not Treat As Authorization

This checklist does not authorize:

- live trading;
- shadow execution;
- campaign promotion;
- strategy config changes;
- archive/sweep results influencing runtime behavior;
- new exchange, broker, stock, options, margin, short, or derivatives execution;
- secrets, deployment, systemd, watchdog, or background-job changes.

Those remain governed by their specific backlog item, decision record, launch
checklist, and `AGENTS.md` risk classification.

## Operating Loop

Use this loop for each work session:

1. Check branch and repo cleanliness.
2. Run `make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20`.
3. If output is passive/operator evidence, run or record the proof instead of
   opening a code batch.
4. If output is low-risk docs/tests, code one scoped batch with targeted tests.
5. If output is medium-risk read-only research/reporting, keep it read-only and
   artifact-producing.
6. If output is high-risk gate/execution/deploy, implement only after explicit
   scope and stop at `READY_FOR_INDEPENDENT_REVIEW`.
7. Update the work log for any repo change.

## Operator Check-In Checklist

Use this when the operator asks for a check-in and no specific host, campaign,
CI, or PR command is requested:

1. Run `git status --short --branch`.
2. Run `make operator-status-json`.
3. If a shorter action list is needed, run
   `make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20`.
4. Report only current status, blockers, and the next concrete action.
5. Do not run campaigns, fetch market data, change configs, push, merge, or
   repair auth unless the operator explicitly asks for that action.

## Fast Commands

```bash
make roadmap-tracking-status-json
make operator-status-json
make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20
make operator-proof-status-json
make operator-read-only-command-status-json
make backlog-lane-status-json
make status-paper-gate-velocity-json
make status-paper-campaigns
make check-cost-assumptions-json
make check-edge-cadence-json
make research-pipeline-status-json
make research-artifact-inventory-json
make research-command-status-json
```

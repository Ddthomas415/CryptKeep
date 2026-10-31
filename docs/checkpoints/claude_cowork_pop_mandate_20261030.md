# Primary Objective Protection (POP): audit and permanent fix

Drafted 2026-10-30 by Claude Cowork at the operator's request ("audit this and provide permanent solution").
Status: DRAFT for operator review. Nothing here is installed. Installing it means editing `AGENTS.md` and
adding `docs/PROJECT_STATE.md`, which needs the operator's approval.

## 1. Audit of the "priority drift / task proliferation" diagnosis

**The label fits, and the record shows it (SHOWN 2026-10-30 unless marked).**
- Uncommitted entries rose from 424 on Oct 28 to 537 now (`git status --porcelain`). There has been no commit
  since Oct 19 (`389020130`), and 18 tracked files under `services/` and `storage/` are modified.
- The task index `REMAINING_TASKS.md` is 442 KB (6,344 lines). The work log is 3.5 MB (55,047 lines).
- Codex has made about 72 work-log entries since Oct 28. By approximate keyword counts, about 28 went to
  funding-rate data and the research collector, which no live decision uses. Only 11 went to the position cap
  and 8 to stuck exits, and neither fix is wired into the live order path yet.
- My side contributes too: 283 scout leads with no plan change in the last 67, 28 sections in the Claude Doc,
  a decision list of about 20 items, and a check-in every 8 hours.

**Two points in the text need correcting.**
- "Optimising fees before establishing a trading edge" mixes two things. The fee level is part of whether an
  edge exists: in 2024-26 the candidate ties holding BTC at 0.50% per side and loses at 0.90%
  (`candidate_band_20261013/README.md`). Fees did not take over the work (one E1 entry since Oct 28). The
  right rule is: test every edge at the confirmed cost or at 0.90%, whichever is higher, and defer execution
  optimisation (E1, maker orders) until a net edge exists.
- "Self-directed / unauthorised" is not quite what happened. Most of Codex's steps record an operator approval
  ("operator continuation", "carry out next steps"). The leak is the granularity: open-ended prompts let the
  agent pick the next task, and step-by-step approvals let low-priority work through because nothing ranks it
  against the queue.

**Why principles alone will not fix it.** `AGENTS.md` already says to "choose exactly one highest-leverage
next action", and the drift happened anyway. A fix has to be built from constraints the agents cannot
reinterpret: one measurable objective, one owner-ordered queue, a limit on work in progress, a budget and a
done-test for each task, and a parking lot for new ideas.

## 2. POP rules (paste at the top of `AGENTS.md`; they apply to every agent in this repo)

```
## Primary Objective Protection (POP) - read first; overrides "No-direction default loop"

OBJECTIVE
Determine whether a trading system exists that is worth running at the owner's stated capital and
costs, and run it only if it is. "No viable system at this capital" is an acceptable answer.
A strategy has an edge only if, on forward or paper data registered in advance, after costs at the
confirmed tier or 0.90% per side (whichever is higher) plus slippage, it:
  (a) beats holding BTC on net return, and
  (b) beats a fixed BTC/ETH/cash mix of similar drawdown on Sharpe, and
  (c) passes the deflated Sharpe at the trial count in the ledger, and
  (d) its expected net gain exceeds infrastructure cost at the planned capital.
Lower drawdown alone is "risk reduction", not an edge. Say which one a result shows.

QUEUE
docs/PROJECT_STATE.md is the only task queue. The owner orders it. Agents may propose, not reorder.
Work in progress: at most ONE active item per agent. Finish, park or hand back before starting another.
An open-ended instruction ("continue", "do what's needed", "carry out next steps") means: do the next
item in the queue. It never means: choose new work.

TASK CARD (required before starting any queue item; one line each)
Decision it serves / Done when / Budget (sessions or entries) / Stop rule.
If the budget runs out, stop and report: finish, cut or park. Do not expand the scope to finish.

PARKING LOT
Anything discovered while working goes into the parking lot as one line (what, why, decision it
would serve). It is not started until the owner moves it into the queue.
Exception: a defect that could lose money, data or credentials is reported at once. It is fixed only
with the owner's approval, unless it is a pure stop or disable of something already running.

NO REOPENING
A closed or rejected item is reopened only with a one-line statement of the new evidence.

PROPORTIONAL REVIEW
Independent review is required for live-money code paths, anything frozen for research, and anything
pushed. Research-only plumbing gets one self-check and a short note.

REPORTING
One weekly status page: what moved the objective, what did not, what is using time without a reason,
and the next 3 owner decisions. Between weeks, report only a fault, a finished queue item or a decision
that is needed. At most 3 open owner decisions; the rest wait in the parking lot.
```

## 3. `docs/PROJECT_STATE.md` (one page; proposed first version)

```
# PROJECT STATE (one page; owner orders; updated weekly)
Last updated: 2026-10-30. HEAD 389020130 (Oct 19). Uncommitted entries: 537.

Objective and edge test: see AGENTS.md "POP".
Current evidence: BTC+ETH trend rule = risk reduction, not a return edge (no return edge over holding
BTC since 2016; rejected at 1.2% fees). At $1,000, ~$240/yr infrastructure cancels its 2024-26 return.

OWNER DECISIONS (max 3)
1. Approve commit and backup of the work (and whether the GitHub repo is made private first).
2. Capital: what amount the system is for, or "engineering project for now".
3. Approve the stuck-exit rule (keep pending with reason and alert; never convert, reprice, drop or cancel).

ENGINEERING QUEUE (Codex; one active)
1. [active] Protect the work: commit and backup, once decision 1 is approved.
2. Position cap (fix 4) plus complete balance reading (fix 1) wired into the live order path; independent review.
3. Stuck-exit rule (fix 2) wired, once decision 3 is approved; independent review.
4. Tracker v2 runs on time (its first week was filled in about 169 hours late).
5. Remove the expired ED-002 pilot job.

RESEARCH QUEUE (Claude; one active)
1. [active] Weekly review of tracker v2 against holding BTC, the 25/25/50 mix and cash.
2. One descriptive report on existing data: market regimes, holding ETH alone, trade count, win rate,
   profit factor (labelled descriptive, not a test). Needs approval.

PARKED (not started until moved into a queue)
- Funding-rate data (rest of fix 3): research only, no live use.
- 25-coin comparison: collector host, freeze, 182-day run.
- E1 maker/taker study, until a net edge exists; fee screenshot (useful, not blocking).
- CMC alerts (window opens Nov 10), state of residence, tax lots, USD vs USDC.
- Scout: weekly, or paused. New strategies, ML and sentiment: no.
- Dedicated Coinbase portfolio and key: needed before any live money.

CLOSED (reopen only with new evidence): E6, E7, E8, E9, E10, VOLFC-1, ATTN-1, ENTR-CB-1, CTREND-OOS (on hold).
```

## 4. How to use it

- To give work: "do queue item N" or "move <parking item> into the queue at position N".
- To check progress: "weekly status".
- To change direction: say so explicitly. Agents may propose a change with evidence; they do not make it.

## 5. Installing it (needs operator approval)

1. Codex adds the POP block to the top of `AGENTS.md` and creates `docs/PROJECT_STATE.md` from section 3,
   with the owner's edits.
2. Claude: scout to weekly (or paused), one weekly status instead of per-report sections, and no check-ins
   between weeks unless there is a fault or a decision is needed.
3. Both agents read `docs/PROJECT_STATE.md` at the start of every session and work only on their one
   active item.

## Addendum, 2026-10-30T19:59:45Z: installed
Operator: "has long as we are not limiting the repo's trading symbol capability's you can proceed with the best approach".
Installed with one change: an explicit guarantee that POP orders work and never narrows symbol scope
(MULTI_SYMBOL_MANDATE.md stays in force), and the 25-symbol forward comparison moved from PARKED into the
engineering queue. The review rule now leaves AGENTS.md risk levels unchanged instead of loosening them.
The installed text in AGENTS.md and docs/PROJECT_STATE.md is authoritative; sections 2 and 3 above are the draft.

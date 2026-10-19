# 90-day research budget: review amendment draft

Date: 2026-10-11. Active role: ENGINEER. Risk: HIGH (financial research governance).
Acceptance: READY_FOR_INDEPENDENT_REVIEW. This proposed amendment does not change
`research_budget_90d_20261011.md` or authorize spending, collection, trading or shutdown.
Original approval in principle is preserved; these corrections need independent review.
Window remains 2026-10-11 through 2027-01-09, not a profitability deadline.

## 1. Correct interpretation of the exploratory bootstrap

SHOWN in `stress_fee050_exploratory_20261011/README.md`: the 8-week-block bootstrap
Sharpe-difference summary reports observed 0.26, a 90% range of approximately
-0.05 to +0.57, and 91% of resamples above zero.

Use: **"91% of bootstrap resamples had a positive Sharpe difference in this
exploratory, same-data analysis; the reported 90% interval includes zero."**
Do not use "91% probability the strategy has an edge," "91% confidence of profit,"
or an independent-confirmation claim. This share is a resampling frequency under
the model, not a posterior probability or a calibrated out-of-sample success rate.
The variants/grid overlap and the benchmark uses hindsight exposure matching.
Registered REJECT at 1.2% remains unchanged; the 0.5% exploration supports at most
continued research. Product fee applicability is still pending for E1. All modeled
economics remain CF-MODELLED, not realized profit or infrastructure-adjusted returns.
The documentation values above were read, not recalculated in this amendment.

## 2. Copilot status: replace stale inactive/not-deployed language

Do not repeat older restoration notes as present operating status. In this chat,
the separate GATE stage directly inspected the running gateway on October 11:

- SHOWN: running and healthy; localhost-only 127.0.0.1:8001 binding; NO_TRADING=true.
- SHOWN: distinct browser/service credentials configured; runtime browser token
  matches its private artifact; expected existing network and read-only /repo mount.
- SHOWN: both private .browser artifacts are regular current-user-owned 0600 files,
  Git-ignored and excluded from Docker builds. No credential values were printed.
- CLAIMED by the operator: successful authenticated HTTP research route with source
  evidence and no upstream fallback, unauthorized denial, and no other-service recreation.
- CLAIMED by the operator: real browser rendered missing-token and invalid-token
  terminal metadata, HTTP 401 feedback and a cleared credential field.
- UNVERIFIED: authenticated browser UI happy path, sustained uptime, full workload
  value and broader full-system operating/production readiness.

Bounded runtime disposition was ACCEPTED_WITH_RISK for localhost research chat only.
This is a dated snapshot, not a new live check in this documentation stage. Deployment
is not proof of profitable research, server dependence, recurring operating health,
or trading authorization. Do not disclose secrets in a status or cost inventory.

## 3. E3 can proceed using the working $20/month cost

Treat ~$20/month as the already available working recurring-cost input, equivalent
to ~$240/year or ~$60 for a three-month planning comparison. These are estimates,
not an invoice claim. An invoice can reconcile taxes, discounts, currency and other
charges later; it is not a prerequisite for starting the workload inventory or for
recording the working cost. Replace "on receipt of invoice -> E3" with "E3 inventory
can start using the working cost; reconcile the amount if an invoice becomes available."
Do not hold the entire planning document incomplete solely for invoice receipt.

Keep E3 separate from E1: list workloads actually running on or depending on the
server, evidence, owner, need, move options, effort, recurring replacement cost and
lost/degraded capability. Local Mac copilot operation does not establish server usage
or prove every workload can move. Protect data/recovery and preserve the research,
news, archive and memory capabilities; no speculative profit valuations.

KEEP remains justified only by a needed workload that cannot reasonably move or
by migration cost exceeding retention over the comparison window. DOWNSIZE/PAUSE
requires a separately authorized preservation/recovery plan; this amendment performs
neither. A single strategy's fee saving is not the server's total value.

## 4. Effort estimates and optional caps

$0 new spend does not mean unlimited labor. Record an effort estimate and a bounded
checkpoint within the existing authorization. Additional hour caps are recommendations
for an explicit budget decision, not new mandatory gates on accepted work. No number
is invented or represented as approved here. E3's original "about an hour" is a planning estimate,
not a newly certified hard cap. E1's one collector/one analysis script is an artifact
description, not an effort budget; arrival-observation requirements need review first.

| Branch | Existing policy retained | Effort decision still required |
|---|---|---|
| E1 | $0 new spend; 3 discarded validation days + fixed 56-day sample + about 7 days analysis | Estimate build/validation/maintenance/review effort before selecting a follow-up; any new hard cap needs an actual decision |
| E2 | Existing frozen weekly pipeline only; $0 new spend | Estimate discretionary repair/reporting effort; existing approved schedule not changed |
| E3 | No new spend; start inventory from ~$20/month | Complete the authorized inventory; migration effort budget only if a migration is selected |
| E4/E5 | Not funded until E1 reports and separately selected | No work allocation or approval inferred; register caps if later funded |

Unset optional hour caps do not revoke existing authorization or create a new
implementation blocker. Do not disable jobs or withhold routine fixes because this
draft lacks caps. If a separately agreed cap is reached, record evidence and remaining work;
do not quietly extend or charge labor against an unrelated approved task.

## 5. E1 prerequisites and calendar reconciliation

E1 is not "waiting only on fees": freeze also requires independent acceptance of
the corrected arrival/taker observability, identical base quantity, conditional fill
models, book/trade gap policy, and sample/inference handling in
`maker_taker_prereg_20261011/PREREGISTRATION_draft_v3.md`. V3's proposed new contract
clauses do not inherit v2's conditional approval. Pair-specific fee rates and sources
remain pending. Full trade-through is not a certified fill and cannot justify live
execution. No collector is authorized or started by either draft.

Preserve all original thresholds and fixed durations. To report within this window,
sample start remains no later than 2026-11-07, validation 2026-11-04 to 2026-11-06,
day 56 on 2027-01-01 and a decision target by 2027-01-08. Those dates assume freeze
and implementation readiness in time; they are not permission to bypass gates.
A later start runs the full 56 days and reports in the next window. No extension or
retuning after an inconclusive outcome; record it for the operator's next decision.

Retain the two-experiments-awaiting-review concurrency limit, existing approved
monitoring exception, no infrastructure expansion without a cost-benefit case,
no new paid data approval, no increase in live capital, and per-branch CONTINUE /
PIVOT / STOP decisions. Neither positive CF-MODELLED economics nor this amendment
automatically funds a follow-up, changes a registered verdict, or activates anything.

## 6. Handoff and remaining unknowns

Only new documentation drafts changed. No original files, work log, frozen studies,
source code, runtime configuration, services or collectors were changed. The parent
records the supplied work-log entry after reconciling concurrent ownership.

Remaining: optional effort-budget decision; product-specific fee evidence; arrival-data
contract/tolerances; valid future sample size and coverage; migration feasibility
and workload value; authenticated UI happy path and sustained copilot operation.
The abbreviated review attachment reference 91d6d80... was not available in this
chat's artifact inventory; this draft addresses the explicit assignment and visible
source documents, not a claimed exhaustive reconciliation of that attachment.

Acceptance: READY_FOR_INDEPENDENT_REVIEW.

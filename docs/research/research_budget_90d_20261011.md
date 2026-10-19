# 90-day research budget and decision criteria

**Status:** APPROVED IN PRINCIPLE by the operator on 2026-10-11, with two clarifications applied (concurrency, server rule, E1 timing).
It is finalized once the actual fees (E1) and the invoice (E3) replace the estimates.

**Window:** 2026-10-11 → 2027-01-09. This is a planning window, not a deadline for finding profit.

**Principles:**
- Don't demand certainty before pursuing a promising hypothesis, and don't treat a promising result as proof.
- Spend money and time where the next experiment can change an important decision.
- Every conclusion is labelled DISPROVEN, UNPROVEN or UNTESTED.

## 1. Budget policy
| Area | Policy |
|---|---|
| Existing research | Reuse the current simulator, datasets and frozen results. |
| New backtests | Only when tied to a registered experiment (section 3) with an unanswered hypothesis. |
| Maker-vs-taker study | Proceeds once fees are verified and the pre-registration is frozen. |
| Paid data | No new subscriptions unless a registered experiment names the need and the cost. |
| Infrastructure | No expansion without a written cost-benefit case. Current cost: ~$20/month server. |
| Live capital | No increase on current evidence. |
| Server | Decided on the whole research workload (E3), not on one strategy. |
| Concurrency | At most 2 experiments awaiting operator review at a time. This does not count routine automated monitoring or data collection already approved (e.g. E2's weekly run, the CMC daily log, E1's collection once frozen). |

Any spend outside this table needs explicit operator approval.

## 2. Decision outcomes (apply per research branch)
**CONTINUE**
- **When:** evidence improves under realistic costs, holds across reasonable parameter changes, and shows a repeatable advantage against the relevant benchmarks.
- **Action:** the next pre-defined validation step. Never automatic deployment.

**PIVOT**
- **When:** the branch is still unproven, but the experiments point to a specific opportunity (execution cost, a regime-specific edge, lower turnover).
- **Action:** fund one targeted follow-up.

**STOP THIS BRANCH**
- **When:** the branch repeatedly fails its pre-defined economic or robustness requirements, or another test is not expected to be worth its cost.
- **Action:** preserve the results and redirect effort. Stopping a branch does not stop the program.

**Before seeing results, every experiment records:**
- hypothesis;
- maximum budget (money and calendar);
- success criteria;
- failure criteria;
- the next action for each outcome.

Results are filed beside the registration. A registered verdict is never overwritten. Exploratory analyses are filed separately and labelled.

## 3. Experiment register for this window

### E1: Maker vs taker execution (BTC+ETH weekly rule)
- **Hypothesis:** resting limit orders at the touch, with a taker fallback, cut all-in cost by more than 10 bps per side compared with taker.
- **Budget:** $0 new spend (public data, existing laptop). Calendar: ~3-day validation + 56 days. Build: one collector and one analysis script.
- **Prerequisites:** operator confirms BTC-USD and ETH-USD maker/taker rates and any discounts; pre-registration frozen.
- **Success:** MAKER SUPPORTED, i.e. the confidence interval sits entirely below −10 bps → PIVOT to a separately approved second paper ledger at the measured cost.
- **Failure:** MAKER NOT WORTH IT → STOP the execution sub-branch. Taker cost stays the planning cost.
- **Inconclusive:** no extension or retuning. Record it, and the operator decides once.
- **Timing:** the 3-day validation is discarded and never counted in the 56 days. The analysis and decision need ~7 days after day 56.
  - To report inside this window, the 56-day sample must start by **2026-11-07** (validation 11-04 to 11-06; day 56 is 2027-01-01; decision by 01-08).
  - If it starts later, the sample is **not shortened**. E1 runs its full 56 days and reports in the next window.
- **Status:** pre-registration draft v2, conditionally approved. Waiting on fees.

### E2: Frozen weekly paper test
- **Hypothesis:** none confirmatory. This is a pipeline check, because forward data cannot resolve a Sharpe difference within this window.
- **Budget:** $0. Runs weekly on its existing scheduled task.
- **Success:** each weekly run produces a valid ledger with no errors.
- **Failure:** a run error or ledger inconsistency → fix the pipeline only. The rule is never changed.
- **Note:** the operator can choose to add a fixed-mix comparison line to the weekly report (it changes reporting, not the rule).

### E3: Server workload inventory
- **Hypothesis:** the server supports research workloads whose value justifies ~$240/year.
- **Budget:** about an hour of operator time with Claude. No spend.
- **Method:** list every workload that actually runs on or depends on the server, with evidence (services, scheduled jobs, data stored). Mark each as needed, movable to the laptop, or idle. No speculative dollar values.
- **For each needed workload, record:**
  - can it move (laptop, cheaper host, or run on demand)?
  - what would moving cost, in one-off effort and any new recurring cost?
  - what is lost or degraded if it moves?
- **Outcomes:** "needed" alone does not keep the server.
  - KEEP only if a needed workload can't reasonably move, or moving costs more than the server over the window.
  - Otherwise DOWNSIZE, or PAUSE with a backup.
- **Input:** the actual invoice (Damian).

### Candidates, NOT funded until E1 reports
These could follow from E1, but none is funded yet. Priority order: E1, then E3 (independent of E1), then E2 (operational only).
- If E1 shows execution cost is material, E4 is the logical next hypothesis.
- If the 2024-26 weakness dominates, E5 may be worth more.
- **E4:** a no-trade threshold to cut turnover. The 0.5% vs 1.2% sensitivity suggests turnover is first-order. This would change the strategy, so it needs its own pre-registration and the frozen rule stays as-is.
- **E5:** a regime check on the weaker 2024-26 period, where 8/13 variants beat the mix.

## 4. Current evidence status (2026-10-11)
| Claim | Status | Source |
|---|---|---|
| Timing advantage vs exposure-matched fixed mix | UNPROVEN, credible. Registered REJECT at 1.2% stands; the exploratory 0.5% result is encouraging (13/13 variants, 94% of grid, 91.1% of bootstrap resamples > 0, not a probability; 90% range crosses zero). The exploratory label applies; it is not validation, and Required 1 (drawdown) still fails. | `stress_corrected_v1.json`; `stress_fee050_exploratory_20261011/` |
| Robust to nearby settings | Encouraging over the full sample; weaker in 2024-26 (8/13). | same |
| Return advantage vs BTC | Not demonstrated; active Sharpe negative in every window. | `dsr_btc_eth_trend_20261011/` |
| Sensitivity to fees | Substantial: the advantage over the mix is broad at 0.5% and mostly gone at 1.2%. | same |
| Maker fills at the touch | UNTESTED (that is E1). | `maker_taker_prereg_20261011/` |
| Profitability after costs and infrastructure | Not demonstrated. | `strategy_decision_report_20261011.md` |

## 5. Calendar
| When | What |
|---|---|
| 2026-10-12 00:47 UTC | E2 first natural run (do not fire it manually). |
| 2026-10-13 | ES trial endpoint (existing study). |
| When fees are confirmed (latest 11-03 to report in this window) | Freeze E1 → build → 3-day validation (discarded) → 56-day sample (start by 11-07) → ~7 days analysis. |
| On receipt of the invoice | E3. |
| 2027-01-08 | Confirmation study checkpoint (existing). |
| 2027-01-09 | Window review: assess the quality of the evidence and the value of the next experiment, per branch (CONTINUE / PIVOT / STOP), then set the next window's budget. It is not a deadline to have produced a profitable strategy. |
| 2027-02-15 earliest | CMC primary analysis (existing; outside this window). |

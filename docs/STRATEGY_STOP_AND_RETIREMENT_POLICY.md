# Strategy Stop And Retirement Policy

Date: 2026-07-03
Stage: paper/research operating state

## Purpose

This policy defines when a strategy is continued, frozen, retired, or kept in
paper. It is written before shadow/live pressure so the operator does not
renegotiate criteria during a drawdown.

## Scope

- Applies to every strategy before it advances beyond paper.
- Does not authorize live trading.
- Does not replace `scripts/check_promotion_gates.py`; it defines the manual
  review decision that follows machine-gate evidence.

## Evidence Sources

Use these in order:

1. Operator-host gate output, not stale backlog counts.
2. Provenance-qualified fill/order/session evidence.
3. Strategy-specific backtest baseline with dataset hash when available.
4. Paper journal and diagnostic reports.
5. Written operator review artifact.

If a source is missing, classify the decision as `INCOMPLETE`, not accepted by
assumption.

## Strategy Decisions

| Decision | Meaning | Minimum evidence |
|---|---|---|
| `keep_paper` | Continue paper observation without promotion | Gate incomplete or performance still inconclusive |
| `freeze` | Stop new evidence collection until cause is reviewed | Negative expectancy, repeated provenance failures, or unresolved operational defect |
| `retire` | Remove from active promotion path | Two or more retirement triggers active, or thesis invalidated |
| `advance_to_shadow_review` | Begin paper-to-shadow operator review | Machine gate clear, manual review complete, no retirement trigger |
| `rewrite_hypothesis` | Keep idea, replace strategy spec/config before more evidence | Results contradict stated hypothesis but the market premise may still be useful |

## Retirement Triggers

A single trigger requires written review. Two or more simultaneous triggers
require retirement or freeze before any promotion.

| Trigger | Threshold |
|---|---|
| Negative qualified expectancy | Average net PnL per qualified round trip below zero after fees/costs |
| Weak sample plus negative direction | Fewer than 20 qualified round trips and worsening win rate/PnL trend |
| Backtest divergence | Observed win rate or avg win/loss outside accepted tolerance versus baseline |
| Repeated evidence failure | Two collection cycles with missing or unqualified required provenance |
| Drawdown breach | Strategy drawdown exceeds configured max review threshold |
| Operational defect | Any critical signal/order/state defect affecting evidence validity |
| Thesis violation | Market behavior contradicts the documented strategy hypothesis |
| Cost-stack failure | Fees, spread, and slippage consume expected gross edge |

## Project-Level Thesis Gate

By the first formal shadow-review packet after archive-first backtesting lands,
the flagship profitability hypothesis must have one of:

- positive walk-forward expectancy after measured or conservatively modeled
  costs, or
- a written decision to revise the thesis, change strategy family/horizon, or
  pause the project.

Until then, the project identity remains evidence-generation and profitability
measurement, not a profitable trading system.

## Required Review Artifact

Before a strategy advances beyond paper, write a dated decision record under
`docs/strategies/` with:

- gate output used as ground truth
- strategy baseline source and dataset hash, if available
- qualified round trips counted
- observed win rate, avg win, avg loss, expectancy, and cost basis
- active retirement triggers
- decision from the table above
- operator acceptance state

## Non-Negotiable Rules

- Do not promote a strategy on raw all-history fills when the gate requires
  provenance-qualified fills.
- Do not treat 10 round trips as profitability proof.
- Do not override negative expectancy because the strategy "looks close."
- Do not change thresholds after a drawdown without recording the reason first.

## Executable Guard

`tests/test_operator_runbook_policy_guards.py` pins the decision table,
retirement triggers, project thesis gate, and non-negotiable rules so strategy
promotion decisions cannot silently drop the accepted stop/retirement boundary.

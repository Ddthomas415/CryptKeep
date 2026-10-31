# ED-002 defaults-25: descriptive prospective comparison

2026-10-27. Active role DIRECTOR. Risk HIGH (financial research design).
Acceptance: READY_FOR_INDEPENDENT_REVIEW. Version: DESCRIPTIVE-1, NOT FROZEN.
Design only: no acquisition, market evaluation, activation or trading authority.

## Decision And Question

ED002-DESCRIPTIVE-20261027: the operator selected "Prepare descriptive comparison
contract (Recommended)" after reviewing SB-1's development limitations. This
adopts preparation alongside unresolved inference work, not the detailed new
proposals below. The original confirmatory design, SB-1 sources, guard, results
and promotion requirements remain unchanged. No capability is retired.

Question: over a separately frozen future 182-day period, how much modelled net
USD profit or loss do the three frozen default families produce across the
declared 25 assets, compared with cash, BTC hold, a declared fixed-unit mix and
the existing incumbent, using one shared account per alternative?

This answers observed model economics under stated conditions. It cannot certify
predictive advantage, expected income, confidence coverage or trading readiness.
Positive descriptive results do not revive rejected historical variants or pass
the original confirmatory screen. Negative results remain scoped to this model.

## Adopted Inputs And Unchanged Implementation

SHOWN: recorded decisions adopt the 25-symbol scope, the frozen signal snapshot,
event-triggered allocation, shared cash with carry-forward, one-hour execution
delay, and these model settings:

| Item | Adopted model setting |
| --- | --- |
| Capital | USD 1,000 per alternative, initially flat, no deposits |
| Horizon | 182 days, prospective dates still unset |
| Fees | 0.50% per side primary; 0.90% per side stress |
| Adverse fill adjustment | 0.25% per side in both scenarios |
| Cash rounding | USD 0.01 per order, buy debits up / sell credits down |
| Overhead sensitivity | Separate USD 20/month, prorated as 20*12*days/365 |

These are hypothetical inputs, not current pair-specific fees, actual account
balances, settlement guarantees, live allocations or risk limits. Do not add a
second spread charge or deduct overhead from the allocation wallet.

Reuse, do not replace, `simulate_delayed_comparison` in
`services/backtest/delayed_research_comparison.py`, the delayed/frozen bridges,
and `shared_cash_research.py`. The saved independent carry-correction review
is ACCEPTED_WITH_RISK for synthetic implementation only; that does not accept
this new contract or establish end-to-end market-data support.

The three families remain breakout_default, ema_cross_default and
mean_reversion_default from the exact frozen snapshot. No search, shorts,
extra stops, family blending, or post-result symbol selection. Buys occur only
when flat; sells when held. All-HOLD emits no rebalance. New entry targets are
at most 1/25 of the signal-close NAV, not a permanent position cap. A batch may
resize other holdings because targets preserve close weights, not exact units
at the delayed open. Record that incidental turnover. Net sell proceeds fund
buys under the existing joint, fee-inclusive affordability/lot rules.

Keep all 25 identities in the denominator: BTC, ETH, SOL, BNB, XRP, DOGE, ADA,
AVAX, LINK, DOT, LTC, MATIC, UNI, ATOM, FIL, APT, OP, ARB, INJ, SUI, PEPE, WIF,
JTO, BONK and PYTH. Resolve exact Coinbase USD identities before freeze; ticker
similarity is not sufficient. Preserve dated MATIC exclusion evidence, with no
POL substitution. Known exclusions leave allocation unused; unknowns are not
excluded survivors. Do not change the coverage registry from design alone.

## Proposed Remaining Input Rules

These are NEW proposals for review, not adopted venue facts or executable input
records. They consolidate the original unresolved choices rather than silently
inferring their adoption from the sequencing decision.

- Controls: propose the original fixed-unit mix of 25% BTC, 25% ETH, 50% cash.
  Cash and BTC hold are separate controls; the incumbent retains its unchanged
  Sunday 28-day trend / 30-day volatility rule. Seven arms times two cost cases
  are 14 alternative trajectories, not USD 14,000 committed or additive income.
- Public eligibility: use dated exact product/base/quote identity and raw field
  presence. For the Exchange metadata schema, require online status and explicit
  false trading_disabled, cancel_only, limit_only, post_only and auction_mode.
  Do not invent an absent view_only value or assert private account entitlement.
  Conflicting identity, malformed fields or missing required values are unknown.
- Freshness: propose one-hour model validity from each metadata receipt, with
  no backward extension. At a decision or execution time, use the latest record
  actually received by that time, expiring at receipt plus one hour, exclusive.
  A later record cannot repair an earlier gap. Evaluate signal permission at T
  and execution permission at E separately. This convention is not evidence
  that venue status remained constant between observations. Collection feasibility
  must be demonstrated before freeze; no collector or refresh is authorized here.
- Rules: propose positive lot_step from dated base_increment, quote_step=0.01
  from the adopted cash model, and model minimum_qty=minimum_notional_gross=0
  for quantity-specified full-fill orders. These zero minima are hypothetical
  market-model conventions, not current order acceptance or account permission.
  Exact mapping to existing rule records still needs reviewed synthetic proof.
  Price ticks are not cash settlement precision; do not conflate them.
- Changes: retain known-ineligible flat assets as cash; unknown required status
  stops the affected account. New listing identities outside the declared 25
  cannot enter this study. Delisting is not a forced zero payout or free exit.
  If a held asset lacks a required valid mark, the account becomes INCOMPLETE.

## Clocks, Data And Completion

Propose A as the first Monday 00:00 UTC at least seven days after a signed future
freeze, subject to completed preflight before A. Set E=A+1 hour and B=A+182 days.
This document supplies no calendar dates and does not freeze or start a study.
Missed preflight leaves the study unactivated; no quiet backdating or extension.

At signal close T, use only its frozen 300 completed hourly bars, with receipts
no later than T+1 hour. Do not include the intervening bar in the signal. Fill
at the modelled open E=T+1 hour. Preserve bar, receipt, signal and execution
times separately. Ex-post outcome-price checks do not establish signal-time
availability or measured latency. All seven accounts share the cash-only first
hour [A,E); controls must actually enter at E. The first trade affects equity
over [E,E+1 hour]. Final primary NAV is the marked close B; no pending order
executes at B. Do not rebase capital after entry costs.

Require 300 contiguous warm-up hours for eligible defaults and 61 complete UTC
days for the incumbent. Warm-up is not traded confirmation evidence. Old archives
ending October 9 cannot supply future outcomes or assumed receipt times. Raw
public data, first-receipt timestamps and original payload/row hashes must be
preserved append-only. Store exact identity/rule versions with their provenance.

No interpolation, last-price carry, retrospective permission or convenient
replacement source. A documented recent listing may remain signal-not-ready
while flat; an unexplained required signal gap or missing held mark is
INCOMPLETE. Preserve reason, stopped state, last valid NAV and all failed arms.
A known missing execution open expires that batch under the existing engine;
it is not silently retried. Required benchmark entry failure invalidates the
comparison, even if its mechanical ledger stayed cash-only and COMPLETE.

Carry all seven accounts' cash, quantities, basis, pending targets and initial
entry evidence through chunks and the A+91-day boundary. No reset, liquidation
or interim strategy selection. Midpoint activity is input/accounting health
only; score halves only after B. Keep primary top-level economic results unknown
unless all seven arms cover the complete period. Partial arm diagnostics are
not a completed comparison or grounds to delete a losing/failed arm.

## Descriptive Deliverable, Not A Statistical Gate

After a separately authorized completed run, report every family and control,
both fee scenarios, and both halves with carry-forward. Lead with net dollars
and losses, not ranks or a selected best trade. Include:

- Initial and final marked NAV, net USD and percentage return, realized and
  unrealized PnL, fees, adverse-price adjustment, rounding and separate overhead.
- Dollar advantage or shortfall against every control over identical dates;
  after-overhead results are scenarios, not a verified infrastructure bill.
- Hourly marked maximum drawdown, drawdown duration, exposure/time in market,
  turnover, worst daily model return, completed position cycles and open risk.
  A position cycle runs from flat through any resizes until flat again; no
  claim that cycles or overlapping trades are independent observations.
- All 25 consideration rows per family, evaluated versus excluded/unknown,
  coverage/missingness by reason, and per-symbol contribution reconciling to
  the shared account. Per-symbol contributions are not standalone portfolios.
- Incidental rebalances, refused/expired batches, dust and benchmark entry proof.
  Retain open positions in primary NAV. Any terminal liquidation sensitivity
  must be separately labelled and preserve unsellable holdings/dust; do not
  deduct exit costs twice or imply that marked gains are realized gains.

Record three policies, 75 symbol-family considerations, 150 cost-case exposures
and 14 trajectories, distinguishing actual evaluation from consideration. Counts
are not an effective independent sample size. Do not calculate confidence bounds,
p-values, DSR, probability of profit, expected monthly income, annualized earnings
or a combined statistical PASS in this branch. No early economic ranking.

SB-1 remains unqualified; its 96 development decisions, 25 abstentions, original
guard and failed prior pilot stay unchanged. A future validated inference method
cannot retroactively turn inspected descriptive outcomes into an untouched
confirmatory test. Any later confirmation needs its own prospective protocol.

## Evidence, Remaining Proof And Authority

SHOWN: the current source implements delayed seven-arm accounting and the saved
review records 185 passing targeted tests. Those tests were NOT repeated for
this document. Collection continuity, current warm-up, mapper correctness and
the requested report columns are UNVERIFIED end-to-end. Do not claim the existing
harness already generates every diagnostic above.

Two explicit model premises: (1) one Coinbase USD spot venue, no FX, interest or
leverage; (2) hypothetical full fills under the declared costs, precision and
one-hour status-validity model, not actual executable liquidity. Missing evidence
is not supplied by either premise. No claim of future data completeness or return.

Next proof is review of this exact contract, then only demonstrated gaps in the
existing mapper/report path with synthetic fixtures. Fixtures must cover metadata
receipt/expiry and T/E separation, absent/invalid flags, missing marks, missing
benchmark entry, full/split and midpoint carry, all 25 rows, and dollar/cost/
contribution reconciliation. Existing accepted sources remain unchanged here.

Before activation: detailed proposals must be adopted, feasibility and synthetic
mapping/report proof reviewed, and future A/E/B plus source/data/contract hashes
recorded. Public acquisition and evaluation each require bounded authorization;
neither follows from preparing this contract. No new job, service, dependency,
account/credential access, risk/capital change, order, commit or push occurs here.
Preparation complete: READY_FOR_INDEPENDENT_REVIEW; experiment readiness INCOMPLETE.

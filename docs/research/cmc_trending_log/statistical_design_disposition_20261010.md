# CMC Statistical Design Disposition

Role: AUDITOR. Risk: HIGH research interpretation.
Status: ACCEPTED_WITH_RISK by separate Hooke review, disposition only.
Reviewer verified pilot counts, source boundaries and scope; no blockers found.
No replacement method, compute batch or scoring authority is approved.
Scope: review the failed candidate and select a bounded next step, not a new
method, a changed trading rule, an early market analysis or scoring permission.

## Findings

SHOWN by paired_ratio_pilot_result_20261010.md: the locked pilot produced
positive lower interval bounds in 6/20 overlap7 histories at90days, 3/20
persistent histories at both lengths, and5/20 and3/20 shared_unequal histories.
Five of twelve candidate cells flagged. The candidate is not eligible for
primary scoring. These are model-family observations, not estimated market
false-positive rates. Twenty trials per cell do not certify coverage or power.

SHOWN by the candidate contract: the target is event-weighted E[S]/E[N],
with paired complete calendar inputs, positive expected count and conditional
stationarity/mixing/moment assumptions. Neither a large coin count nor many
bootstrap repetitions establishes those assumptions. Seven-day holding-period
overlap is not a justified upper bound on all market dependence.

SHOWN by the authoritative checklist: mature primary evidence is not yet
available. The failed pilot has no power study. There is no supported claim
that the registered90-day window can distinguish an economically useful edge
from zero. This is unknown, not proof that90days can never suffice.

Primary-source boundary: [Sharipov and Wendler](https://arxiv.org/abs/0911.3083)
study bootstrap consistency under specified dependence and moment conditions.
[CMU bootstrap lecture](https://stat.cmu.edu/~cshalizi/dst/20/lectures/16/lecture-16.html)
explains dependence-aware resampling and its stationary, short-dependence
limitations. These sources do not supply a finite-sample guarantee for this
particular ratio or the CMC market data. No theorem transfer is claimed here.

## Recommendation

Do not substitute a stationary bootstrap, longer block, wider interval or
larger resample count merely because the current pilot failed. Those would be
new candidates requiring their own justification, not corrections to the
frozen candidate. Do not tune against its saved histories.

The next methodological deliverable should be a mathematical applicability
review before another implementation or simulation: either establish explicit
conditions supporting a proposed ratio procedure, or state why the available
assumptions cannot support the requested confidence claim. An empirical
diagnostic cannot prove stationarity or mixing for future returns.

Any subsequent prospective method contract must identify:

- The unchanged event-weighted target, paired BTC comparison, cost convention
  and complete-cohort policy; any change requires an explicit amendment.
- A complete argument covering joint dependence, random counts, denominator
  behavior and the ratio transformation, not just a scalar mean theorem.
- A minimum economically useful effect and a declared power target. Do not
  infer these from the best historical result or confuse benchmark excess
  return with absolute dollar profit after infrastructure.
- Fresh validation streams, declared error/power criteria, per-model acceptance
  rules and a reviewed compute ceiling before generation.
- Refusal when applicability, coverage or power is unsupported; no automatic
  primary-gate integration following simulation success.

This review does not choose those constants or authorize a new compute batch.
The original contracts, candidates and failed trials remain unchanged.

## Useful Work That Remains Valid

Continue the accepted collection and descriptive reporting lane. At maturity,
report observed net outcomes, paired BTC differences, costs, drawdown and
coverage with their evidence labels. Do not turn a descriptive positive result
into a confidence-qualified primary pass. Do not treat return per hypothetical
event as an executable portfolio profit without sizing and execution evidence.

R05 remains INCOMPLETE. The practical outcome of this review is a stopping
criterion for unjustified method churn, while preserving the research objective.
No scheduling, account, campaign, trading, market scoring or frozen-source change.

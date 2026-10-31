# ED-002: one prospective statistical revision plan

2026-10-27 New York. Active role DIRECTOR. Risk HIGH (financial inference).
READY_FOR_INDEPENDENT_REVIEW. Proposal only; no new implementation or run.

## Decision And Preservation

Question: can one dependence-aware replacement screen control false positives
in a fixed synthetic audit without making the test economically powerless?

SHOWN: the original seven-day percentile screen flagged8/32 persistent-null
trials, despite no expected family-versus-incumbent wealth advantage. Its code,
213-test result, receipts and pilot remain frozen in
`ed002_stat_validation_20261027/`; their16hash bindings were rechecked. No
independent review exists because the assigned reviewer returned a usage limit.
No retry, duplicate reviewer, recalibration or market study is initiated here.

The operator approved that checkpoint, then requested the next steps. This
prepares a revision/validation contract, not permission to silently replace the
method. Existing accounting/bridge/comparison acceptance remains closed. All
adopted economic settings,25-symbol scope and one-hour execution delay remain.

## One Candidate, Not A Search

Recommend SB-1: paired stationary bootstrap, with its mean block length set by
the corrected Politis-White automatic selector rather than choosing7/14/28after
outcomes. This is a candidate, NOT a proven repair. The cited selector targets
dependence/variance properties; its literature does not certify our finite-sample
USD terminal-wealth quantile or a nonstationary crypto market.

Keep the182daily rows, joint seven-arm resampling,20000replicates per call,
three family-minus-incumbent wealth contrasts and one-sided1/60tail unchanged.
Keep resampling portfolio returns, not invented executable trade paths. No
post-outcome family/asset selection, Sharpe substitution or economic-rule change.

Proposed fully specified selector inputs: seven log-return columns and three
family-minus-incumbent log-return differences, plus the square of each centered
column. Remove exact constants only, recording which. Select one common mean
length: the ceiling of the maximum finite positive stationary estimate, at least1.
All seven arms use the same resampled calendar indices. This maximum rule is a
conservative-design hypothesis, not a coverage or portfolio-profit bound.

If a nonconstant input has an undefined selector result, return INCOMPLETE;
never fall back to seven days or drop a troublesome arm. If every input is
constant, use length1 and label the resulting distribution degenerate, not a
confidence certificate. Returns at total loss make this log-selector path
INCOMPLETE, not a removed bankruptcy. Preserve ordinary accounting for the loss.
If182/selected_length<10, abstain from inference with an insufficient-blocks
reason. Ten is a proposed operational guard, not proof of an adequate sample.

For each next index, restart at an independent uniform calendar position with
probability1/mean_length; otherwise advance one day with circular wrap. Use one
shared index sequence across arms. Freeze the exact RNG/implementation/source
and selector version before random validation. Use batches, not unbounded arrays.

## Fixed Validation Cases And Authority

Two separate evidence lanes: deterministic implementation/reference fixtures,
then a fresh randomized audit. The old pilot is development evidence only;
fresh synthetic paths are not untouched market data.

Six182-day null cases are fixed now: iid Gaussian; Gaussian AR(1)rho0.5,0.8,
0.95 and-0.5; and common two-state volatility with no signed-return persistence.
All four tested arms have identical marginal path laws and no expected wealth
advantage, with common shocks plus identically distributed idiosyncratic shocks.

For Gaussian cases, use independent stationary unit-variance AR factors,
common log-shock scale0.01 and idiosyncratic0.005,1024burn-in observations. Draw
initial AR factors from their stationary standard-normal distribution. For the
volatility case, multiply iid factors by a common two-state scale0.5or2.0,
stay probability0.95, initial state equiprobable. The two unused market controls
are diagnostic columns as in the pilot; cash returns0. These are test fixtures,
not fitted market regimes or assertions that real returns are stationary.

Development:16paths per null,96calls,90-second compute limit. Use only for
implementation diagnostics; do not delete cases or change method parameters
based on the estimated error rates. Bug fixes must preserve outputs and be
reviewed before freezing a candidate. No automatic method search is permitted.

Audit:512fresh paths per null,3072calls. Power diagnostics:64paths at each of
three positive log-drift injections in the rho0.8 generator,192calls. Injection
sizes are log(1+u/1000)/182per day for noiseless uplifts u=50,150,300USD, NOT
claims of expected dollar profit under noisy compounding. Keep overhead/economic
filters separate. Total audit3264calls, at most600seconds compute, one foreground
process with one BLAS/OMP thread; no background job or scheduler. Development
plus audit uses at most3360calls/67,200,000resamples and690compute seconds.
Imports and final receipt writes must have separate stated limits in the runner.

Allocate independent streams by hashing fixed stage/case/trial domains
`ED002-SB1-development-20261027`, `ED002-SB1-audit-20261027` and
`ED002-SB1-power-20261027` with the frozen implementation identity. No audit
paths are generated/read before source/parameter freeze and review. Seeds are
reproducibility inputs, not secret holdout protection or restored virgin history.

## Prospective Pass, Fail And Stop Rules

Count a null false positive if ANY of the three lower bounds exceeds0. Record
all paths, numerical failures and abstentions. Report conditional and unconditional
rates; require at least80% computational/inferential availability in every case
so a rule that never computes cannot pass by abstaining.80%is a proposed utility
criterion, not a statistical theorem.

For each null case calculate a one-sided exact binomial upper limit at confidence
1-0.05/6, over all512paths. To qualify for this FIXTURE SUITE only, every upper
limit must be at most0.05. The correction concerns six validation cases; it is
separate from the three-contrast1/60method tail. Integer arithmetic check:
at512trials, at most14false positives satisfy that upper-limit criterion.

An upper limit above0.05means insufficient evidence of required control; a lower
limit above0.05is evidence of inflation for that generator. Neither certifies a
crypto-market error rate. Report power at all three injections with uncertainty,
availability and counts. Low power cannot be hidden behind correct error control
or advertised as a useful profit detector; no income probability is estimated.

No early stopping on good results, extensions, seed replacements, discarded
failed replicates, alternate lengths or a second audit in this budget. Timeout,
unresolved bug or incomplete receipts -> INCOMPLETE. A failed qualification or
unusable power is recorded, not repaired using that audit. Any later candidate
requires a new disclosed hypothesis/budget, not repetition until it passes.
Even qualifying all fixtures grants no live/paper eligibility, real-world
confidence certificate or market-run permission.

## Dependencies, Review And Next Action

Read-only inspection: neither `arch` nor `scipy` is installed in this repository
environment. No installation was attempted. A future implementation decision
must pin the corrected reference/source/license and either use a separately
approved isolated dependency or a narrowly reviewed NumPy implementation;
do not modify the existing environment silently. Exact reference parity must
be established before either randomized stage. This plan is not runnable code.

One independent method review must cover this proposal BEFORE implementation
or audit authorization; then implementation needs synthetic/reference proof and
separate high-risk review before the fresh audit. The existing unavailable
reviewer is not silently replaced or represented as having accepted this plan.
No new financial settings, infrastructure, market data, private access, services,
trading, commits or pushes are authorized. The existing research scope is intact.

## Primary Sources Opened

- [arch 7.2 stationary bootstrap](https://arch.readthedocs.io/en/stable/bootstrap/generated/arch.bootstrap.StationaryBootstrap.html):
  documented mean-block parameter and reproducible seeded implementation.
- [arch corrected block selector](https://arch.readthedocs.io/en/stable/bootstrap/generated/arch.bootstrap.optimal_block_length.html):
  separate stationary/circular estimates and corrected selection reference.
- [Politis and White 2004](https://public.econ.duke.edu/~ap172/Politis_White_2004.pdf):
  dependence-aware block selection in a stationary time-series framework.
- [Patton, Politis and White 2009 correction](https://public.econ.duke.edu/~ap172/Patton_Politis_White_2009.pdf):
  corrected stationary-bootstrap variance constant and selection calculations.

These sources support a candidate implementation route, not the proposed max
aggregation, ten-block guard,80%utility threshold,182-day power or market-profit
inference. Those are explicitly proposed rules whose adequacy must be tested.

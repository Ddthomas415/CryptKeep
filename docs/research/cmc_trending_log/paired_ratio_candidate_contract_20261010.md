# Paired calendar-ratio candidate: complete development contract

Role: DIRECTOR. Risk: HIGH. Status: ACCEPTED_WITH_RISK by separate Hooke
review for development contract only. No blockers found. Implementation needs
its own review; pilot execution and scoring are not authorized by acceptance.
One candidate, no method search. Scope is conditional-method development;
not primary scoring, market certification or an alteration of trading rules.

## Implementation disposition

Standalone implementation: `scripts/research/cmc_paired_ratio_candidate.py`.
Separate Hooke review: ACCEPTED_WITH_RISK after the strict numeric-metadata
correction. Parent and independent review each passed52 targeted tests across
candidate, completeness helper and adapter. Original31-test run is superseded
by this wider corrected run, not counted as an additional study.
No integration, pilot generation, confidence certification or scoring took place.
The next stage needs a separately reviewed pilot stream manifest and cost
estimate; do not reuse prior calibration streams or launch full confirmation.

## Estimand and inputs

Preserve theta = E[S]/E[N] under the stated stationary model, estimated by the
event-weighted ratio sum(S)/sum(N). Inputs are the accepted complete-cohort
calendar pairs, one pair for every predeclared mature UTC entry date, including
observed zero-event dates. Require COMPLETE_FULL_COHORT, resolved membership,
finite sums and nonnegative integer counts. A zero count requires a zero sum.
Require a positive total count. Missing dates or outcomes refuse, never impute.
Never replace the event target with an equally weighted daily mean.

Two unverified model assumptions:
1. The joint stationary pair process has finite 2+delta moments for some delta>0
   and strong-mixing coefficients satisfying sum(alpha(k)^(delta/(2+delta)))<infinity.
2. E[N]>0 and the linearized ratio has positive long-run variance. The joint
   CLT, paired-bootstrap convergence and bootstrap delta-method conditions
   required for the construction must be established independently before an
   asymptotic coverage label is allowed. They are not asserted by passing tests.

No finite-sample market error guarantee follows from these assumptions alone.

## Exact candidate algorithm

Use a circular paired-block basic interval, never independent event resampling.
For n calendar days fix L=max(7,ceil(n^(1/3))) and B=2000. Implement integer
ceiling cube root exactly, avoiding floating boundary differences. Require
n>=2*L as a computational floor only. These constants are locked before any
new calibration; no winner selection or block-length tuning is authorized.

For each replicate independently sample ceil(n/L) uniform integer starts from
0..n-1; append L consecutive pairs from each start modulo n, truncate to n.
Keep S and N together. Compute theta_star = sum(S_star)/sum(N_star).
If any replicate denominator is zero or any sum/ratio is nonfinite, the whole
interval is INCOMPLETE. Do not discard or redraw inconvenient replicates.

Define d_star=theta_star-theta_hat. Sort all B values. Use order statistic
indices floor(0.05*B) and floor(0.95*B), zero-based. The basic interval is
[theta_hat-q95(d_star), theta_hat-q05(d_star)]. Record its convention and both
endpoints; floating overflow anywhere refuses. A zero-width empirical interval
is DEGENERATE, not a confident positive result. Nonzero width does not establish
positive population variance. All outputs retain scoring_authorized=false.

Record input canonical hash, contract hash, implementation hash, Python/NumPy
versions, n, event count, L, B, seed, outcome disposition and interval. Random
streams use NumPy PCG64 with a separately recorded nonnegative integer seed.
Reject booleans as numeric values, malformed shapes and mismatched counts.
Original inputs and previous artifacts are never overwritten.

## Theory boundary

[Sharipov and Wendler, Theorem 2.1 and Remark 2.1](https://arxiv.org/pdf/0911.3083)
give conditional mean-bootstrap results under moment, mixing and growing-block
conditions, including a stated circular-block extension. Our growing L has
L->infinity and L/n->0, but that fact alone proves neither joint ratio validity
nor useful finite-n coverage. Independent review must check the joint extension,
delta-method transfer, centering, truncation and denominator remainder explicitly.
This contract does not claim the scalar theorem already proves our procedure.

## Proof sequence and compute ceiling

1. Separate review of this contract and mathematical boundaries.
2. Isolated helper plus deterministic tests, no market-report integration.
   Test event weighting, valid zero-event dates, circular pairing, exact length,
   basic-interval centering/sign, quantile indices, reproducibility, zero
   denominators, degeneracy, malformed/nonfinite inputs and immutable originals.
   Separate implementation review before stochastic calibration.
3. One frozen pilot, not a selection contest: existing nine model definitions
   at n=90 and365, null mean only, 20 fresh histories per cell (360 histories).
   Use a new named stream stage, never V2/V3/V4 seeds or history reuse. Existing
   missing/sparse refusal scenarios retain their refusal classification;
   complete zero-event calendar dates are not missing outcomes.
   Record all dispositions and failures. Pilot size is not certification.

Pilot execution must have a separate reviewed generator/stream manifest and
cost estimate. Limit foreground compute to ten minutes total; check budget
between histories, preserve partial results, and do not launch a full grid.
Do not claim hard interruption inside a history. No full confirmation is
authorized by this contract. A pilot failure is retained, not repaired by
changing constants against that same sample. A subsequent candidate would need
a separately justified prospective contract and distinct validation streams.

## Before any primary use

The accepted November10-February7 window and February15 12UTC not-before time
remain unchanged. Existing entry-day and 7/14/28-day intervals remain descriptive;
the registered all-ranges-positive condition is not silently replaced by this
candidate. Any mapping of this method into that gate needs an explicit reviewed
amendment before primary outcomes are inspected.

Require a complete mathematical argument, fresh locked confirmation with
declared error/power criteria, and an explicit market-assumption assessment.
Simulation success is model-family evidence, not market proof. Unsupported
stationarity, tails, denominator behavior, coverage or power yields INCOMPLETE.
No clipping, early return screening, background job, live trade, campaign,
account or schedule change is authorized. R05 remains INCOMPLETE.

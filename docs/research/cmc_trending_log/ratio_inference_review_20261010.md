# Event-weighted ratio: mathematical review boundary

Role: AUDITOR. Risk: HIGH research semantics.
Status: ACCEPTED_WITH_RISK for this source/derivation memo only, by separate
Hooke review and user approval. No blockers found; market assumptions remain
UNVERIFIED. Acceptance grants no method implementation or scoring authority.
No statistical method selected, implemented or certified.

## Target and conditional derivation

For a complete calendar, let S_d sum qualified event net excess returns on day d,
and N_d count those events. The descriptive event mean is sum(S_d)/sum(N_d).
A proposed population target under stationarity is theta = E[S_d]/E[N_d].
These are distinct: a fully observed historical mean needs no population
confidence interval to describe that history, but cannot alone prove future edge.

Two material model assumptions, neither established here:

1. The paired daily process is stationary and obeys a joint square-root-n central
   limit theorem with a finite long-run covariance matrix Sigma. Seven-day
   overlap alone does not imply dependence stops after seven days.
2. mu_N = E[N_d] is positive and the linearized long-run variance is positive;
   the moment/dependence conditions required by the eventual estimator hold.

Conditional on those assumptions, applying g(s,n)=s/n gives gradient
(1/mu_N, -theta/mu_N). The limiting variance of sqrt(n)*(theta_hat-theta) is

    V = (Sigma_SS - 2*theta*Sigma_SN + theta^2*Sigma_NN) / mu_N^2.

The corresponding large-sample estimator variance is V/n, not V itself.

Equivalently the linearized daily quantity is
(S_d - theta*N_d)/mu_N. It is not the unweighted daily average S_d/N_d;
zero-event days stay on the calendar. This is an algebraic delta-method
derivation, not a proof that market data satisfies its premises or a finite-n
coverage guarantee. The joint CLT includes the necessary mean convergence.

## What the sources actually support

[University of Washington large-sample theory notes, Delta Method section](https://faculty.washington.edu/yenchic/26A_stat581/Lec2_large.html)
provide the differentiable-transformation route conditional on a limiting
distribution. The ratio gradient and variance above are our explicit derivation.

[Sharipov and Wendler, Bootstrap for the Sample Mean and for U-Statistics of Mixing and Near Epoch Dependent Processes, Theorem 2.1](https://arxiv.org/pdf/0911.3083)
establish conditional consistency for a nonoverlapping block bootstrap of a
sample mean. Their assumptions include stationarity, moment/dependence
conditions, and block lengths growing while their fraction of sample size
vanishes. This is not a theorem about our existing paired ratio implementation,
fixed 7/14/28-day bands, missing endpoints, or ninety-day finite-sample accuracy.
A transfer to a joint ratio bootstrap still requires a separately reviewed
argument and exact resampling/centering/denominator specification.

## Engineering consequence

Keep the accepted complete-cohort audit and event-weighted descriptive mean.
Do not implement a nominal confidence gate from this memo. A future method
contract must bind its covariance or paired-bootstrap estimator, dependence
conditions, block rule, undefined-denominator handling, finite-sample validation,
power and refusal rules before primary outcomes are inspected.

Diagnostics can reveal conflicts with assumptions, not establish population
stationarity or finite moments. Regime changes, sparse counts, heavy tails and
missing outcomes remain substantive limits. V4's finite reference family does
not supply these premises. No return clipping, mean-of-day-means substitution,
fresh simulations, market scoring or schedule changes are authorized here.

The accepted prospective timing window is unchanged. R05 remains INCOMPLETE.
Original results, failed calibrations and study rules remain untouched.

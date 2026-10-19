# CMC market inference proposal: complete-cohort ratio reporting

Role: DIRECTOR. Risk: HIGH. Status: ACCEPTED_WITH_RISK for the bounded read-only
completeness-audit contract only, by separate Hooke review. Unknown-membership
clarification reviewed. Mathematical validity and market applicability are not
accepted; implementation requires its own review.
This is a design proposal, not an accepted statistical method, rule amendment,
implementation authorization, fresh experiment or market-scoring result.

## Preserve the question

For each eligible first appearance, r is the registered seven-day net return
minus matched BTC net return, using unchanged fees, quote qualification, identity,
endpoint and prior-history rules. The primary descriptive estimate is
sum of all eligible event returns divided by eligible event count. A daily mean
of means is not substituted. Equal-weight-day summaries are secondary only.

Represent every calendar entry day by the pair (S, N), where S sums its eligible
event returns and N counts those events. A valid observed zero-event day is
(0, 0), not missing. Resampling must move the pair together and compute
sum(S*)/sum(N*), preserving within-day dependence and variable event counts.
An all-zero resampled denominator is undefined; never silently discard it.

## Two explicit, unverified model assumptions

1. The eligible calendar-day (S, N) process is stationary and weakly dependent
   over the proposed reporting population, with dependence conditions sufficient
   for the chosen block-bootstrap ratio estimator. Regime shifts or unrestricted
   long memory invalidate transferring this interpretation to markets.
2. The required joint moments exist (including a finite 2+delta moment for the
   linearized ratio process for some delta > 0), with positive expected N and a
   nondegenerate long-run variance. Observed maxima do not establish tail bounds
   or these population moments. Extreme returns must not be clipped silently.

These assumptions are not established by the current CMC sample, a stationarity
test or V4. Independent mathematical review must specify sufficient conditions
for this exact ratio construction before conditional coverage can be claimed.

## Completeness before uncertainty

Only include a predeclared contiguous entry-date window for which all registered
seven-day endpoint windows have closed. Immature tail dates are excluded by
calendar cutoff, never by observed performance. Prior-30-day coverage must pass
for each eligible first appearance. Every date must have its valid list record.

Enumerate all eligible events and their outcome dispositions before computing
the estimate. If any eligible mature event lacks a qualified endpoint, return
INCOMPLETE_FULL_COHORT. Available-case summaries may remain descriptive but must
not stand in for full-cohort inference. This refusal avoids asserting missing
at random; it does not recover missing outcomes or make coverage complete.

Retain known ineligible events with explicit reasons outside the eligible
population. A failed quote is not automatically treated as an irrelevant event:
distinguish exclusion under the fixed entry rule from a missing required exit.
Unknown eligibility is a separate disposition, not known ineligibility. In
particular HISTORY_UNCERTAIN and AMBIGUOUS_FIRST_CAPTURE do not prove exclusion
from the eligible population. Any unresolved membership in the reporting window
prevents COMPLETE_FULL_COHORT, remains separately counted, and cannot be converted
to a zero-event (0, 0) calendar day. Missing valid list coverage likewise prevents
establishing a true zero-event date.

## Existing bands and what they cannot establish

Preserve entry-day and 7/14/28-day bands and the registered all-ranges-positive
condition. Report them as descriptive; this proposal does not certify their
fixed block lengths. Ordinary consistency results are asymptotic and require
conditions on block growth, not merely a fixed 28-day block or 90 elapsed days.
At least two blocks is an existing computational floor, not a power calculation.
Report actual mature calendar days, event days/counts and complete-cohort coverage.

No early success selection or repeated-look confidence claim. The current
90-day collection floor is retained, but it is not automatically a fixed primary
analysis date, 90 mature days or adequate power. A primary analysis date and any
permitted additional looks need explicit preregistration before inferential use.

## One bounded next implementation, if independently accepted

Implement only a read-only complete-cohort (S, N) audit and deterministic tests:
variable event counts preserve the event mean; zero-event dates remain on the
calendar; immature tail and missing list/endpoint cases are distinguished;
undefined denominators refuse; original outcomes cannot be overwritten.
Do not add a new confidence method, tune block lengths, inspect immature returns,
change gates or run another synthetic calibration in that slice.

This would remove data-definition ambiguity, not close R05. Further inference
needs a separately reviewed mathematical contract, fresh locked validation and
justified market applicability. If those cannot be established, retain descriptive
evidence rather than manufacture a nominal confidence label.

## Primary methodological sources

- Politis and Romano, The Stationary Bootstrap (1994): resampling theory for
  weakly dependent stationary observations; not unrestricted market dependence.
  https://www.tandfonline.com/doi/abs/10.1080/01621459.1994.10476870
- Lahiri, On the moving block bootstrap under long range dependence (1993):
  validity has restrictive conditions; long-range behavior cannot be ignored.
  https://www.sciencedirect.com/science/article/abs/pii/016771529390035H

Sources motivate limits; neither is claimed to prove this unimplemented ratio
procedure. No data, schedule, campaign, account or external document is changed.

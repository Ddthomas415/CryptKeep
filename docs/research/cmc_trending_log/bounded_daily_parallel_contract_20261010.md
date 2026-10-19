# Parallel Bounded Daily Study: Development Contract

Role: DIRECTOR. Risk: HIGH. Status: ACCEPTED_WITH_RISK by separate Hooke review,
development contract only. Formula, alpha spending, target and scope reviewed;
no mathematical blockers. Implementation requires its own independent review.
User authorized a parallel study, preserving the original study and artifacts.
This contract authorizes no execution, scheduling, scoring or promotion yet.

## Distinct Target And Preserved Evidence

Keep the original event-weighted seven-day net excess return study unchanged.
This parallel study instead asks whether a bounded, equally weighted daily
score has positive average conditional expectation over the declared window.
It is neither the original population mean nor executable portfolio profit.

Use the same prospective November10-February7 entry dates, preceding30day
coverage, identity exclusions, paired BTC observations, seven-day endpoint
qualification and fee rules as the original study. No earlier outcomes enter
this new primary dataset; no clipping threshold selection from returns.

For each complete UTC entry day d, preserve every raw net excess return r_di.
Define c=0.05, x_di=max(-c,min(c,r_di)). If N_d>0, X_d=sum(x_di)/N_d;
otherwise X_d=0, only when the day is verified to have zero eligible events.
All90dates remain, including zero-event dates. Thus X_d is in [-0.05,0.05].
This knowingly changes event weights and the treatment of extreme outcomes.
The 5-percentage-point cap is a prospective design choice, not a proven economic
optimum, a loss limit, or a trade order. Never replace or alter r_di in storage.

Alongside the score, report raw event-weighted mean, raw daily mean, event count,
zero-event count, clipped-event count, raw positive/negative tails separately,
and clipped-minus-raw contribution. A positive bounded result cannot override
negative raw economics or establish the original target's confidence condition.

## Exact Conservative Confidence Sequence

Let F_t contain the complete, ordered information released through maturity of
entry day t, including previously observed outcomes and publicly available
information. Only finalized day scores may enter the sequence. Set
mu_t=E[X_t | F_(t-1)] and M_t=(sum_{i=1}^t mu_i)/t. This is a changing,
history-conditional average; not a stationary population mean or future forecast.

For alpha=0.05, assign delta_t=alpha/[t(t+1)] for integer t>=1.
With range width w=0.10, define

    h_t = w * sqrt(log(2*t*(t+1)/alpha)/(2*t))
    L_t = max(-0.05, mean(X_1,...,X_t)-h_t)
    U_t = min( 0.05, mean(X_1,...,X_t)+h_t).

Conditional Hoeffding's lemma for an adapted bounded X_i yields
E[exp(lambda*(X_i-mu_i)) | F_(i-1)] <= exp(lambda^2*w^2/8).
Iteration and Chernoff optimization give
Pr(|sum(X_i-mu_i)| >= t*h_t) <= delta_t.
Summing delta_t over all t gives alpha because sum1/[t(t+1)]=1.
Consequently Pr(for all t, M_t in [L_t,U_t]) >=0.95, under this specified
filtration and complete bounded observations. No independence, mixing or
stationarity is imposed; the weaker conditional target is the price of that
generality. Missing outcomes, selective inclusion or return-dependent stopping
of the declared calendar cannot be silently converted into complete observations.

This is our conservative Hoeffding/union-bound derivation, not a claim to implement
Howard et al.'s sharper empirical-Bernstein construction. Their
[confidence-sequence paper](https://arxiv.org/pdf/1810.08240) supplies the general
time-uniform framework and explicitly distinguishes conditional-mean targets.
Separate review must verify this specific derivation and filtration mapping.

Implementation must represent chronological information at successive maturity
boundaries, not entry-time information or a retrospective release after viewing
all outcomes. Record the concrete maturity-boundary/receipt rule in the helper's
input contract before implementation review. Missing days must refuse, never
compress the calendar or select a favorable observed subset. The separate review
specifically identified this filtration mapping as a remaining implementation risk.

## Finite Window And Useful Limits

Retain the existing single-look/not-before boundary: February15,2027 at12UTC.
Anytime validity does not authorize early outcome inspection. At90complete days,
h_90 is approximately0.02656 (2.656 percentage points). A positive lower bound
requires the observed bounded daily mean to exceed that value. This deliberately
conservative design may be uninformative for modest edges; it does not promise
power or a pass. Positive conditional average still does not predict future profit.

Before implementation, review analytic width and the economic usefulness of this
cap/target. Do not run another broad Monte Carlo search: the stated coverage
claim rests on the proof, not favorable simulated histories. Any alternative
cap, target or sharper bound is a separate prospective contract, not a tuned
replacement after inspecting primary returns. Scoring_authorized remains false.

## Implementation Proof Required After Contract Review

Isolated helper only; no primary evaluator or gate integration. Deterministic
tests must cover clipping without raw mutation, zero-event versus missing dates,
day weighting, exact90day membership, finite values, t=1and90 width arithmetic,
interval bounds, counts and decomposition, source/input hashes and no authority.
All outputs visibly separate bounded score from raw returns and modelled PnL.
Independent implementation review is required before any dataset evaluation.

State outcomes: INCOMPLETE for missing/unqualified evidence; descriptive parallel
result otherwise. A positive interval is bounded-score evidence only, not original
study acceptance, portfolio readiness or promotion. Original R05 remains unresolved.

## Isolated Implementation Input Mapping

Development helper: scripts/research/cmc_bounded_daily.py. No CLI or live/archive
adapter. Input is a normalized COMPLETE_FULL_COHORT audit containing exactly90
ordered COMPLETE_DAY records. Each has eligible count, zero unknown/missing
counts, list-observed flag, list receipt time, maturity boundary, and individual
event IDs, raw net excess returns, paired-endpoint qualification and receipt time.
No events is permitted only on a complete observed zero-eligible day.

For entry date d, the deterministic chronological boundary is UTC midnight
d+8days plus12hours: it covers the latest entry that day, seven days and the
existing endpoint tolerance. All input evidence must have been available by
that boundary; the helper cannot attest truth of supplied receipts/qualification.
It reports qualification_verified=false and binds canonical inputs and source
hashes. F_t is chronological information available through this boundary, not
the later analysis-time dump. Missing historical availability must refuse an
upstream adapter; no retrospective timestamp manufacture is permitted.

Implementation status: ACCEPTED_WITH_RISK by separate Hooke review for isolated
helper and input mapping only. Fourteen deterministic tests pass locally and
independently; reviewer also verified overflow refusal, raw/tail decomposition,
range intersection and February15 12UTC maturity. No market dataset evaluated,
adapter integrated or scoring authorized. Supplied provenance remains unverified.

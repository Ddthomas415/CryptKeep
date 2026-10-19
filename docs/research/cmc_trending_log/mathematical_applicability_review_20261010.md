# Mathematical Applicability: CMC Mean Excess Return

Role: AUDITOR. Risk: HIGH. Status: ACCEPTED_WITH_RISK by separate Hooke review.
Reviewer verified construction, means, probability inequality, numerical bounds,
source limits and preservation of scope. No blockers; memo acceptance only.
Decision: current premises do not establish useful finite-sample primary
inference. Descriptive reporting remains valid; no replacement is certified.

## Conditional Route Is Not A Market Certificate

The accepted ratio memo correctly derives the delta-method variance conditional
on a joint central limit theorem, positive expected event count and positive
linearized variance. A multivariate/bootstrap transfer still requires its own
argument. Even completing that asymptotic argument would not demonstrate useful
coverage or power at90days, or establish its premises for CMC returns.

[Sharipov and Wendler, Theorem2.1](https://arxiv.org/pdf/0911.3083), pages5-6,
requires stationarity, a finite2+delta moment, specified summable dependence and
growing blocks whose fraction vanishes. Its conclusion is asymptotic. It does
not give this study a ninety-day error bound. The failed pilot supplies separate
negative finite-family evidence; it is not a theorem that every method fails.

## A Direct Finite-Sample Obstruction

The following is our explicit construction, not a market model or quotation.
Set N_d=1, so the ratio reduces to a mean. Under model P, S_d are independent
uniform observations on [0.009,0.011], with mean0.01. Under model Q, each day
independently draws from P with probability0.999 and otherwise returns -20.
Q has mean 0.999*0.01-0.001*20 = -0.01001.

Both are stationary independent processes with positive variance, positive
count and all finite moments. Thus merely stating finite moments and mixing
does not exclude the example. No shared numerical moment/tail bound is provided
by the current contract. The -20 is an excess-return example, not a permissible
loss on unlevered spot principal: a BTC-relative return difference can be below
-1 when the benchmark rises sufficiently. These values illustrate a missing
assumption, not an estimate of crypto tail probabilities.

For n independent days under Q, the probability no rare event appears is
(0.999)^n. Conditional on that event, the complete observed sample has exactly
the P distribution. For any rule A declaring a positive population mean,

    Pr_Q(A) >= (0.999)^n * Pr_P(A).

If that rule controls false positive probability at0.05 for Q, its power on P
cannot exceed 0.05/(0.999)^n: about5.471% at90days and7.204% at365days. This is a
bound for these two illustrative distributions, not a power estimate for the
registered study. It also holds for independently randomized rules by conditioning
on their randomization. No bootstrap choice can remove this information limit.

The calculation does not prove useful inference is universally impossible.
Known tail/moment bounds, a restricted justified model or a different target
could exclude Q. None has been justified for this primary contract. Clipping
returns or testing win rate instead would change the estimand; it is not an
authorized repair to the frozen mean-excess-return claim.

## Completed Review And Operational Consequence

The applicability review is complete with a negative finding about what is
currently justified. R05 primary method remains INCOMPLETE. Do not silently
reclassify the registered study as descriptive-only or remove its intended
capability: preserve the confidence gate as unresolved and scoring disabled.
At maturity the existing descriptive lane may report the observed complete
cohort without calling it proof of future profitability or a primary pass.

There is no justified replacement implementation to build now. A new contract
requires an explicit justified model restriction, or a user-approved change of
target, followed by independent theory review and fresh error/power validation.
Longer collection can help a particular justified model but cannot by itself
establish uniform guarantees over unrestricted finite-moment distributions.

Verification: deterministic arithmetic gives no-rare-event probabilities
0.9138900319 at90 and0.6940698870 at365days, power bounds0.0547111778 and
0.0720388551, and Q mean -0.01001. No Monte Carlo, outcome inspection, tuning,
source-code changes, schedule changes or scoring performed. Originals preserved.

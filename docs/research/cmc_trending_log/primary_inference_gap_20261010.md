# CMC primary inference: unresolved contract inputs

Role: AUDITOR. No inference method, gate or trading rule changed.

## Shown mismatch

`statistical_reporting_amendment_20261009.md` retains the registered seven-day
event-weighted mean net excess over BTC. The operator's gate decision requires
all four registered ranges above zero. V4 instead bounds a daily equal-weight
mean over a finite synthetic generator family. V4 is therefore not a drop-in
repair of the primary estimand, even apart from its poor tested power.

## Necessary next contract

A market-applicable method must explicitly specify the following before any
fresh validation or primary scoring:

- Preserve the event-weighted primary estimand; label day-weighted summaries as
  secondary rather than silently substituting them.
- State which serial dependence and nonstationarity assumptions support its
  uncertainty claim, and the refusal conditions when those assumptions cannot
  be supported. Synthetic family membership is not market evidence.
- State the minimum eligible entry days/events and the handling of missing
  outcomes. Available-case intervals are not full-cohort uncertainty under
  informative missingness.
- Keep existing identity, quote, fees, timing, coverage and all-ranges gate rules
  intact unless an explicit operator decision authorizes an amendment.
- Register one candidate, a cost bound and independent review before fresh
  validation; do not tune against the closed V2/V3/V4 confirmation results.

No numerical thresholds or market-process assumptions are invented here.
This is a contract-input audit, not statistical certification. Separate reviewer
Hooke returned ACCEPTED_WITH_RISK for this audit only, with no exact-claim
blockers. The next contract must also specify scale/tail restrictions, eligible
population, confidence claim and repeated-look policy. Sample counts alone
cannot establish validity. Primary scoring remains
disabled; mature forward observations are still required.

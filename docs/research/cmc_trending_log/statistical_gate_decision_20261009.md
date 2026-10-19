# Operator decision: CMC primary gate rule (pre-scoring amendment)

Recorded 2026-10-09 ~11:05 UTC by Claude (cloud session) from Damian's explicit answer. No outcomes have been
scored or viewed; the earliest primary cohort day is 2026-11-08 and scoring cannot start before 90 qualified days.

Decision: "All ranges above zero". The 7-day primary passes its statistical condition only if the registered
entry-day 90% range AND each of the 7-, 14- and 28-day calendar-block 90% ranges are entirely above zero.
Any block range that is INCOMPLETE, INSUFFICIENT_DAYS or MISSING_CALENDAR_COVERAGE means the condition is NOT met.
This only tightens the registered gate; fees (1.2%/side), horizon, timing and coverage rules are unchanged.

Reason: review_statistical_reporting_20261009.md, finding 1 - under persistent day-to-day dependence the
entry-day range alone excluded a true zero mean in ~61% of synthetic null histories (nominal 10%).

Still owed by the implementing session before scoring (not decided here): 7-day missing-outcome status counts in
the statistics block; a pre-registered minimum number of entry days/events. cmc_statistics.py currently computes
no gate verdict (scoring_authorized False); implementing this rule is the author's work and needs separate review.

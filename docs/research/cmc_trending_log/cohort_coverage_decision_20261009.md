# First-appearance coverage decision

AUDITOR. Registered event: first hidden-boost top-100 appearance within a
30-day window. No evaluator implementation or scoring performed here.

SHOWN: observations began October 9, with multiple manual captures and a daily
schedule. Startup and missed observations cannot prove absence from the list
over the preceding 30 days. Identity qualification alone does not repair this.

Recommendation, pending operator decision: classify startup/gap-affected events
as HISTORY_UNCERTAIN and retain them for separate diagnostics. Require one valid
hidden-list observation on every preceding UTC calendar day for 30 days before
qualifying a first-observed event for the primary cohort. This is daily sampled
absence, not proof of continuous intraday absence. Multiple manual observations
must not increase the daily event count or supply independent samples.

Alternative: count first observed appearances immediately and label the study
as a first-observed signal rather than confirmed 30-day first appearance. This
changes the operational interpretation of the registered event.

No choice is silently implemented. Endpoint tolerance remains approved at
plus/minus 12 elapsed UTC hours. Original fees and primary 7-day target remain.
Operator chose required 30-day coverage. Separate helper
`scripts/research/cmc_cohort_coverage.py` implements the approved classification
using already validated daily lists. Startup/gaps stay HISTORY_UNCERTAIN; any
observed prior appearance stays REPEAT_APPEARANCE. Candidate status is not
scoring authorization. Five tests pass. READY_FOR_INDEPENDENT_REVIEW.

## Operator decision (2026-10-09 ~06:00 UTC, recorded by Claude cloud session)

Damian chose the recommended option: a first appearance qualifies for the PRIMARY cohort only after one valid
hidden-list observation on every preceding UTC calendar day for 30 days (daily sampled absence). Startup- or
gap-affected appearances are classified HISTORY_UNCERTAIN and kept for separate diagnostics, not dropped.
Earliest possible primary-cohort entry: 2026-11-08 UTC, if no daily observation is missed. A missed day
resets eligibility for coins whose 30-day window includes it. Multiple runs on one day count as one day.
This decision is recorded only; no evaluator was implemented and nothing was scored.

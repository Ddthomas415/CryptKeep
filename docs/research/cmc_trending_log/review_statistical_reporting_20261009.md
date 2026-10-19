# Independent review: R05 statistical reporting (cmc_statistics.py + amendment)

Reviewer: Claude (cloud session), separate from the author. 2026-10-09 ~10:50 UTC. No code edited.
Reviewed (sha256): scripts/research/cmc_statistics.py 4d2eef94...; scripts/research/run_cmc_diagnostic_report.py
55e44f44...; statistical_reporting_amendment_20261009.md (10:42). Also read cmc_diagnostic_evaluator.py,
cmc_return_math.py (paired_excess, 1.2%/side default), cmc_daily_cohorts.py, cmc_cohort_coverage.py.
Tests: tests/test_cmc_statistics.py + tests/test_run_cmc_diagnostic_report.py -> 7 passed (matches amendment).
Probes: review_statistical_reporting_20261009_probe.py (read-only, synthetic data, 20 s). No real outcomes read.

## Verdict: CHANGES_REQUIRED before any gate decision (ACCEPTABLE as diagnostic-only today)

Nothing can be scored before ~2027-01 (90 collection days; first primary cohort day 2026-11-08), and the code
always returns scoring_authorized False, so there is no live harm. But the amendment's stated rule - the gate stays
on the registered entry-day bootstrap and "sensitivities do not replace or loosen the gate" - would let the least
dependence-robust interval decide. That must be settled before scoring, which is what item 5 asks.

## Confirmed correct
- Not-ready refusal before 90 days; INSUFFICIENT_ENTRY_DAYS below 2 days; repeats < 100 refused.
- Only status DIAGNOSTIC at horizon 7 enters; NaN raises; bool raises. Deterministic (seed 20261009, rng re-created
  per interval; identical output across runs - probe 1).
- Entry-day clustering works: same-day events resampled together (test + probe).
- Event days must be inside observed days; non-contiguous calendar refuses sensitivities; any empty replicate ->
  INCOMPLETE (probe 4: 3 sparse event days -> all three sensitivities INCOMPLETE; conservative, as documented).
- 7-day primary objective and 1.2%/side registered fee preserved; 1-day and 30-day outcomes are not pooled in.
- Same coin cannot overlap itself at 7 days: a re-entry needs 30 prior days absent (classify_appearance).

## Findings
1. HIGH - registered primary interval is anti-conservative under the dependence this design creates.
   Consecutive entry days hold overlapping 7-day windows (6 of 7 days shared), so day-level excess returns are
   serially correlated. Probe 8, 150 synthetic histories with true mean 0, 3 events/day, 61 event days, nominal 90%:
   | day-level shared drift | entry-day (primary) | 7-day blocks | 28-day blocks |
   |---|---|---|---|
   | independent (phi 0) | 92% | 86% | 68% |
   | persistent (phi 0.85) | 39% | 71% | 60% |
   With persistence the primary range excludes zero in ~61% of null histories. A gate on the primary alone would
   be easy to fool. Required (operator decision, pre-scoring amendment): either gate on ALL reported intervals being
   above zero (only tightens; my recommendation), or make the 7-day block the registered primary. Also note 28-day
   blocks over ~91 days give ~3 blocks per replicate and undercover even without dependence - label them unreliable
   or require more days.
2. MEDIUM - missing outcomes are invisible in the statistics block. Probe 3: 61 DIAGNOSTIC + 549 MISSING 7-day rows
   -> summary reports events 61 and nothing else. The report's status_counts mixes horizons 1/7/30. Required: in
   summarize, count 7-day primary candidates by status (DIAGNOSTIC / MISSING / INVALID_ENTRY_QUOTE / IMMATURE ...)
   and the DIAGNOSTIC share, so selection by data loss is visible next to the mean.
3. MEDIUM - no pre-registered minimum sample. Probe 5: two entry days produce status DIAGNOSTIC with a "90% range"
   0.20..0.30. Required: register a minimum (entry days and events) below which the result is INSUFFICIENT.
4. LOW-MEDIUM - point estimate is event-weighted. Probe 2: one day with 20 events at +50% and 59 days at -1%
   -> mean +11.75% (day-weighted -0.15%). This is consistent with the stated target (mean over events) but one
   burst day can dominate. Recommend reporting day-weighted mean and the largest single-day share of events.
5. LOW - block starts are not circular (edge days drawn less often) and sensitivities run over the 30 warm-up days
   where no primary event can exist; both waste information but do not bias toward profit. Optional.
6. LOW - None/str excess_return raise TypeError, not the ValueError the code intends; unreachable from the
   evaluator today. Optional.
7. NOTE - percentiles are order statistics 101 and 1901 of 2000 (index int(n*.05), int(n*.95)); acceptable,
   state it in the amendment.

## Not in scope / unchanged
Quote qualification (R03), unattended schedule (R07, still UNVERIFIED in the report), and execution realism
remain open; this review does not accept profitability or executability.

## Re-check against the 10:45-10:46 revision (same day, ~10:58 UTC)
New sha256: cmc_statistics.py a9707cab...; run_cmc_diagnostic_report.py 312da745...; cmc_daily_cohorts.py
77793df7...; amendment updated 10:46 (re-review requested). CMC regression on this machine: 103 passed
(tests/test_cmc_*.py + test_run_cmc_diagnostic_report.py + test_report_cmc_readiness.py).
- Accepted: collection clock now starts at the first valid, nonempty listed observation
  (qualified_collection_start_utc, set after the unusable/invalid/no-listing exclusions); regression
  test_failed_early_capture_does_not_start_collection_clock pins it.
- Statistics math is unchanged; only limit labels were added. Probe rerun on the new file reproduces the same
  numbers (primary 92%/39% coverage; 7-day blocks 86%/71%; 28-day 68%/60%).
- Finding 1 (HIGH, gate rests on primary alone): OPEN - needs the operator's pre-scoring decision.
- Finding 2 (missing outcomes): PARTLY addressed - now labeled as a limit, but 7-day status counts are still not
  in the statistics block. Labels describe the gap; counts would measure it.
- Finding 3 (no minimum sample): OPEN. Finding 4 (event weighting): OPEN, recommend reporting only.
Verdict unchanged: diagnostic-only ACCEPTABLE; CHANGES_REQUIRED before any gate decision.

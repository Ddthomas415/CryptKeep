# CMC statistical method v3 - NEW EXPERIMENT PLAN (draft; nothing runs until Damian approves)

Author: Claude (cloud session), 2026-10-09 ~22:16 UTC. The v2 confirmation result NO_CERTIFIED_SAMPLE stands and is not
re-tuned: the 28-day block method, its seeds and thresholds are closed. This is a separate, pre-registered experiment
with new candidates, new seeds and the same certification bar.

## Why v2 failed (from confirmation_result_v2_20261009.md)
Every supported null cell exceeded the pointwise Wilson-upper 7.5% tolerance (74-95 false positives per 1000 at
365 days); power criterion met only under iid. Percentile block bootstraps of an event-weighted mean are known to
under-cover with overlapping 7-day returns and few effective blocks; one burst day also dominates the event mean.

## Proposed changes (each must be approved before any code or run)
1. Estimand (operator decision): day-weighted mean of the daily equal-weight cohort excess return (each entry day
   counts once), reported next to the registered event-weighted mean. Removes burst-day dominance.
2. At most three candidates, fixed before development, no tuning afterwards:
   A. HAC t-test with fixed-b critical values (Kiefer-Vogelsang, Bartlett kernel, bandwidth b=0.2*n), one-sided 5%.
   B. Studentized circular block bootstrap of the day-weighted series, block 14 days (2x the 7-day overlap),
      2000 resamples, one-sided 5% on the studentized statistic.
   C. Non-overlapping weekly reference: one pre-declared weekday's cohorts only, ordinary one-sided t-test
      (lower power, but overlap-free by construction).
3. Same synthetic grid and certification as v2 (9 models x 3 lengths x 4 means = 108 cells; supported/refusal-only
   split unchanged; pointwise Wilson-upper <= 7.5% on every supported null cell; power criterion unchanged),
   with NEW named seed streams recorded before generation. Development on the 12 v2 development cells only,
   10 histories each, deterministic selection rule (lowest worst-cell false positives; ties C, then B, then A).
4. If no candidate passes: report NO_CERTIFIED_SAMPLE_V3 and stop. Any further attempt needs another new contract.
5. Gate wiring unchanged in spirit: operator rule "every reported range above zero" applies to the certified
   method's interval in both registered and quote-qualified views; uncertified intervals stay descriptive.

## Cost / time
Pure synthetic computation on the laptop (v2 took 144.75 s for 108,000 histories); no market data, no collectors.
Implementation + independent review + confirmation run: one bounded session.

## Decisions needed
(1) approve or change the day-weighted estimand; (2) approve candidates A/B/C; (3) approve running development
and confirmation under the v2 certification bar.

## HOLD before implementation (Claude, 2026-10-09 ~23:04 UTC): the approved power bar is unattainable by ANY method
Check: oracle_power_bound_20261009.py (4,000 histories per cell, seed 20261009; the test KNOWS the true long-run
variance, so no real method can beat it). Contract volatility sigma = 0.03, one-sided 5%:
| model | 90 d | 180 d | 365 d | days for 80% power at 0.5% | smallest mean detectable at 80% in 365 d |
|---|---|---|---|---|---|
| iid | 47% | 73% | 95% | 223 | 0.39% |
| overlap7 | 14% | 21% | 33% | 1,558 (~4.3 years) | 1.03% |
| persistent (0.85) | 10% | 15% | 23% | 2,745 (~7.5 years) | 1.37% |
Null rejection of the oracle is 4.4-5.1% (correct size). So the contract's "80% power at 0.5% in every supported
scenario" fails for every dependent model at every allowed length no matter which method is chosen; v2's power
failure was mostly structural, not a method defect. v2's SIZE failure (7.4-9.5% false positives) is a method defect
and is fixable. Running v3 unchanged would produce NO_CERTIFIED_SAMPLE_V3 by construction.
Options for Damian: (1) certify SIZE only (false positives within tolerance on every supported null cell) and report
power as the sample length/effect size needed; (2) keep the power bar but at a 1% target and 365 days (overlap7
oracle 78% - still marginal); (3) stop method work and treat the CMC study as descriptive only.

## OPERATOR DECISION + IMPLEMENTATION (2026-10-09 ~23:07 UTC)
Damian chose size-only certification: pass = on every supported null cell (6 models x 90/180/365 days) all 1000
histories available and Wilson-95% upper false-positive rate <= 7.5%; refusal-only models must refuse every history.
Power is reported per alternative cell, not required. Day-weighted estimand. Candidates A/B/C as above.
Code: scripts/research/cmc_calibration_v3.py, scripts/research/run_cmc_calibration_v3.py, tests/test_cmc_calibration_v3.py
(7 tests, incl. generator identical to v2 under a v2 label and new seeds under v3 labels).
Development run (12 cells x 10 histories x 3 methods): worst-cell false positives C=2, B=1, A=2 -> LOCKED
B_studentized_circular_block14 (research/research_corrections_20261009/cmc_calibration_v3/lock_v3.json, with module and
runner hashes). Confirmation refuses to run until the code hashes match the lock AND review_accepted_v3.txt exists
(written only after an independent review). Status: READY_FOR_INDEPENDENT_REVIEW. No confirmation seeds touched.

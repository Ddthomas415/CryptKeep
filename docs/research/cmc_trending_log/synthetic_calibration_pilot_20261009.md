# Synthetic calibration pilot

Bounded prereal-outcome pilot:60/180 consecutive entry days,30 independent seeded
histories per scenario,100 bootstrap replicates per history. Null models: iid
Gaussian, literal overlapping seven-shock means, stationary AR(1) withphi0.85.
One event per day, no gaps or missingness; all true expectations are zero.
The study calls the existing diagnostic statistics without changing their rules.

False-positive counts (lower90% interval bound above zero), each out of30:

| Days | Null model | Entry-day | All four intervals positive |
| --- | --- | --- | --- |
|60|iid|5|4|
|60|overlap7|10|4|
|60|persistent|10|4|
|180|iid|2|2|
|180|overlap7|9|3|
|180|persistent|10|5|

These small Monte Carlo samples have wide uncertainty; the output includes
Wilson95% ranges for every count. No method or sample length is certified by
this pilot. Requiring all intervals positive is not demonstrated to control
false positives, particularly with persistent returns. Calendar length alone
cannot establish an adequate sample requirement. No alternative-power assessment,
missingness, variable daily coin counts or regime shift was tested.

Result: keep primary pass/fail scoring disabled. A larger independently reviewed
calibration and power contract is needed before choosing a gate or minimum sample.
No mature market outcomes accessed, parameters optimized or frozen rules changed.

Artifact: research/research_corrections_20261009/cmc_synthetic_calibration_v1.json
It records script/statistics hashes and all six scenarios. Seven targeted tests
passed; the180-history pilot completed. Acceptance: READY_FOR_INDEPENDENT_REVIEW.

# Calibration execution checkpoint

Measured on the laptop using the current diagnostic implementation, one synthetic
overlap7 history per length with2000 resamples. This is a workload benchmark,
not statistical calibration; single measurements are noisy.

| Entry days | Seconds/history | Projected minutes/1000 histories |
| --- | --- | --- |
|90|1.02|17.0|
|180|0.78|13.1|
|365|1.42|23.7|

Even one scenario over all three lengths projects approximately54 minutes. The
complete proposed grid would take substantially longer. Do not start it with the
current implementation as an open-ended run. Benchmark artifact:
research/research_corrections_20261009/cmc_calibration_runtime_checkpoint_v1.json

Independent design review returned INCOMPLETE despite recorded human acceptance
of the direction. It identified unfrozen distributions, dependence strengths,
event-count/missingness equations and supported/refusal-only combinations; an
exact grid and development trial cap are required. The proposed Wilson-upper
7.5% criterion permits58/1000 false positives and cannot certify a5% maximum.
Pointwise versus simultaneous certification must also be stated explicitly.
Survivor returns cannot identify full-cohort means under loss-dependent missingness.

Execution limit for the next implementation stage: at most60 seconds per benchmark
batch and10 minutes total measured compute before a new checkpoint. No full
confirmation grid, silent background job or repeated full-suite run is authorized
by this checkpoint. Preserve results and stop on budget exhaustion or source-hash
change. Full-grid runtime remains unapproved and no full-grid run has started.

Next: freeze exact scenario equations and certification scope, then benchmark a
bounded candidate implementation. Any revised acceptance criterion is a visible
contract amendment requiring review, not a silent rewrite of the accepted design.

Acceptance: ACCEPTED_WITH_RISK for observed runtime measurements only; calibration
design completeness and primary scoring remain INCOMPLETE.

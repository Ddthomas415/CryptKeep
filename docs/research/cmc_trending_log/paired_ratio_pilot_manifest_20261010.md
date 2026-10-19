# Paired-ratio pilot: streams, budget and locked screening rules

Role: DIRECTOR. Risk: HIGH. Status: READY_FOR_INDEPENDENT_REVIEW.
This authorizes a bounded synthetic pilot after separate runner and budget
review, not a full confirmation, power study, method selection or market scoring.

## Exact trials

Reuse cmc_calibration_v3.generate unchanged, SHA256
26fb3ce192f93416f215d1c8ec2e3f7bb39489ac85c9b1f20ebc7843858369d4.
Nine existing models, lengths90/365, mean_index0 (null), trials0..19:360 histories.
No alternative means, parameter search, additional trials or substituted cells.
Six original supported models are computational candidates; volatility_shift is
a stress case outside the stationary inference premise. The three original
refusal-only models retain that policy. Model classes are not changed by results.

New stages: paired_ratio_benchmark_20261010 and paired_ratio_pilot_20261010.
Benchmark uses one trial per supported model/length, separate from all pilot
streams. Canonical stream encoding and SHA256 first16-byte PCG64 seeds are the
existing generator's unchanged functions, with the new stage explicitly allowed.
For each history, generate its named innovation/count/missingness/event-noise
streams independently; use its bootstrap stream for the candidate's PCG64 seed.
Record structured identifiers and enumerate seed uniqueness over this manifest.
Earlier stage names development,confirmation,benchmark,v3_development,
v3_confirmation,v4_reference_20261010,v4_confirmation_20261010 are forbidden.
Distinct namespaces prevent deliberate reuse; hashing is not a mathematical
claim that collisions are impossible. Refuse any observed seed collision.

## Adapter and refusal

For supported models, enumerate every generated event and observed disposition
on the full declared calendar and call the accepted completeness helper. Never
use day_series (it changes weights). Known missing outcomes stay missing.
Refusal-only model policy returns REFUSED without computing an interval; retain
that policy explicitly, not as evidence that sparse complete calendars are
necessarily missing. Valid zero-event dates remain distinct from missingness.
Every attempted pilot trial is recorded, including unavailable and failed ones.

## Locked pilot screen, not certification

Positive means CANDIDATE_INTERVAL with lower bound>0. Each supported cell must
produce20 candidate intervals. Flag a supported cell if more than2/20 are
positive or any interval is unavailable. Require20/20 REFUSED per refusal cell.
Report all cell rates and existing Wilson95 bounds, including flags. At20 trials
these bounds cannot certify a5% error rate; absence of flags is SMALL_PILOT_ONLY.
Any flag is PILOT_SCREEN_FAILED, not proof about real market profitability.
The full observed rates matter more than the coarse screening label. No power
claim is possible because the pilot contains null means only.

Do not tune the method if it fails. Preserve this candidate and all artifacts.
No full confirmation is authorized, whether the pilot passes or fails.

## Cost gate and evidence

Runner/adapter/stream-manifest review must precede benchmark generation.
Benchmark12 histories; report durations only, not interval outcomes used for
selection. Project pilot cost by20times each matching supported-cell duration,
sum, and multiply by2 safety factor. Add10seconds for refusal/logging overhead.
Require projection<=600seconds and separate review of the benchmark receipt
before pilot. Stop otherwise rather than asking the machine to run indefinitely.

Pilot foreground wall budget600seconds, checked between histories. Persist each
trial once with exclusive file creation; resume only exact matching identities
and identifiers, validate the exact18-cell/360-history grid before aggregation.
Cumulative recorded history durations count against the budget across resumes;
benchmark durations also count against the shared600second compute ceiling.
Ordinary evaluation failures are persisted as FAILED_ATTEMPT with elapsed cost;
the run stops and resume cannot retry those identifiers. Failed benchmark
receipts stop further generation too. Process termination or storage failure
can still prevent saving an attempt; exactly-once across those failures is not
claimed and requires an operator investigation rather than an automatic retry.
the budget is not a hard interrupt inside a history. Reject mixed hashes, duplicate
or misnamed trials and incomplete grid. No background process or automatic retry.

Pin candidate contract, pilot manifest, generator, completeness helper, calculator,
runner, Python and NumPy identities; review acceptance and budget gate must match.
Results remain scoring_authorized=false. No market data, originals, campaigns,
accounts, schedules, logger or prior calibration artifacts are changed.

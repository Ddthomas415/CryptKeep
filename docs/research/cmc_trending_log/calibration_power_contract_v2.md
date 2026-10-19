# Calibration contract v2: exact grid amendment

Status: ACCEPTED_WITH_RISK by explicit human acceptance. This amends v1 explicitly; v1 and its human
acceptance remain preserved. No method, minimum market sample or CMC gate certified.

## Exact grid and estimand

Lengths90/180/365 UTC days crossed with means0/0.0025/0.005/0.01 and the nine
models below produce108 cells. Null:27 cells; alternatives:81 cells. Six models
are supported candidates; sparse, random-missing and loss-dependent-missing are
refusal-only in this first version. Refusal-only results cannot certify inference.
The target is the event-weighted mean excess return over all generated events,
before observation losses. No post-result reclassification of model support.

For every history use independent standard-normal draws Z and independent U(0,1)
draws U from named generator streams. Generate n+6 innovations for overlapping
returns. Common volatility sigma=0.03; add the declared mean mu only after all
zero-mean shocks are generated. Daily index t starts0; all events share their day.

1. iid: one event/day, r[t]=mu+sigma*Z[t].
2. overlap7: one event/day, r[t]=mu+sigma*sum(Z[t:t+7])/sqrt(7).
3. persistent: one event/day, X[-1]~N(0,sigma²); X[t]=0.85*X[t-1]
   +sigma*sqrt(1-0.85²)*Z[t]; r[t]=mu+X[t].
4. heavy-tail overlap: replace each Z in overlap7 by T5*sqrt(3/5), where
   T5=Z/sqrt(sum(V[j]² for j=1..5)/5), with independent normal V.
5. volatility shift: overlap7, innovation scale sigma beforefloor(n/2) and
   3*sigma afterward; use each innovation's own scale inside the overlapping sum.
6. shared unequal events: base daily shock as overlap7; event count20 on day
   floor(n/2), otherwise1. r[t,j]=mu+base[t]+0.01*independent Z[t,j].
7. sparse (refusal-only): generate overlap7, retain events only when independent
   U[t]<0.2; absence is recorded, not a zero return.
8. random missing (refusal-only): generate overlap7; hide20% of event outcomes
   using U[t]<0.2. Keep full generated truth in synthetic evaluation only.
9. loss-dependent missing (refusal-only): generate overlap7; hide an outcome with
   probability0.8 when r[t]<0, otherwise0.1. Mark known missingness explicitly.

Models have different dependence/volatility by design; no retrospective matching
to CMC observations. These are synthetic support assumptions, not observed facts.

## Methods and development ceiling

At most three candidates: current entry-day bootstrap reference, calendar moving
block bootstrap with fixed28-day blocks, and calendar moving block bootstrap with
fixed56-day blocks. No block-length search. References may fail; retain results.
Refusal-only cases require refusal of primary inference, not survivor intervals.
The registered entry-day calculation remains diagnostic and is not rewritten.

Development cells: six supported models at lengths90 and365, mean0 only:12 cells.
Ten histories per cell per method: maximum360 method-history evaluations.
No alternatives or confirmation seeds during development. Select one method by
the lowest worst-cell false-positive count; ties choose56-day, then28-day, then
entry-day. Require at least one available result per supported cell, otherwise
NO_METHOD_LOCKED. This is a deterministic screening rule, not certification.
Availability correction: filter out any method with no available result in any
required development cell BEFORE ranking. If no methods survive, NO_METHOD_LOCKED.
Lock the method and implementation hash in an immutable artifact before confirmation.

Block candidates inherit noncircular contiguous starts chosen uniformly, append
blocks until n days are drawn, truncate the last block to n, and pool selected
events to calculate the event-weighted mean. Require n>=2*block. Empty resamples
make the interval INCOMPLETE, not silently discarded. For B resamples, sorted
percentile indices arefloor(0.05*B) andfloor(0.95*B), as in the diagnostic method.

## Certification meaning and trial accounting

Preserve v1's empirical target5% and pointwise Wilson95% upper tolerance7.5%.
Call a pass POINTWISE_SIMULATION_TOLERANCE_MET, never certified error<=5%.
58/1000 can pass the tolerance; that fact must be prominent in the final report.
All required cells must pass, with no averaging. No simultaneous confidence claim
across cells or lengths is authorized by pointwise Wilson intervals.

Confirmation:1000 histories per cell for the one locked method,108000 total.
If resampling is used,2000 resamples/history. Null false-positive denominator is
all1000 histories; separately report abstentions. Supported alternative power
requires empirical>=80% and Wilson95% lower>=75% atmu0.005; the lower condition
is retained for compatibility though redundant at this trial count. Do not count
abstentions as power successes. Report all other means. Refusal-only models require
100% primary refusal; no inference certification from that refusal.

Shortest length meeting supported null and target-power criteria may be reported
as a synthetic candidate length only. None passing means NO_CERTIFIED_SAMPLE.
Neither outcome sets a real-market minimum or changes frozen CMC scoring.

## Seeds, compute and checkpoints

Development history seeds1000000+10000*model_index+1000*length_index+trial.
Confirmation history seeds3000000+10000*model_index+1000*length_index
+100*mean_index+trial, where trial0..999. Each history uses a structured identifier
(stage,model,length,mean,trial); derive stream seeds with SHA256 of that identifier
and the stream name. Structured identifiers are authoritative: arithmetic seed
collisions must not merge streams. Names:innovations,event_noise,counts,missingness,
bootstrap,heavy_tail_denominator. Confirmation and development identifiers cannot overlap.
Canonical stream encoding is compact ASCII JSON of the list
[stage,model_name,length,mean_index,trial,stream_name], with separators(',',':').
Take the first16 bytes of SHA256 as an unsigned big-endian integer seed for
NumPy PCG64. Record NumPy version; any generator/version change requires new hashes.

Before development, benchmark one history per length/model on synthetic inputs,
at most60 seconds per batch and10 minutes aggregate compute. Publish projected
development and108000-history costs. Stop if projected confirmation exceeds one
hour; obtain a new execution-budget decision rather than launching it.
No full confirmation is authorized by this contract without that checkpoint.
Resume immutable per-cell files only when contract/method/config hashes match;
reject duplicates or mixed hashes. Preserve partial results on budget exhaustion.

No mature data access, background job, frozen strategy change, or scoring activation.
Human acceptance was explicitly supplied after the design handoff. Implementation
must retain the runtime checkpoint and obtain separate review before confirmation.

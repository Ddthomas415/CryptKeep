# Candidate interval implementation checkpoint

Three isolated synthetic candidates now implement the fixed entry-day,28-day and
56-day moving-block methods. Event sums and counts preserve event-weighted means;
noncircular starts, final-block truncation and percentile indices follow v2.
Resampling batches are bounded to128 histories. Unsupported models refuse and
missing outcomes never become survivor-only inference. Existing CMC scorer unchanged.

Verification:7 targeted model/interval tests passed. A scalar-reference fixture
matches vectorized block28 percentile endpoints on unequal daily event counts.
Constant outcomes, determinism, short-sample refusal and missingness covered.

Benchmark:81 method/model/length cells at2000 resamples completed in0.106 seconds
aggregate measured interval time. Simple108000-history projections: entry-day162s,
block28 141s,block56 122s. These are single-observation estimates, excluding
generation, artifact I/O, checkpointing and runtime variation, not guarantees.
Artifact: research/research_corrections_20261009/cmc_interval_runtime_checkpoint_v1.json

Proposed full-stage budget:10 minutes measured compute, checkpoints after each
development cell and each100 confirmation histories; stop/resume immutable parts.
No confirmation has started and no method locked. Separate implementation review
precedes development/confirmation. Timing does not prove calibration or power.

Acceptance: READY_FOR_INDEPENDENT_REVIEW.

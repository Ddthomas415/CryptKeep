# Frozen synthetic confirmation result

Status: ACCEPTED_WITH_RISK by explicit human acceptance. Result: NO_CERTIFIED_SAMPLE.
The accepted28-day method ran108000 synthetic histories across108 cells, with
2000 resamples where inference was permitted. Runtime144.75 seconds, below the
600-second between-chunk cap. All1080 immutable100-history checkpoints retained.
Earlier interrupted v1 remains separately preserved and unaccepted.

| Entry days | Supported null cells failing tolerance | Target-power cells failing |
| --- | --- | --- |
|90|6 of6|6 of6|
|180|6 of6|6 of6|
|365|6 of6|5 of6|

At365 days, false-positive counts range74–95 out of1000 histories across supported
nulls. Every supported null cell fails the declared pointwise Wilson-upper7.5%
tolerance. Target-power successes range226–939 of1000 at0.5% net excess; only iid
meets the power criterion. Unsupported sparse/missingness models refuse inference;
that refusal is not evidence of adequate power or real-world error control.

This is a negative methodological result, not a negative trading-profit finding.
No market data was accessed. It does not prove another method cannot work or set
a universal minimum sample. No method/threshold changed after confirmation.
Any further method development requires a new contract and new confirmation seeds.

Evidence: research/research_corrections_20261009/cmc_confirmation_summary_v2.json
and cmc_confirmation_v2/. Summary records frozen source/lock hashes and NumPy2.4.4.
The bounded v2 runner corrections were separately accepted WITH_RISK;13 targeted
tests were reproduced by the reviewer before this run. Human acceptance of the
result is recorded; no additional independent result verification is inferred.
CMC primary scoring remains disabled; diagnostics and data collection continue.

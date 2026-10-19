# Statistical v3 independent review

Role: AUDITOR. Acceptance: INCOMPLETE. Environment: VERIFIED_ENV.
Scope: synthetic calibration implementation and confirmation evidence contract, not profitability.

## Blocking finding

`run_cmc_calibration_v3.summarize()` requires only 108 files. It does not require the exact unique 9-model x 3-length x 4-mean grid, validate each part's lock hash, or validate counts and identifiers. The refusal criterion passes vacuously when there are no refusal cells.

SHOWN by an in-memory probe (no output files): 108 duplicates of a single iid/90-day/null cell, each carrying a wrong lock hash, produce `SIZE_TOLERANCE_MET_POINTWISE`. Thus missing supported scenarios, missing refusal tests and mixed-lock artifacts can be reported as certification.

Required correction: enforce exact unique expected cell identities, expected means/history counts, valid nonnegative integer counters and complete status totals, matching lock/code identities and complete supported-null/refusal sets before evaluating tolerance. Existing confirmation files must be validated before resume skips them. Summarization must reject changed sources as well as confirmation execution. Preserve original development artifacts; any source change requires an explicit new lock/provenance record rather than silently accepting the old lock.

## Additional reproducibility gap

The development lock names two source hashes, but does not bind the plan or NumPy runtime. Existing-file resume skips content validation. Record and enforce the full experiment identity and runtime before confirmation/resume/summary, with regression probes for changed or malformed evidence. A text-file existence check is not hash-bound independent acceptance.

## Verification and limits

`./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_cmc_calibration_v3.py`: 7 passed.
The duplicate-grid/wrong-lock probe reproduced the blocker without generating confirmation histories or accessing market data. No confirmation acceptance file written; no confirmation run, scoring or original artifact mutation.

This is not a rejection of the operator's size-only/day-weighted decision. It is a requirement that the run and its summary prove the exact experiment that was approved. Mathematical-method certification remains pending after evidence-contract repairs and separate review.

## Bounded implementation correction

The runner now binds module, runner, plan hash and NumPy version in the lock; requires a JSON acceptance record matching lock and identity; validates all saved cells before resume; and checks the exact unique 108-cell grid, means, history totals, integer status/positive counts and lock references before summary. The original legacy lock and development outputs are unchanged. They intentionally fail the new identity check and must not be overwritten or silently upgraded. A separately documented, independently reviewed provenance-lock transition is required before confirmation, without retuning the already selected method.

Verification: 12 targeted method/evidence tests passed, including duplicate-grid, wrong-lock, changed-identity, malformed-count and resume-refusal regressions. No confirmation generation or acceptance record was performed. Correction status: READY_FOR_INDEPENDENT_REVIEW; mathematical review remains a separate requirement.

## Evidence-contract correction acceptance

User explicitly supplied INDEPENDENTLY REVIEWED ACCEPTED. Separate GATE Hooke returned ACCEPTED_WITH_RISK for the bounded evidence-contract correction, independently running 12 tests and 16 additional refusal probes with no blockers. The legacy lock was correctly refused. This supersedes the correction's handoff status only: provenance-lock transition and mathematical-method certification remain unaccepted. No confirmation run is authorized by this bounded acceptance.

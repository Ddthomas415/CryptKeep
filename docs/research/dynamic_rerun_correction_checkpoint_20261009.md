# Dynamic rerun correction checkpoint

ENGINEER. User approved the two reproduced review findings.

Merge now rejects overlapping original-source/input keys with conflicting hashes,
in addition to existing runner/math and duplicate-result checks. Output creation
is exclusive; published results cannot be overwritten by this merger.

Buys now refuse additional exposure when any current holding's opening price is
missing, nonfinite or nonpositive. Sales do not use this entry gate. An unavailable
target opening price likewise cannot authorize a buy. Frozen signals, fees,
windows and selection remain unchanged.

Verification: `tests/test_rerun_frozen_dynamic.py`: 15 passed. New tests cover
both manifest conflict types, existing-output preservation, missing/nonfinite
held prices, subsequent recovery and a protective sale with a valid own price.
No full suite or archive rerun performed. Original 96-result artifact and parts
are preserved and describe the pre-correction runner; their recorded hash must
not be replaced with the corrected source hash.

Next proof: independent review, followed by a separately named rerun of affected
outage paths and manifest verification. Do not reuse old-hash parts in a new
corrected-runner merged artifact. Missing bars establish an archive gap, not an
exchange outage. End NAV remains marked, not terminal-liquidated profit.

Acceptance: READY_FOR_INDEPENDENT_REVIEW. No logger, schedule, account, campaign,
original archive or production changes.

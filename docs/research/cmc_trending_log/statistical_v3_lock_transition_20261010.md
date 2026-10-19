# Statistical v3 provenance-lock transition

Role: ENGINEER. Risk: HIGH. Status: READY_FOR_INDEPENDENT_REVIEW.

New artifact directory: `research/research_corrections_20261009/cmc_calibration_v3_evidence_v2/`.
Original directory, development results and legacy lock remain unchanged. This transition preserves B_studentized_circular_block14, development seeds, confirmation seeds, generator, estimand and thresholds; it does not repeat selection or inspect confirmation outcomes.

Verified the unchanged method module matches both legacy development and lock; the old runner identity matches development; the selected method agrees in both artifacts; and the original confirmation directory contains zero JSON parts. The new lock adds the corrected evidence-runner hash, current plan hash and NumPy 2.4.4 identity, with parent lock/development hashes.

The runner's default output directory remains the original directory to avoid silently rerouting existing operations. Future authorized use must explicitly set the imported runner's OUT to this separate directory before invoking confirm/summarize. Do not rerun develop, overwrite the legacy lock, mix old parts, or create the hash-bound review acceptance until separate review is complete.

No confirmation histories, acceptance marker, market outcomes, scoring or campaign changes occurred. Mathematical-method review is separately pending; this provenance transition does not establish statistical size control.

## Independent disposition

Separate GATE Hooke accepted the provenance transition WITH RISK, with no blocker: parent/development hashes, unchanged selected module and current runner/plan/NumPy identities match. In-memory OUT redirection accepts the new lock; confirm refuses absent matching acceptance before generation. Both directories have zero confirmation parts at review. Mathematical code-contract review is now separately complete with risk, but statistical size certification remains pending. The immutable lock's historical pending-review wording is superseded by this disposition, not rewritten. No confirmation authorization follows solely from these reviews.

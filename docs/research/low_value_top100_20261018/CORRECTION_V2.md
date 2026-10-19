# Version 2: instrument identity correction

Version 1 protocol, source, results, by-asset output and review are preserved.
Separate GATE found wrapped instruments slipping through incomplete historical
category tags. Parent's bounded identity scan also found BTCB and seven stable
asset IDs selected in at least one snapshot. These are inconsistent with the
existing instrument-type exclusions; neither their gains nor losses justify
including them. Governance tokens are not excluded by association.

Version 2 removes exactly the 11 CMC IDs in instrument_correction_v2.json from
the input view after validating the unchanged original archive. It reuses the
frozen version 1 engine, with all other membership, raw-rank, timing, capital,
cost, missingness and statistical rules unchanged. No original price or rank is
altered, no excluded rank is backfilled, and no future winner replaces an asset.
Equal-weight baskets are recomputed after the membership correction. An empty
basket stays cash under the original rule. Slug mismatches must fail, not guess.

This is a disclosed post-result data-classification correction, not untouched
validation or another optimized variant. The three hypotheses stand; both
versions count in the research history. No original result is silently removed.
The stored map documents the sources actually accessed. It fixes demonstrated
classification gaps, not every possible historical taxonomy error. Only a
venue-specific, action-aware follow-up can establish executable opportunity.

Primary sources supporting classification: CMC currency pages and stablecoin
category, linked in the JSON. Current instrument descriptions do not establish
past redemption or tradability. No current prices from those pages are inputs.

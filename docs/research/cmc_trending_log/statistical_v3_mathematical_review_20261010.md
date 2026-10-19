# Selected statistical method B: independent review disposition

Separate GATE reviewer Hooke: ACCEPTED_WITH_RISK for code-contract correctness only; no blocking finding. Statistical size remains uncertified.

SHOWN by reviewer reconstruction/probes: day-weighted cohort series, circular 14-day block means, 2000 bootstrap replicates, centered studentization and mean minus upper bootstrap-t quantile form a one-sided lower bound with the intended sign. Missing-day/refusal-only histories refuse and degenerate variance is unavailable. Module hash and recorded method selection match legacy development.

Reviewer did not generate/evaluate confirmation histories, edit files, create acceptance records or access market outcomes. Earlier absence of confirmation-outcome access is not independently provable from these artifacts.

Risks retained: floor(n/14) whole-block resampling represents 84/168/364 days at the 90/180/365-day lengths. Original standard error uses circular-block population variance while bootstrap replicates use sampled-block variance. These finite-sample choices require calibration. Future tolerance acceptance would be pointwise synthetic size control at the registered 7.5% Wilson-upper threshold, not simultaneous coverage, demonstrated power or trading edge.

Provenance-lock transition remains separately under review before confirmation.

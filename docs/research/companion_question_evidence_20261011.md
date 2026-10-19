# Question Evidence in Research Answers

## Confirmed Disconnect

The deployed endpoint returned different keyword citations for Bitcoin and
regulation, and no keyword citations for an unmatched term, but identical
fallback explanations and a confidence score of 0.8 for all three questions.
Retrieval worked; the explanation ignored its question-specific matches.

## Bounded Correction

Fallback answers now display up to three matching archived headlines, identify
keyword overlap rather than verified semantic or causal relevance, and state
when no matching archived evidence was found. Unverified retrieval is distinct
from a verified empty result. Market data remains available as background.

The existing confidence number remains for compatibility, but is explicitly
labelled an uncalibrated context-availability heuristic in fallback answer text.
Response metadata includes confidence_calibrated=false, confidence_basis, and
question_evidence with match count/status and semantic/causal verification false.
This does not establish profitability, causation, or calibration.

## Proof and Limits

Targeted source verification: 34 passed, 90 framework deprecation warnings.
New regressions exercise matched evidence with missing market data, no matches,
and unknown retrieval. Separate review and deployed endpoint results are in the
work log. No rule, campaign, account, collector, credential or paid-model changes.
This is not a semantic relevance benchmark or sustained-operation proof.

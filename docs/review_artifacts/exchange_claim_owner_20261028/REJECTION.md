# EXCHANGE-CLAIM-01

Submission01a18456-a590-7400-9fe9-34958aebdee8 was REJECTED by independent
GATE, P1. Its36passing tests did not cover retry from an existing error row
with both acknowledgement and unknown writes failing. That row remained
error/no-RID and permitted another placement.

Reviewer36passed1.33s;11bindings/four unchanged dependencies verified. This
was not acceptance. Exact submitted artifacts are preserved in rejected_v1.

Author reproduced surviving error state (1failed0.21s), then two fake
placements (1failed0.20s). V2 atomically claims an eligible error row as created
before client build/submit. New regression and rejected-v1 negative control
remain in tests. Corrected v2 needs separate review, not author acceptance.

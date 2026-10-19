# Clock/venue-time sanity (live-money backlog item 11): independent review

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or
deployed; no config or account change. Patch 0047 (commit b6d87e23, cloud
clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev58.zip`,
folder 55. Zip SHA-256:
b151a5359d5068a9fcdfbd96b91b311e2d27a7be83cb2a4eb551a6215f69172c

## What holds

Skew is measured against the round-trip midpoint. An affirmative measured skew
beyond the threshold rejects the intent. Exceeded and failed measurements are
not cached. A venue time in the wrong unit reads as a huge skew and blocks.

## Finding (P3)

Measurement quality was recorded and not used. With a 20 s round trip and a
venue time at the midpoint, the estimate was 0 ms, the result was OK and it was
cached for 300 s, while the true skew could be anywhere within +/- 10 s.

## Correction in 0047

A measurement is a confirmed OK only when |skew| + rtt/2 is within the
threshold. An unconfirmed measurement still does not block, but is not cached,
is logged, and carries `confirmed: false`.

7 new cases, all fail on the previous code. Full suite: 4609 passed, 33
skipped, 19 failed (the same 19 as master).

## Not changed

- A venue with no server-time endpoint, a measurement error and an unconfirmed
  measurement never block; only a log line shows the check is inert.
- The check gates `live_intent_consumer` only, not the executor path.
- The paper campaign has no clock check.

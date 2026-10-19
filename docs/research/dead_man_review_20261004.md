# Dead-man alerting (live-money backlog item 6): independent review

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or
deployed; no config or account change. Patch 0043 (commit 8066e739, cloud
clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev54.zip`,
folder 51. Zip SHA-256:
fad04aa90097c48945af381eb31a05a7adefd8df9410e0ce8fa215f75086c0a0

## What holds

Named heartbeats are written atomically, rate-limited and never raise. The
checker fails closed on no configured names, a missing file, corrupt JSON and
a non-numeric, non-finite or non-positive timestamp. The two live loops beat at
the top of every iteration.

## Findings

1. P2. A heartbeat dated in the future read as age 0, so the checker returned
   `ok` for a loop that was not running until the clock caught up.
2. P2 for evidence. Only `intent_consumer` and `live_reconciler` beat. The
   paper evidence collector, the only loop running today, wrote no heartbeat,
   so the dead-man check could not see it stop.

## This checkout (read-only)

`runtime/heartbeats/` holds only the two live names, last written 2026-09-23.
The collector (pid 46484) is idle and its status file was written within the
last few minutes. Whether anything runs the dead-man check on a schedule here
was not established.

## Correction in 0043

- A beat more than 60 s in the future is unusable; the checker reports that
  name as `missing`. Skew up to 60 s still reads as age 0.
- The collector writes the heartbeat `paper_evidence_collector` at the top of
  each daily-loop iteration and inside the session wait loop.

7 new cases, 5 fail on the previous code. Full suite: 4561 passed, 33 skipped,
19 failed (the same 19 as master).

## Using it (not scheduled by the patch)

The collector idles in 300 s steps by default, so the check needs a longer
window than its 180 s default:

    make check-dead-man DEAD_MAN_NAMES=paper_evidence_collector DEAD_MAN_MAX_AGE_S=900

Scheduling that and choosing where the alert goes are the operator's.

## Not changed

- One maximum age for all names.
- No beat during the OHLCV preflight or while components start and stop.
- The strategy runner, paper engine and tick publisher children have no
  heartbeat of their own.

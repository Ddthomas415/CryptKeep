# Rev58-87 Submission Reconciliation and Priority Review

Active role: AUDITOR. Overall latest-series review: INCOMPLETE.

## Findings

1. P2, SHOWN: latest rev87 still omits the paper corrections reviewed in this
   conversation. paper_engine.py:679 validates a newly read snapshot while
   filling from its earlier quote; the unchanged independent probe again fills
   at 40020 from a three-hour-old 40000 quote after a fresh 61000 snapshot.
   paper_engine.py:607 still scans only the newest fills; its prior independent
   recovery probe again misses the older record. paper_runner.py:253 still calls
   recovery only at startup. This is an integration omission, not a new finding
   or evidence that the separate isolated corrections regressed.

2. P2, SHOWN: 0075 increases the fixed tracked scan from 60 to 1000 but does not
   provide eventual traversal beyond the cap. live_reconciler.py:537-548 reads
   the same newest rows on every pass. A real-store probe with the cap reduced
   to five and seven tracked orders leaves the oldest filled venue order
   submitted through three passes. The saturation warning works but does not
   account that fill. This reproduces the author's disclosed limit, not an
   undisclosed 1000-row incident. Keep 0075's universal "every tracked intent"
   wording qualified; require fair bounded paging or explicitly reviewed
   saturation containment before unrestricted use.

3. P2, SHOWN: REVIEW_GUIDE_0031_0075 says none of 0031-0075 is reviewed. That is
   inconsistent with recorded bounded 0031-0039 dispositions, 0040/0041/0043,
   0046 and separate correction reviews. Do not reset accepted statuses, and do
   not infer those statuses apply to the assembled original patches without
   their required overlays. The guide's git-stash example does not restore
   previous committed production code on a clean commit, so it is not a valid
   before/after reproduction procedure. Use isolated before/after trees.

## Coverage and Verification

Read the pasted request and guide in full. Both rev87 ZIPs are byte-identical:
SHA256 0540eeec764923a91d422e7401e5f1db9bfb5361a05a9651cc2ac35d7ab5a1e2.
Both standalone guide files are byte-identical. ZIP integrity checks passed for
all 30 distinct supplied revision numbers 58-87. Per-numbered-patch hashes show
no changed existing numbered patches between consecutive revisions; revisions
59-86 append 0048-0075, and rev87 adds no numbered patch. This does not compare
all historical README/document semantics.

Read both workbook sheets' cells and formula text via XML. Its own source label
is a rev73 / 0031-0062 snapshot, not rev87. Its counts and statuses cannot serve
as current acceptance proof. Formula caches were read, not recalculated; no fee
or strategy economic result was independently recomputed in this review.

SHOWN: 73 active numbered patches apply in order to 97c24c8e4 in a fresh isolated
candidate /private/tmp/cryptkeep-rev87-candidate-20261005, excluding held 0011 and
superseded 0019. Work-log hunks excluded during assembly. Applicability is not
exact commit-tree identity. 0061 emits a new-blank-line-at-EOF whitespace warning.

Priority live-reconciler group: read production diffs for 0057/0073/0074/0075 and
assembled source; targeted tests covering working orders, not-found and failed
lookup behavior: 47 passed, 8 deprecation warnings, 2.49s. Independent probes:
3 failed in 1.28s, as described above. Commands use the main absolute venv Python
with PYTHON/PYTHON_BIN set, bytecode/cache disabled and temporary CBP_STATE_DIR.
VERIFIED_ENV local isolated candidate. Venues are test doubles, stores are real.

The author's 4904 passed / 33 skipped / zero failures is CLAIMED here, not a
reproduced full-suite result. Earlier "same 19 as master" claims were explicitly
withdrawn in the new guide; preserve that correction instead of quoting the
older numbers as baseline failures.

Remaining groups were inventoried, not semantically or independently approved.
No full historical transcript audit, multiprocess/host/real venue drill, fee-tier
query, current running-process proof, merge or deployment. Claims that live is
disabled or no live producer exists are not freshly established by this review.

## Next Scoped Action

Reconcile original 0042/0044 and the reviewed exact-quote/recovery overlays into
one isolated latest-series candidate before continuing integration proof.
Retain held 0011 and superseded 0019 exclusions. Track 0075 saturation as a
separate bounded reconciliation task. Do not generate another broad patch batch
or change strategy thresholds to manufacture trades from the historical sample.
The research objective remains sustainable net-profit evidence, not endless
hardening; the strategy inactivity diagnosis is a separate read-only economic
task, not authorization to alter campaign logic or historical accounting.

Probe and inventory artifacts: docs/review_artifacts/rev87_review_20261005/.
Main runtime source/config/accounts/collectors unchanged. Acceptance: INCOMPLETE.

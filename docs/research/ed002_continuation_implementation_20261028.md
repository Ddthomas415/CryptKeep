# ED-002: offline continuation and readiness implementation

2026-10-28. Active role ENGINEER. Risk HIGH (financial input/timing correctness).
Implementation: READY_FOR_INDEPENDENT_REVIEW. Study/statistics: INCOMPLETE.

## Decision And Delivered Scope

ED002-CONTINUATION-DESIGN-20261028: the operator selected "Adopt proposed design
(Recommended)" for structural readiness before A, first-candle validation by
E=A+1 hour and proposed observations at :05/:35 each hour. This adopts the
submitted design, not a claim of independent review. No collection, schedule,
date activation or trading was authorized by that decision.

Implemented its offline continuation/readiness path, without strategy or
financial-ledger edits:

- `scripts/research/capture_descriptive_inputs.py` now accepts the separate
  `ed002-public-continuation-plan-v1` profile. It requires pinned aligned
  start/end timestamps spanning 1-24 hours, the exact universe hash and all
  25 identity rows. A window not completed at worker start is refused before
  any request. At most 27 GETs; all existing timeout, payload, TLS and no-retry
  controls remain. Legacy two-hour and warm-up modes retain their bounds.
- `services/backtest/descriptive_readiness.py` supplies pure `merge_receipts`
  and `first_batch_readiness` functions. They have no file/network/process,
  scheduler, strategy, random-trial or return-computation path. Callers supply
  raw response bytes and receipt fields, not trusted precomputed observations.
- The merger verifies supplied hashes, public routes, receipt clocks and body
  status/truncation, then reuses the existing candle and metadata adapters.
  Equivalent overlapping candles preserve the earliest receipt. Conflicting
  completed values remain withheld; future receipts cannot repair old cutoffs.
  Unanswered calls are diagnostics, not delivery proof. Partial calls with valid
  individual receipts can still contribute evidence.
- A newer failed, truncated, unreadable or ambiguous products observation yields
  unknown permission, not old permission or a valid-looking error body. A failed
  candle request does not erase an earlier valid candle. Original failure hashes
  are retained; synthetic unknown mapping bytes are not presented as raw evidence.
- The first-batch check uses separate A/E permission, 300 required default hours
  and 1,464 BTC/ETH hours. It retains known flat exclusions, rejects unknowns,
  and requires BTC/ETH eligibility for the controls. It reports all 25 rows.
  An input COMPLETE report is explicitly not an execution-open check, activation,
  statistical qualification, an economic result or a usable live-trading signal.

## Preservation And Prepared Artifact

Preserved the tested v2 capture script and its two test files byte-for-byte in
`../review_artifacts/ed002_public_capture_v2_20261028.tar`, SHA256
`c29d57d5e09048880e8e0c3215574db593a9791c2322d6e01b0e9d8c7bc6002a`.
Original v1/v2 receipts and hash records remain historical; the new capture
source intentionally has a new hash. The accompanying diff is against the
archived v2 source, not a nonexistent clean Git baseline for these untracked files.

Prepared `research/ed002_public_inputs/plans/continuation_gap_proposal_20261028.json`
for the known six-hour gap, October 28 00:00-06:00 UTC, using preserved candidate
identity references. They are not renewed eligibility. Any later authorized
acquisition refreshes public metadata. The proposal does not extend itself to
subsequent hours or imply historical receipt-time availability.

SHOWN: actual default CLI preview exited 0 with dry_run=true and request cap 27:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B scripts/research/capture_descriptive_inputs.py --plan research/ed002_public_inputs/plans/continuation_gap_proposal_20261028.json --output research/ed002_public_inputs/CONTINUATION_NOT_STARTED_20261028
```

No `--execute`, worker, output capture directory or HTTP request. Existing raw
captures, original contract and frozen strategy implementations were not changed.

## Verification

VERIFIED_ENV targeted command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_descriptive_continuation.py tests/test_capture_descriptive_inputs.py tests/test_capture_descriptive_warmup.py tests/test_descriptive_candles.py tests/test_descriptive_metadata.py
```

SHOWN: 164 passed in 5.35s, exit 0 (35 new, 129 existing). Initial run before
unanswered-call handling and four additional cases: 160 passed in 4.67s.
Final proof includes 27/26 call counts, pinned/future/invalid windows, scope,
actual supplied receipt times, missing/truncated candles, overlap/conflicts,
metadata shadow/expiry/A-E separation, unknown identities, control failure,
deadline-prefix refusal and unchanged caller inputs. Invented bytes/fake transport
and process fixtures only; no new live behavior or market returns verified.
Existing supervisor tests cover owned cleanup and append-only output refusal.
Socket/process guards apply in test bodies, not an OS-wide or import guarantee.

No full-suite, prior backtest, randomized audit or accepted report rerun. No
independent review of this new implementation is claimed. The previous reviewer
availability error was not retried or treated as acceptance.

## Limits And Next Boundary

The merger is a pure API, not an automatic filesystem crawler, authenticity
verifier or new continuous collector. Caller-supplied scope/identities must be
bound to the frozen universe and provenance. Structural registration still needs
an actual future signed F/A/E/B and reviewed source bindings; no helper chooses
dates or signs for the operator. Supplied timestamp checks do not attest clocks.

First-batch checks assume initially flat accounts. They do not certify subsequent
held-position valuation, all future input continuity, fills, source truth, or
whole-comparison correctness. Execution-open and later outcome validation remain
the existing comparison/report responsibilities. An INCOMPLETE planned start
cannot be silently shifted or retrospectively repaired. A later optional repair
dataset cannot change evidence available at the old deadline.

The twice-hourly cadence is adopted as design only. No host/scheduler was
inventoried or changed. The 182-day capacity scenario is not an uptime, vendor
quota or storage promise. Model settings, all 25 assets, one-hour delay, frozen
strategies, existing evidence and SB-1's unresolved qualification are preserved.

Next: review these exact changed sources, diff, tests and bindings. Any real
continuation capture or scheduling needs its separately bounded operational
authorization; no runtime commands are proposed as already approved here.
Implementation proof complete: READY_FOR_INDEPENDENT_REVIEW.

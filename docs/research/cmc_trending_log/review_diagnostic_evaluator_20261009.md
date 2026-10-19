# Independent review: CMC diagnostic evaluator and helpers - 2026-10-09 10:40 UTC

Reviewer: Claude (cloud session), not the author. Read-only: no evaluator, helper, test, snapshot or schedule edited.
Scope: `cmc_diagnostic_evaluator.py` (112e818d) as marked READY_FOR_INDEPENDENT_REVIEW, plus the helpers it and the
cohort path use: `cmc_snapshot_evidence.py` (c363c2f9), `cmc_daily_cohorts.py` (8908af57), `cmc_cohort_coverage.py`
(84891acf), `cmc_quote_evidence.py` (8df9e64c), `cmc_endpoint_timing.py` (c5f5a35e), `cmc_return_math.py` (30deee74).
Existing tests: 90 passed. Probe: the real v3 snapshots in `cmc_trending_log/snapshots/`, loaded with the
accepted loader and passed through `build_cohorts`.

## Verdict: CHANGES_REQUIRED (one blocker on real data)

Collected snapshots are unaffected (all raw evidence is saved); every finding is in evaluation code, so fixing
before any scoring loses nothing.

## Findings

1. BLOCKER - real v3 lists are rejected as malformed; zero observed days.
   Each v3 snapshot has 100 hidden-boost rows: 84 `listing` + 16 `dex`. DEX rows carry `cmc_id: null` by design
   (no CMC id). `build_cohorts` requires every row to have a positive decimal id, so both real v3 snapshots
   (05:03:03Z, 05:09:13Z) are excluded with "malformed or duplicate CMC IDs": observed days [], events 0.
   Consequence if unfixed: every collection day counts as missing, every appearance is HISTORY_UNCERTAIN,
   and the operator's 30-clean-day primary cohort can never form. The 90 tests pass because fixtures contain
   no DEX rows; the latest "malformed-ID fix" made this stricter rather than safer for real data.
   Suggested fix (author's call; needs a written convention): define the event universe as `type == "listing"`
   rows; DEX rows are counted and reported as out of universe, not as malformed; a null/invalid id on a
   listing row still rejects the capture. Add a fixture copied from a real v3 snapshot.

2. HIGH - interfaces do not connect yet. `build_cohorts` emits `identity_eligible_at_first_observation` and no
   quotes; `evaluate` reads `event["identity_eligible"]`, `event["coin_quote"]`, `event["btc_quote"]`. Passing
   cohort events straight in would mark every event EXCLUDED_IDENTITY or raise KeyError. The integration adapter
   (first-observation snapshot -> that coin's tracked Coinbase quote + majors BTC quote) is still missing.

3. HIGH - silent exclusions. `evaluate` drops endpoint candidates for ineligible identity, structurally invalid
   quotes and coin/BTC pairing > 60 s with `continue`, without counting them. Item 4 requires every exclusion and
   missing endpoint to be reported; a MISSING result cannot currently say why.

4. MEDIUM - crash instead of exclusion. `select_endpoint` raises on two observations with the same timestamp;
   `evaluate` does not catch it, so one duplicate aborts the whole evaluation rather than recording an exclusion.

5. MEDIUM (item 2 convention) - tie order. Captures with equal `snapshot_utc` are ordered by file path. v3 file
   names end in a random hex suffix, so "first observation" among equal timestamps is deterministic but
   arbitrary. The convention needs an explicit rule (e.g. earliest `received_utc` of the coin's own quote, then
   file name) and a test.

6. MEDIUM (item 3 quote qualification) - what the captured quote can and cannot prove. The logged Coinbase
   quote is the public ticker: payload has bid, ask, price, size, time, trade_id, volume. `time` is the last
   TRADE time and `size` the last TRADE size, not quote time or top-of-book size. So:
   capture alignment = provable (request/receipt times); provenance = partly (response hash and the tracked
   product name are recorded, but the payload has no product id to cross-check); freshness = only a proxy
   (age of last trade at receipt); executable size = NOT provable from current captures (no bid/ask sizes).
   Qualifying executable size would need a level-1 book capture (bid/ask with sizes) in a future logger version.

7. LOW - identity flag scope. Only the 25 rows with a Coinbase product carry `identity_eligible` (16 True,
   9 False); the rest have no key and correctly read as not eligible. Worth stating in the convention.

Correct as reviewed: cost arithmetic (entry commission on cash, exit commission on proceeds, 1.2% registered fee);
+/-12 h endpoint window with earlier-on-tie; 30-day daily-sampled coverage logic matches the operator decision
(observed event day required; prior missing day -> HISTORY_UNCERTAIN; prior appearance -> REPEAT); first observation
is preserved per UTC day and later captures do not upgrade identity.

Acceptance: NOT ACCEPTED until finding 1 is fixed and tested on a real-snapshot fixture; 2-4 are required for item 4.

## Re-check 2026-10-09 10:45 UTC (author change to cmc_daily_cohorts.py at 10:39, not yet marked ready)

Finding 1 resolved on real data: both v3 snapshots accepted; 16 DEX rows per snapshot reported as
`dex_rows_outside_listed_event_scope`; observed days ['2026-10-09']; 84 listed events, all HISTORY_UNCERTAIN (correct:
no prior days). Finding 5 addressed: same-timestamp captures that disagree become AMBIGUOUS_FIRST_CAPTURE.
93 CMC/readiness tests pass. Identity-eligible events = 0 because the first observation of each coin is the
05:03 capture, made with an earlier identity map (sha 44136fa3...) that qualified no coins; the 05:09 capture used
the accepted map (sha 2fa8792d...), which qualifies 16, but cannot upgrade a first observation (intended rule).
Today's events are HISTORY_UNCERTAIN regardless, so no primary event is affected. Findings 2-4 and 6 remain open. Full review will be repeated on the integrated version when marked ready.

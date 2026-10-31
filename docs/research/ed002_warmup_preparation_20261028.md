# ED-002 bounded warm-up preparation

2026-10-28. Active role ENGINEER. Risk HIGH (public capture/provenance/process path).
READY_FOR_INDEPENDENT_REVIEW. Acquisition NOT RUN; study readiness INCOMPLETE.

## Scope

Continued the requested next step: prepare the warm-up seed, not acquire it.
The previous single public capture instruction is consumed. This preparation
does not authorize more requests, study activation, schedules or trading.

Extended the existing capture script with a separately validated warm-up plan
schema. Legacy two-hour plans retain their 27-call cap and default behavior;
the new profile alone allows up to 35 calls. Original source/tests were preserved
before editing in `../review_artifacts/ed002_public_capture_v1_20261028.tar`,
SHA256 `8ac33b7c983248bbb87548745d140148ab794bb464ea2be3c648d9bd3c5b9b22`.
Both archive-member hashes match the earlier submission. Prior raw receipts,
plans, results and verification files were not rewritten. Their recorded code
hashes describe that archived version, not the now-extended source path.

## Fixed Proposed Acquisition Profile

| Inputs considered | Required hourly seed | Maximum candle pages |
| --- | ---: | ---: |
| BTC and ETH | 1464 each: 61 complete UTC days | 5 each: 300/300/300/300/264 |
| Other 23 declared symbols | 300 each | 1 each |
| Public reference metadata | Products and currencies refreshed first | 2 requests |

Total cap 35 public GETs if all 25 are eligible, 34 if only MATIC is excluded as
in the previous observation. Actual future status must be fetched; old status
is not permission. All 25 rows remain in the plan and diagnostics. Unknowns
remain INCOMPLETE; known-ineligible flat symbols need no candle request.
Do not replace MATIC with POL or select symbols using returns.

Resolve one W at worker start: the most recent completed UTC midnight. BTC/ETH
request [W-1464h,W); others [W-300h,W). Pages are non-overlapping, at most 300
hourly buckets; request end is one second before the page's exclusive boundary
to avoid asking for a 301st inclusive endpoint bucket. Validate returned coverage
independently; do not assume an endpoint produces every requested hour.

W is a warm-up seed boundary, NOT A/E/B or an activation date. Seed records keep
their actual future capture receipts, not historical publication times. They can
inform a later decision once known; they do not prove historical tradability or
earlier causal signal availability. Additional up-to-A coverage will still need
proof before activation. No strategy is evaluated on the seed.

Unchanged transport limits: 5-second socket inactivity timeout, 110-second
cooperative loop, 120-second parent worker wait and up to 5-second owned cleanup;
process creation and initial/final filesystem operations are outside that wait.
No universal whole-program deadline or successful cleanup guarantee. No retry,
redirect, auth, environment proxy, TLS bypass or overwrite. Same 2 MiB/body,
16 MiB stored payload total plus one overflow-detection byte before stopping.
The attempt may end partial; its budget is not extended to finish paging.

## Candidate Plan And Proof

Plan: `research/ed002_public_inputs/plans/warmup_seed_20261028.json`.
References: `research/ed002_public_inputs/plans/warmup_id_sources_20261028.json`.
All 25 candidate IDs derive from the preserved October 28 metadata capture,
with both payload hashes checked. References are not independent semantic
identity approval; metadata is refreshed again on any authorized acquisition.

Actual read-only CLI preview, VERIFIED_ENV, exit 0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B scripts/research/capture_descriptive_inputs.py --plan research/ed002_public_inputs/plans/warmup_seed_20261028.json --output research/ed002_public_inputs/WARMUP_NOT_STARTED_20261028
```

SHOWN: dry_run=true, planned_max_requests=35. No capture folder, worker or request.
The --execute flag is absent, not authorized by this preview.

Final targeted command, VERIFIED_ENV, exit 0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_capture_descriptive_warmup.py tests/test_capture_descriptive_inputs.py tests/test_descriptive_candles.py tests/test_descriptive_metadata.py
```

SHOWN: **129 passed in 3.64s**: 13 new warm-up cases and the 116 prior targeted
cases. Invented bytes/fake processes only. Exact per-symbol windows/counts,
descending provider rows, final 264-hour pages, no overlap, missing-hour refusal,
mid-page HTTP failure, unknown/excluded rows, profile constraints, preserved
receipts and legacy limits checked. No actual warm-up, returns, random audit,
full suite or new network/real cleanup test. Existing 101-report proof not rerun.

## Handoff

Exact extended transport/plan needs independent or human review. This thread
does not independently accept its new high-risk code. After review, one bounded
warm-up acquisition can be proposed under the stated 35-call cap. No new study,
collector, service, account/credential, campaign, capital/risk or trading action;
no original registry/strategy/old-result changes, dependency installation, commit
or push. Real warm-up completeness, ongoing coverage and statistical readiness
remain INCOMPLETE until separately demonstrated.

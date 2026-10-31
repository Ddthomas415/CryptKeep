# Full Collector Restoration Preparation

2026-10-29. Active role: AUDITOR. Operational restoration: INCOMPLETE.
This is preparation, not permission to start collection or alter the archive.

## Findings

- SHOWN: refreshed scoped host checks found neither recorded PID2741 nor the
  known collector-script match, and no open handles on the three exact archive
  paths. Stop flag absent. Saved status still says running at14:34:05UTC;
  that is not current liveness. Other hosts/launch methods remain UNVERIFIED.
- SHOWN: an isolated byte copy of SQLite/WAL/SHM passed quick_check before and
  after the existing store initializer. All existing schema hashes and row
  fingerprints were preserved. Only raw_funding_observations and its
  source/capture index were added. Original three file hashes, sizes and
  mtimes matched before/after. This is compatibility evidence, not a migration
  of the original archive, permanent exclusivity or a live collector check.
- SHOWN: existing counts on the copy:16631funding,13296open-interest,
  16628basis,33810quote and13296order-book rows. The added raw table is empty.
  The mutated rehearsal copy is NOT an untouched pre-start backup.
- SHOWN: services/analytics/edge_cadence.py reads funding_snapshots only.
  A disposable replay containing a validated saved raw pair and fresh synthetic
  OI/basis rows reports funding missing. With old legacy rows, legacy funding
  would eventually appear stale despite successful paired collection. Failed
  pair attempts must not be used to hide a genuine collection failure.
- SHOWN: the accepted plan template retains all five existing families.
  The dashboard's specialized start helper does not expose the paired options;
  the existing explicit CLI does. No new launcher/framework is required.
- UNVERIFIED: recurring runtime, installed remote configuration, binary
  signature authenticity, source freshness guarantees and financial eligibility.

## Evidence And Verification

Rehearsal: docs/review_artifacts/okx_full_collector_rollout_20261029/
20261029T184226Z_d0e8c4098be64399ab5235943459370e/REHEARSAL.json.

Offline reproduction: same parent directory, cadence_replay.py and
CADENCE_REPLAY.json. It validates the prior pilot pair, uses only a disposable
SQLite database, and retains the replay database's hash across the checker.
This is historical receipt replay, not new market data or a strategy run.

VERIFIED_ENV commands:

```sh
./.venv/bin/python -B docs/review_artifacts/okx_full_collector_rollout_20261029/cadence_replay.py
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_edge_cadence.py
```

Replay exit0 confirms the mismatch, not a repair. Existing cadence tests:
11passed in0.32s, exit0. Their passing does not cover raw-pair compatibility.
Historical304source tests were not rerun. No full-suite claim.

## Next Source Repair

DIRECTOR proposal: narrowly repair source-cadence compatibility before rollout.
Keep legacy behavior available; distinguish successful validated raw capture
from a diagnostic attempt, corrupt evidence and financially qualified funding.
Use explicit source/native identity when evaluating paired coverage so another
source or instrument cannot stand in for a missing configured pair. Expose the
evidence lane in results. Do not synthesize legacy rates or promote any
strategy/execution/normalization gate. Ordinary cadence thresholds remain
unchanged; future timestamps must not become fresh through age clamping.

Required synthetic tests: legacy parity; valid paired capture; source/native
identity isolation; failed/partial/corrupt records; empty/missing raw table;
malformed/future/stale timestamps; bounded scan uncertainty; read-only behavior
and no store initializer. One consolidated independent review for this
monitoring change, not another infrastructure layer. Implementation not done
under this read-only preparation stage.

## Proposed Operational Sequence, Not Executed

1. After that source repair is independently accepted, recheck exact host,
   process ownership and handles immediately before any separately approved
   operation. Preserve the current original archive/WAL/SHM as a fresh coherent
   backup; do not substitute the already-mutated rehearsal copy.
2. Preview the explicit full-family template/options and original DB target;
   pin inputs for the operation. Proposed source live_public preserves existing
   provenance but must not turn old SDK records into paired records. Proposed
   raw budget1row/4MiB per cycle; two funding GETs/30s funding capture checks.
   Existing other-family SDK requests are additional and outside that budget.
3. Obtain explicit permission for one full-family foreground cycle and original
   archive initialization/writes, including PID/status/stop-flag side effects.
   Use the existing CLI with max-loops1, not a new scheduled job. Any proposed
   outer timeout must actually be enforced on the owned child; the CLI's
   funding limits are not a whole-cycle timeout. Preserve receipts on failure.
4. Verify a successful pair, all expected other-family writes, reopen/readback,
   correct source cadence and unchanged authority gates. Loop liveness alone
   is not success. A partial write is not rolled back by stopping the process.
5. Only after that result and separate recurring authorization, launch the
   existing collector with the same approved full-family inputs at300s. Track
   the owned PID and first successful cycle. No duplicate job, trading change
   or unrelated service action. Do not kill an unowned PID, delete evidence,
   restore an old DB over new writes or retry automatically after failure.

No service, schedule, active plan, original database, account or trading setting
changed during preparation. No new public requests. Original archive byte
preservation is shown for the rehearsal interval, not claimed for all time.

# ED-002: offline Mac pilot wrapper and job template

2026-10-28. Active role ENGINEER. Risk HIGH (background lifecycle/concurrency).
Implementation READY_FOR_INDEPENDENT_REVIEW. Operations/study/statistics INCOMPLETE.

## Adopted Design And Scope

ED002-MAC-PILOT-DESIGN-20261028: operator selected "Adopt local Mac pilot design
(Recommended)" for offline wrapper/template preparation: this Mac, at most
24 hours/48 slots, maximum dispatch lateness 120 seconds. No installation,
collection, power change, study activation or trading was authorized.

Implemented `scripts/research/run_ed002_collection_slot.py` as a standalone
stdlib-only controller. The existing capture CLI, financial libraries, frozen
strategies and stored raw evidence remain unchanged. No installer is added.

## Artifacts And Guards

- Disabled policy:
  `research/ed002_public_inputs/plans/local_pilot_disabled_20261028.json`.
  enabled=false, start_ms/end_ms=null. No pilot or study dates assigned.
- Two-hour capture plan:
  `research/ed002_public_inputs/plans/pilot_two_hour_20261028.json`.
  Preserves all 25 candidate identity rows and the adopted universe hash. Raw
  reference identity hashes are not current eligibility; each later authorized
  capture would still refresh metadata through the existing CLI.
- Uninstalled template:
  `docs/review_artifacts/ed002_local_pilot_20261028/com.cryptkeep.ed002.public-inputs.plist`.
  Minute 5/35 calendar array, RunAtLoad=false, KeepAlive=false, no extra triggers.
  Its absolute command pins the exact policy SHA and uses Python -I -S -B.
  Even loading this disabled draft would not authorize or start collection.

Before invoking capture code, the wrapper verifies ten exact input hashes:
itself, the capture CLI, adapters, shared ledger and its corrected-math dependency,
two package initializers, universe and capture plan. Two currently absent namespace
initializers must remain absent. Source drift, unexpected pin sets, symlinked
inputs/output paths, duplicate policy keys and nonfinite JSON are refused.
These are local drift checks, not adversarial attestation or a hermetic Python
environment. Installed third-party packages/OS/interpreter are not fully pinned.

Each UTC slot has one exclusive claim directory. A stable nonblocking flock
prevents concurrent dispatch, and its inode is not unlinked. Duplicate or partial
claims are never reset. An unfinished prior slot, corrupt final receipt or
uncertain group cleanup holds later slots. This remains conservative if a
controller is killed while its child continues; no automatic recovery guesses
that an unseen descendant has stopped. Operator release is not implemented.

Pre-start, expired, late and busy dispatches preserve bounded, exclusive local
diagnostic receipts where the namespace can be written. Invalid/disabled policy
and failed receipt writes also produce sanitized CLI status; they cannot promise
a persisted receipt when filesystem access itself fails. Before spawning, source
pins/timing are checked again, a successful claim is flushed, and at least 24 MiB
free-space headroom is required. The headroom is not a reservation.

Each permitted slot invokes the existing two-hour CLI once with a replacement
clean environment, disabled stdin/stdout/stderr, and a new owned process session.
The wrapper does not import the capture module. launchd environment entries
override selected values but are not themselves an environment scrub; the child
environment replacement is explicit. No private credentials are read or passed.

The existing capture retains at most 27 GETs, its 120-second worker wait/five-
second cleanup, 110-second cooperative loop, five-second sockets and payload
limits. The outer CLI wait is at most 140 seconds, then at most five seconds
owned-group cleanup. A dispatch needs that remaining expiry margin. On timeout,
interrupt or lingering group, only the session created by this invocation is
targeted; a failed disposition marks the pilot held. No pkill or unrelated process
cleanup. File/process creation and receipt writes are outside wait deadlines;
this is not a hard 145-second bound on every operation or an OS-wide kill guarantee.

Two material operating premises: a trustworthy local clock and an OS/filesystem
honoring the checked locking/process APIs. Clock tampering/jumps, OS hangs or
power-loss durability are not certified. UTC slot keys and the fixed date range
still bound eligible distinct opportunities to 48; the controller never creates
catch-up slots, extends dates or performs intra-slot retry.

## Verification

VERIFIED_ENV command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_ed002_collection_slot.py tests/test_descriptive_continuation.py tests/test_capture_descriptive_inputs.py tests/test_capture_descriptive_warmup.py tests/test_descriptive_candles.py tests/test_descriptive_metadata.py
```

SHOWN: 200 passed in 6.45s, exit 0 (36 new / 164 existing). New standalone
selection: 36 passed in 0.56s. The first 32-case run had 31 pass/one fail: a test
incorrectly expected only the primary wait, not the bounded cleanup/reap wait;
the expectation was corrected, not the cleanup behavior weakened.

Cases cover UTC minutes and repeated New York DST hour, disabled/preview/no
namespace side effects, 48-slot/24-hour/date/lateness guards, clean child command,
duplicate/pending claims, real nonblocking file-lock contention and stable inode,
source drift before import, namespace/package changes, disk refusal, time changing
between claim/spawn, timeout/interrupt/error/cleanup failure, final-write failure,
unknown prior completion, template trigger/schema and JSON refusal cases.

Only invented child receipts and fake process/group control were used. Actual
file locks operate on disposable test directories. No real process-group kill,
launchd invocation, hard process death, DNS/TLS, unattended file permission,
background data capture, full suite, strategy/return or statistical trial verified.
Existing accepted capture tests are regression proof, not new network proof.

Actual isolated CLI preview (without --execute) exited 0:
dry_run=true, enabled=false, scheduled_slots=0, max_slots=48,
max_public_gets=1296, collection_started=false. The first preview command
mistakenly supplied a placeholder hash; it refused with exit 2 before action.
The corrected command used the generated hash; no source was changed to pass it.
`plutil -lint` returned OK for the uninstalled template. No pilot directory exists.

## Review And Operational Boundary

The existing independent reviewer was checked once after source freeze; it
returned its usage-limit error. No replacement, repeated polling, reset-time
assumption or independent acceptance is claimed. Source/tests, disabled policy,
template, diff and bindings are submitted together; human review remains an
available route. This thread does not independently accept its high-risk code.

Before any pilot: review this exact package, supply separately authorized future
pilot start/expiry, regenerate the pinned policy/template, recheck duplicates and
paths, and obtain explicit installation/collection authority. This does not require
a new strategy, vendor account, signing credential or framework. Do not install
the disabled draft as if it were an activated plan. Do not grant broad folder or
account access speculatively; any actual denial needs its precise diagnostics.

The installer/operational cutover is not built or run here. In particular, the
future pilot root/log directories must be prepared under that separate scope;
launchd output paths need usable parents. Unloading a job cannot substitute for
verifying owned descendants. Preserve evidence on stop/failure, never clear raw
state or an unsettled claim just to restart collection.

Only real pilot receipts can establish cadence/availability on this Mac. No
external alert delivery, restart continuity, 182-day data coverage, study freeze,
historical tradability, executable edge or profitability is established here.
No scheduler, service, Docker, power, account/credential, strategy/risk/capital,
trading, dependency, commit or push change. Implementation proof complete:
READY_FOR_INDEPENDENT_REVIEW; study/statistics INCOMPLETE.

# Declared-account backup acquisition bridge

Bot relation: BOT_RULES; runtime trading configuration not checked.

Initial state:READY_FOR_INDEPENDENT_REVIEW; source remains self-checked until
the independent result is recorded below. Existing R3/R10 operating work is
INCOMPLETE. This is source/test evidence, not a live backup or provider test.
Final source disposition2026-11-11T23:32:57Z:ACCEPTED_WITH_RISK by separate
Rawls GATE, declared quiescent local acquisition only; INDEPENDENT_REVIEW.md.

## Operator outcome and boundary

`services/control/group_a_backup_acquisition.py:acquire_bundle` takes all nine
explicit Group A account data roots, their caller-owned query-only SQLite
connections, one whitelisted public configuration projection per account and
the public run manifest. It inventories the declared data trees, refuses
unmapped SQLite stores and missing paper_trading/intent_queue/strategy_state
stores, freezes regular artifacts into one private temporary spool, checks
local recording references, invokes the accepted local bundle core, then
re-inventories and rehashes source artifacts before an acquisition receipt.

No implicit path discovery, private YAML reading, source database opening,
connection closing, source chmod, repair or deletion. Caller-supplied handles
remain caller-owned. Unknown filenames, unsafe links/types, orphan SQLite
sidecars, incomplete/deep/oversized decision records, missing/changed local
recording objects and shared/outside-root references refuse. SQLite WAL/SHM/
journal sidecar contents are not read or copied; consistent main-store copies
use the existing SQLite backup API. A missing directory is not created.

All producer-allowlisted regular files in the declared data trees are selected,
not just three database filenames. Unrecognized files/directories refuse the
whole acquisition rather than being silently skipped. This closed producer
allowlist was added after the initial GATE rejection documented below;
the first implementation's generic extension policy was insufficient.
Required names come from the actual producer
DB_PATH declarations in storage/paper_trading_sqlite.py,
storage/intent_queue_sqlite.py and storage/strategy_state_sqlite.py.
Recording paths/ref relationships come from signal_input_capture.py:
runner_decisions, signal_inputs, code/settings/completed-prefix/bar digests.
The coverage check establishes retained local bytes/references, not complete
record semantic correctness, historical tradability, or successful replay of
every possible record. The existing shared-object mode is not removed or
changed; this acquisition bridge refuses it until its separate root and restore
mapping are implemented. No record is silently reassigned to another coin.

Artifacts must be quiescent throughout this acquisition lane. Observed append,
rotation, deletion, replacement or additions refuse. Database/WAL contents
may change while their per-store snapshot is taken; this is not one atomic
nine-account timepoint. Active-file prefix capture or a writer freeze protocol
is not implemented. This is a real operating-integration gap, not an invented
permission gate or a completed foreground backup service.

Outputs are always new exclusive directories through the accepted core.
A failed final revalidation can leave a content-verified bundle, but no
acquisition-approved receipt is returned. That retained output must not be
promoted as a complete source acquisition. No automatic retry, overwrite,
cleanup or success-entrypoint stub. Temporary scratch is private and closed
on return/failure; it does not delete retained source or bundle files.

## Evidence required and validation scope

Required proof:real nine-account SQLite/WAL and artifact fresh restore;
producer-generated decision archive preservation/replay; required stores,
root/output isolation, path/handle mismatch, missing/aliased/link/unknown input
refusal; exact lengths/digests; final full-inventory and content revalidation;
resource/deadline/partial-write failures without a false acquisition receipt.

Tests started with collection ImportError before the new API existed.
The first implementation ran22test bodies successfully but all22fixtures
errored in teardown because the fixture both closed each SQLite writer and
later invoked its context exit. Corrected that fixture ownership mistake;
then22passed, expanded26passed, before final consolidated verification.
This was test code, not a production connection-lifecycle defect. No passing
suite was claimed from the teardown-failing run.

SHOWN initial author command,2026-11-11T23:26:45Z (HEAD82b5f216e; existing dirty
work retained):

```sh
env CBP_STATE_DIR=$(mktemp -d /private/tmp/cryptkeep-acquire-XXXXXX) \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest -q \
  -p no:cacheprovider tests/test_group_a_backup_acquisition.py \
  tests/test_group_a_backup_bundle.py tests/test_sqlite_backup.py \
  tests/test_state_backup_restore.py tests/test_group_a_unit_composition.py \
  --junitxml=docs/review_artifacts/group_a_backup_acquisition_20261111/pytest.xml
```

151passed in6.52s:28acquisition+55bundle+7helper+14legacy+47composition,
zero failures/errors/skips. Actual existing capture producer's record was
replayed from the created bundle; the separate nine-account fixture was
restored into a fresh directory. The actual-producer test's name includes
"restore", but that test itself does not invoke fresh restoration; do not
represent the two tests as a single producer-through-fresh-restore proof.
No full suite/CI/native target/provider run. This execution is author proof;
independent review remains pending at this addition.

Bound source SHA256:
`66a3909f29a72739ebf7d8a262afeedb5ae7040f49b28f32fc4990c42a16440e`.
Bound tests SHA256:
`c8df34e1db55d145c1b5c589fbc54dada7e0b0aa1a0c774dd4b1ccf2a7a6b864`.
Accepted bundle core remains
`140cf68cd3247c4ab5017dfd1cf976dda9fabaab6e655b9e2d18aba49b520fa1`;
SQLite helper remains
`9a0fcd1f4894b18f571406e60beb34cf7514d8595d1bb9d564fb8c943d031a6a`.
No source/test edits while the final GATE is pending.

### Dated correction:2026-11-11, after initial source GATE

SHOWN separate Rawls GATE checked the initial bound source, producer paths,
references and revalidation; independently ran151tests in5.85s and verified
the initial XML/hash. It REJECTED that source with one P1:generic path/extension
policy allowed an unrecognized data/config.json with a synthetic api_token
to be copied and a successful acquisition receipt returned. Namespace
ownership is not secret clearance. Author had flagged this possible boundary
while review was pending; review independently reproduced it. No real
credential or operating data was involved. Earlier automatic-selection safety
claims are narrowed by this correction, not supported by151passing tests alone.

Correction:closed paths derived from the existing producers, before any
artifact payload/scratch read:signal_inputs/<sha64>.json and
runner_decisions|runner_candle_diagnostics/<account64>/<session32>.jsonl,
plus only their known parent directories. Databases still require explicit
caller-owned connection mappings; extensions do not authorize arbitrary
database acquisition. Unknown paths fail; no broad content scanner or claim
that trusted producers cannot emit sensitive data. A speculative health-file
entry was removed after checking its actual producer uses runtime/flags,
not data. Runtime flags are not acquired or claimed by this bridge.

Four new refusal regressions failed before the guard, reaching the scratch
trap and reporting the wrong fixed failure. They pass afterward, checking
that neither scratch nor payload reading occurred. The first correction run
had154passed/1failed:using real-format fixture IDs collided with the existing
producer's test IDs, so its reader encountered the minimal fixture envelope
first. GATE paused before further edits. Corrected fixture IDs to disjoint
valid shapes; also made the actual-producer test perform a fresh restore
before replay instead of merely replaying the bundle. Original151-test and
failed155-test XMLs remain preserved; neither is final corrected evidence.

SHOWN corrected five-file command above with output`pytest_corrected.xml`:
155passed in7.30s (32acquisition+55bundle+7helper+14legacy+47composition),
zero failures/errors/skips. XML SHA256:
`31e2f285455ad62e229f1a420d924f44b6a58adc83fbbca4d0a161ff024363f9`.
Corrected source SHA256:
`1efc872694476e547e76c0cc7cf61d1ae2cdd32838b8b0d9f468b519cd1a1317`.
Corrected tests SHA256:
`d47c511dae7e2c261296738c6355aaae2d49b63721211f04ed823712306d2177`.
Core/helper/composition unchanged. Diff-only re-review pending when this
correction was written. No source/test edits while it is pending.
Subsequent separate GATE23:32:57Z closed P1:four failures independently
reproduced before, five passes after (including producer/fresh-restore/replay),
corrected XML/hash verified; full155-test rerun remains author evidence.
No further source/test edits. Initial rejected source is not accepted by this
final disposition; only the corrected source hash above is covered.

Two material assumptions:
1. Trusted producer owns the declared roots and supplies query-only database
   handles with continuous creation/path provenance. database_list plus a
   matching current stat establishes pathname attribution, NOT the inode
   already held by a connection if the file was replaced after opening.
2. Source/output namespaces have no hostile same-UID concurrent mutation.
   Canonical paths, link/type checks and inventories are not kernel-enforced
   namespace isolation or physical read-only mount proof.

Content file-count/byte limits cover the combined selected inventory and
generated metadata; enumeration has an additional4x-entry cap. One shared
cooperative deadline covers scan/freeze/record checks/core/rehash/receipt.
These are not hard interruptible disk/SQLite deadlines or a cap on all kernel
I/O/allocation; verification rereads bytes, and scratch plus bundle can each
occupy up to the selected content budget. Disk capacity still needs native
proof. Source SQL statements are fixed read-only PRAGMAs, not arbitrary SQL.

Inspected:current queue/log/Git; accepted bundle/core/helper/composition;
actual producer paths and record schema; new acquisition/test code. Not
inspected:existing account/config/database contents, source mounts/ACLs,
MEGA account/quota/keys/client, target runtime, CI or full suite.

## Remaining work

DONE, independently source-accepted WITH_RISK:declared-nine-root acquisition, local reference
coverage, frozen artifact streams, selected bundle/fresh restore integration
and focused failure tests. PARTLY DONE:live-source acquisition/R10 coverage.
NOT DONE:shared recording-root capture/restore mapping; active-file capture;
source-connection inode attestation; complete secret-free operating config;
encryption/key/client provisioning; MEGA upload/download/restore; retention;
six-hour foreground entrypoint; native/service/heartbeat/commissioning proof.
No package install, service/host/Docker/provider/account/credential/scheduler/
alert/trading/configuration change, source archive mutation, commit or push.

Source/hash drift, missed source roots/references, unsupported storage behavior,
changing files or a failed encrypted remote restore could overturn broader use.

What do I know that could change the owner's decision that I have not yet said?
The bridge removes manual stream assembly for declared local evidence, but
it cannot yet run successfully against continuously changing recordings or
shared-object archives. That remains part of completing the real backup
program; no complete live or off-server protection is claimed.

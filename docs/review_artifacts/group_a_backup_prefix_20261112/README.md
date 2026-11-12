# Active recording prefixes and shared-object recovery

Bot relation: BOT_RULES; runtime trading configuration not checked.

Creation state:READY_FOR_INDEPENDENT_REVIEW, self-checked source only.
Final source disposition2026-11-12T01:55:39Z:ACCEPTED_WITH_RISK by separate
Rawls GATE; see INDEPENDENT_REVIEW.md. No material blocker in reviewed scope.
Existing R3/R10 operating integration remains INCOMPLETE. UTC date2026-11-12;
owner's local date2026-11-11. No live source or provider was used.

## Delivered scope

New services/control/group_a_backup_prefix.py provides acquire_prefix_bundle
and restored_recording_directories. The accepted strict/quiescent acquisition
API, local bundle/helper and unit composition are unchanged. No existing
acceptance result is reopened or claimed to cover this extension.

The separate mode uses all nine declared account data roots, explicit
caller-owned query-only SQLite handles, public configuration projections and
optional explicit per-account shared-object directories. No environment-based
source guessing, private YAML or existing operating database opening.

For each initially enumerated journal, one nonblocking shared lock freezes
its complete newline-ended prefix. Only byte copying is inside the lock;
parsing, reference resolution and bundle finalization are outside. The writer
uses a blocking exclusive lock, so the reader CAN delay a writer during copying.
Busy locks refuse without waiting/retry. A pre-existing partial tail refuses
without repair. Final validation locks and hashes only captured bytes; later
append, including a later incomplete tail, does not invalidate that prefix.
Truncation, replacement and rewriting captured bytes refuse success.

Initial local/shared CAS objects plus transitive references of captured
decisions are acquired by expected digest. Objects published after initial
enumeration but before a captured record are included when referenced.
Identical shared digest-verified bytes are stored once under the first sorted
account's data/shared_signal_inputs namespace; metadata preserves each
account/journal scope mapping. Local and shared records may coexist in one
journal. This layout is an archive namespace, not reassignment of ownership
or permission to change source runtime configuration.

Each account receives a manifest-hashed recording_prefixes.json with journal
byte counts, hashes, individual cutoff timestamps, scope destinations and
explicit new-session exclusions. No global atomic account/file snapshot is
claimed. New sessions after initial inventory are outside capture, not silently
described as backed up. Immutable object hashes and captured prefixes are
rechecked before returning a prefix receipt. A failed final check may leave a
content-verified selected bundle but never returns a prefix-approved receipt.

The restore helper first verifies the bundle using an external manifest hash,
then checks mapping schema, fixed local/shared destinations, account/journal
association and recorded size/hash. It returns scope-specific directories for
the existing replay consumer, including mixed-scope journals. It never fetches
an absent object from a source root or substitutes another account's quotes.

## Selection, budget and failure boundaries

Reuses the accepted closed producer-path policy:unknown artifact paths refuse
before scratch/payload copying. Shared roots are explicit, canonical and flat;
only digest.json files can supply payloads. Known .capture-* temporary names
are metadata-only and count against enumeration bounds. Local publication
temps and transient two-link CAS publication may conservatively refuse; link
checks are not broadly relaxed. No temporary/source file is repaired/deleted.

One cooperative deadline covers inventories, freezing, closure, copying,
source revalidation and restored mapping. Selected file-count/byte limits
cover objects, journal prefixes, metadata and core output. Additional scan
entry limits bound shared metadata enumeration. Repeated verification reads
extra bytes; spool and bundle both require space. These are not hard disk,
SQLite, kernel-I/O or wall-clock interruption guarantees. Caller-owned SQLite
connections remain open and source settings are not changed.

Assumption1:trusted producers emit backup-appropriate content, obey the append
lock/immutable-object protocol, and provide continuous SQLite connection/path
provenance. Path attribution does not prove the inode held by an old connection;
hash/name authorization is not semantic secret clearance.
Assumption2:source/output namespaces are not maliciously changed by the same
UID. Canonical paths and inode/link checks are not kernel namespace isolation
or proof of physical read-only mounts. Per-store SQLite consistency remains
distinct from cross-account or cross-file atomicity.

## Verification and evidence lanes

Evidence needed:real producer local/shared/mixed capture through acquisition,
fresh restore and replay; append-safe cutoffs; reference closure/deduplication;
initial/late partial tails; busy locks; changed prefixes; unknown/unsafe inputs;
mapping tamper under verified hashes; size/deadline and failure receipts.

Initial feature run failed collection because the API did not exist. New
source's first13cases passed3.28s, expanded26cases passed6.69s. These are
development checks, not independent acceptance or a full-suite result.

SHOWN final author verification (HEAD82b5f216e; existing dirty work retained):

```sh
env CBP_STATE_DIR=$(mktemp -d /private/tmp/cryptkeep-prefix-XXXXXX) \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest -q \
  -p no:cacheprovider tests/test_group_a_backup_prefix.py \
  tests/test_group_a_backup_acquisition.py tests/test_group_a_backup_bundle.py \
  tests/test_sqlite_backup.py tests/test_state_backup_restore.py \
  tests/test_group_a_unit_composition.py \
  --junitxml=docs/review_artifacts/group_a_backup_prefix_20261112/pytest.xml
```

181passed13.10s:26prefix+32strict acquisition+55bundle+7helper+14legacy+
47composition; zero failures/errors/skips. XML separately parsed by the
author, SHA256f9163379e64253fbb1bcec58e58d9152402448e70111ad7cc84cccc44a84ddd4.
New prefix source SHA256:
4b3dc23494a5b5de9e9a41e78b3c17fcfe1aac647ccee28ba52318e6686229c7
New tests SHA256:
62381c4dc645bdbd3959b6fdb988f14f37d9c0b95ca0f306d8fc327a29198c1c
Accepted strict source1efc8726..., core140cf68..., compositor41520005...
unchanged. Source/tests frozen while independent GATE is pending. This is
focused Mac/source/synthetic proof, not full-suite, Linux/deployment, market
performance or encrypted MEGA recovery.

Separate GATE independently matched the bound hashes/dependencies, inspected
locking/budgets/reference closure/deduplication/final source checks/restore
mapping, ran all26new tests (26passed5.31s) and parsed the181-case XML with
zero failures/errors/skips. It did not rerun all181. No reviewer edits,
network or operational action; source/tests remained frozen during review.

Inspected:latest queue/work-log/Git, actual recorder publication/append/replay
code, accepted core/acquisition/composition, and new source/tests. Not
inspected:operating configs/accounts/data, native Linux locks/mounts/ACLs,
MEGA account/quota/client/keys, services, CI or full-suite status.

DONE, separately source-accepted WITH_RISK:explicit local/shared prefix acquisition,
persisted cutoff/scope mappings, fresh-restore replay and focused tests.
PARTLY DONE:R10 backup integration. NOT DONE:complete secret-free operating
config, source/connection/native attestation, encryption/key/client setup,
MEGA upload/download/restore, retention, six-hour foreground entrypoint,
native service/heartbeat/commissioning evidence. No run_group_a_backup.py
stub, source archive mutation, installs, provider/credential/host/Docker/
service/schedule/alerts/trading/configuration operations, commits or pushes.

Source/hash drift, uncooperative writers, untrusted content/provenance, source
namespace replacement or failed broader recovery could overturn applicability.

What do I know that could change the owner's decision that I have not yet said?
An internally complete prefix is not the whole archive at one global time.
New sessions/later records are excluded explicitly, writer delays and safe
publication-window refusals remain possible, and this is still not an
encrypted off-server backup service.

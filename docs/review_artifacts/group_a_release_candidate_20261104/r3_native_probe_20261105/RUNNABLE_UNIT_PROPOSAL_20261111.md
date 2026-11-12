# Group A runnable-unit and provisioning proposal

Bot relation: BOT_RULES; runtime trading configuration not checked.

Role: DIRECTOR. Scope: engineering queue item2/R3 only. Evidence checked
2026-11-11T16:15:48Z; self-checked, READY_FOR_INDEPENDENT_REVIEW.
This is a local implementation proposal, not runnable units, an installer,
an operating configuration, or permission to connect or change services.

## Decision and usable outcome

Recommend one offline composition increment that turns the accepted account,
quote-routing, alert and lifecycle fragments into a reviewable stopped-release
package, together with the missing Group A backup integration. Reuse the
existing implementations below; do not create another service manager or
rewrite strategy/financial logic. Then obtain separately scoped stopped-stage
and activation approval. A target that merely becomes active is not success.

The intended outcome is nine isolated paper accounts whose exact source,
configuration, quotes, order lifecycle, recording, alerts, backups, startup and
stop behavior can be demonstrated under the existing frozen contract. Group A
does not replace Group B or narrow the25-symbol mandate. No research dates,
strategy, exit, capital, risk, sizing or cost rule changes are adopted here.

## Existing evidence and reuse (SHOWN)

- Frozen core: v3 overlay SHA256
  `724b4785dd627f9ff35bc91b939788d6ac90850458ba4f4333f7c7231f3dac1d`,
  on protected580ca31ea983af6452a1e02ab8d4b51645e9b43c; manifest928b12da...
  and tree74ffffcc.... Selected1616 pass/one disclosed Linux skip, separately
  accepted with risk. Not a standalone runtime release or Linux dependency lock.
- Retained host capture SHA256
  `2b0c30e8b3846b39e60178a496be53f8db92f5ef8023b1b367d4a48bd2e3c5c8`,
  sampled14:42:43Z, separately accepted with risk. systemd255, isolated venv
  Python3.12.3/SQLite3.45.1, ccxt4.5.48/PyYAML6.0.3/NumPy2.4.4. These
  observations are not current application health, import/ABI or load proof.
- `services/control/group_a_systemd_policy.py`: exact21-service roster,
  target,21 named failure instances, failure template, restart/stop overlays.
  `group_a_account_units.py`:18 non-startable account fragments and argv.
  `group_a_quote_routing.py`:18 replacement account fragments with directory
  binds, publisher fragment/argv. Do not install both copies of an account unit.
  `group_a_alert_units.py`:watcher/failure fragments and argv, distinct user.
- The four renderers and `scripts/run_group_a_alert.py`,
  `scripts/run_group_a_quote_publisher.py`, queue readers and cursor image
  were byte-compared with the frozen archive:8/8 match. Additional baseline
  entrypoints, paper/strategy sources, app paths, observations and backup tool
  match the frozen tree manifest. No application execution in this inspection.
- `scripts/backup_state.py`:reuse its SQLite backup/integrity/manifest
  primitives after isolated tests, not an unchecked CLI invocation. Its backup
  selects `data_dir()` only; the CLI also records an operator event. It is NOT
  the full R10 decision/config archive, encryption, remote upload, retention,
  heartbeat, restore rehearsal or Group A foreground scheduling implementation.
- Frozen requirements: `docs/research/paper_simulation_spec_20261031/README.md`
  sections3,6,8,9,12. Earlier source reconciliation and deployment boundary
  remain applicable; this proposal replaces neither their evidence nor scope.

The rest is PROPOSED unless expressly labelled SHOWN. No claim that a proposed
file, user, ACL, credential, package, test result or integration already exists.

## Exact role and launch contract

For planning only, `R=ga724b4785dd62`, `P=cbp-group-a-R`,
`S=/srv/cryptkeep/releases/R`, `D=/srv/cryptkeep/state/R`,
`C=/srv/cryptkeep/alert-state/R`. These expand literally, not via a shell.
Account IDs are the Cartesian product of
`breakout-default`, `ema-cross-default`, `mean-reversion-default` with
`btc`, `eth`, `sol`, joined by a hyphen. Strategies map respectively to
`breakout_donchian`, `ema_cross`, `mean_reversion_rsi` and underscore preset IDs.

| Role / exact naming rule | Intended launch and physical authority |
| --- | --- |
| Nine `P-ACCOUNT-strategy.service` | Preserve account renderer argv: `/usr/bin/env -i`, its explicit PATH/state/venue/symbol/log/strategy/preset/hourly/capture variables, `S/.venv/bin/python -B S/scripts/run_strategy_runner.py run`. Write only `D/ACCOUNT` in the service namespace, with config and bound snapshot subpaths read-only. |
| Nine `P-ACCOUNT-paper.service` | Matching same-account argv/state/market, `S/.venv/bin/python -B S/scripts/run_paper_engine.py run`; never a live executor. Same account-state boundary as its strategy partner, no other account root. |
| `P-publisher.service` | Preserve quote renderer argv and existing foreground publisher. `CBP_STATE_DIR=D/support/publisher`, exact component symbols BTC/USD,ETH/USD,SOL/USD. Write only its snapshots/locks; no legacy publisher or nine independent polling replacements. |
| `P-watcher.service` | Preserve alert argv `/usr/bin/env -i PATH=/usr/bin:/bin S/.venv/bin/python -I -B S/scripts/run_group_a_alert.py watch R`. Alert identity; release state read-only, cursor writable, credentials read-only. Actual read permission must be proved, not inferred from a mount directive. |
| `P-backup.service` | Required role, NOT IMPLEMENTED by current fragments. Proposed one foreground no-overlap6-hour supervisor, using existing consistent-copy/manifest primitives plus explicit full-artifact/encryption/provider/verification integration. No placeholder command or exit0 stub may satisfy this row. No timer or extra unmanaged background process silently substitutes for the frozen role. |
| `P-failed@.service` | Preserve alert terminal argv ending `terminal R %i`, with instance restricted to the21 existing lifecycle identities. No queue/cursor credential or writable state. Inaccessible release state and cursor preserved.21 possible instances, not21 extra base-unit files. |
| `P.target` | Preserve lifecycle Wants/PartOf/Requisite/OnFailure/stop ownership, no new semantic dependency graph by accident. Actual health is a separate acceptance check. Only this approved target may later be enabled; no current enable/start authority. |

Normal base files:21services+one failure template+one target=23. Overlay the
existing21 lifecycle service drop-ins and one failure-template drop-in=22.
Account quote binds belong in the18 quote-rendered base units, not a second
conflicting set. Thus45 intended unit/drop-in files before any justified new
drop-in. The capture's44 queried identities include21 concrete failure
instances; they are NOT44 installable base files. Stop membership remains
target+21services+21failure instances, exactly as the accepted policy produces.

A future compositor emits each `ExecStart` exactly once from validated argv;
no shell, `eval`, raw YAML interpolation or `shlex`-as-systemd escaping.
Preserve intentional `%i` only in the failure template; reject injected
newlines, extra directives and unintended substitutions. Existing startup
loader-variable unsets must operate before `/usr/bin/env -i` starts. Preserve
UMask0077, restart growing delay/start limit, cgroup killing and stop bounds.
Do not weaken guards or rewrite the non-startable APIs merely to make tests
expect executable output: add a separately explicit composition API and tests.

Any new runtime code, including backup integration, changes release composition.
Keep v3 immutable; freeze the reviewed increment and complete source/operating
manifest together, then derive the final release ID and regenerate all paths,
units and receipts. The planning R/path-absence observations do not certify a
different final release namespace. Bind both source and operating hashes.

## Provisioning and permission contract

Proposed identities remain distinct `cbp-ga-paper` and `cbp-ga-alert`, non-root,
no login or trading credentials. SHOWN absent at capture, not allocated UIDs.
Do not pick numeric IDs, add them to the owner's gid1000, or change the existing
host tree's ownership/mode. Shared paper UID follows the accepted renderer;
per-account namespace restrictions are not whole-host hostile-tenant isolation.

Source and venv:immutable/root-controlled after separately approved staging,
read/execute only to required identities, no unreviewed writable `.pth`,
site startup hooks or shared mutable host venv. Pin complete Linux dependency
artifacts; matching three METADATA versions is not a dependency lock. Pytest
is a test dependency, not a reason to install it in the operating venv.

State:root-controlled release parent; nine distinct physical account roots,
separate publisher snapshots/locks, no symlinks or aliases to old state.
Account pair writes only its own root; root-owned frozen `runtime/config/user.yaml`
and publisher snapshot directory bind are read-only exceptions. No production
data opening during stopped file staging. Journal creation is a distinct,
explicit fresh-candidate initialization operation, not a read-only smoke test.

SHOWN old parent/app/state mode0750 UID/GID1000. Proposed smallest access
mechanism is named-user traversal/read ACLs on only the required paths and
future-created release files, preserving existing owners and no broad chmod.
This is NOT a validated ACL recipe or authorization to modify those ancestors.
First inspect relevant ACLs/mounts in a later authorized bounded read and test
two distinct UIDs on an isolated Linux tree. Account UMask0077 is retained.
Default ACLs may not survive explicit0600 creates/chmod or atomic replacement:
prove actual status, snapshot, SQLite DB/WAL/SHM and rollover writers remain
readable to the alert identity and unwritable by it across restart/replacement.
If that fails, stop the permission subdesign and propose the smallest writer/
publication correction; no read-all capabilities, owner-group membership,
same-UID alert workaround, silent UMask change or assumed root watcher.

Watcher:read-only mount of D with the same physical root/queue identities as
the protected receipt; writable C only. Mount protection is not a DAC grant.
Keep original nofollow/single-link/readonly-filesystem and FD identity checks.
Cursor parent must satisfy the existing root-owned/non-group/world-writable
check; C must be alert-owned0700, `group_a_delivery.image` alert-owned0600,
initialized from exact EMPTY_IMAGE, plus stable `supervisor.lock`0600 regular
single-link file. Provision once; never unlink/reseed them to clear a failure.

Credentials:existing root-controlled proposed `/etc/cryptkeep/group-a/R`
contains no secrets in this package. Later owner-authorized provisioning only:
encrypted `slack-webhook.cred`, separately pinned public `queue-receipt.json`.
Preserve per-unit read-only credential mounts and file-mode/link checks.
`env -i` does not remove the filesystem mount; the existing entrypoint explicitly
uses `/run/credentials/UNIT`. Do not assume a credential variable survives it.

Queue receipt cannot be fabricated before fresh journals exist. After an
explicitly authorized initialization, freeze actual release-root, nine data-dir
and nine database device/inode pairs plus since_ms, then mount the receipt
read-only. All three DB/WAL/SHM files must meet the existing reader contract;
do not create fake empty WALs or replace a journal to pass. Inode loss or queue
replacement invalidates attribution: report unknown/stop; no automatic reseal.

## Configuration, missing integrations and test matrix

Generate nine new configs only after configuration-change approval. Do not copy
the live laptop or host YAML. Proposed profile follows the frozen simulation:
both `execution.live_enabled=false` and `live_execution.armed=false`; exactly
one Coinbase USD symbol per account; named preset/hourly source, loop15s,
paper USD1000, fee50bps, slippage0, strict
`require_fresh_hourly_candles=true`, `require_fresh_snapshot_quotes=true`,
`use_ccxt_fallback=false`. Booleans must be typed, not truthy strings. Entry
and exit/first-signal rules remain unchanged. Fee must be rechecked/recorded on
official start day;50bps here is the frozen modelling input, not a fresh
account observation. Validate the actual merged/runner-effective config.

Sizing remains a known contract implementation gap: source reads fixed
`strategy_runner.qty`, while section3 requires aboutUSD1000 per position.
A fixed tiny0.001 or an invented fractional/dynamic sizing rule is not equivalent.
Before config approval, show the existing intended sizing mechanism, initial
quote/precision/fee-inclusive quantity and behavior after price/cash changes;
obtain clarification if the frozen wording cannot choose it. No sizing value
or financial logic is changed by this proposal. Preserve the documented
cooldown cadence ambiguity; do not certify15-second blocked loops by arithmetic.

R10 reuse must include ALL9 account data stores, decision/input recordings,
secret-free configs and manifest; per-database consistency is not an atomic
snapshot across all9 accounts. Retain capture times and relationships. The
existing CLI's operator-event write must not escape the candidate boundary;
prefer its pure functions behind an owned adapter. Encryption BEFORE upload,
separate provider/key/retention and weekly restored-copy comparison are still
required by section8. Provider/accounts/keys are owner choices, not invented
by this plan. No provider calls, credentials or new spending here. The R3
resource adapter currently supplies disk/memory, not a proven backup-success
producer: route a dated validated backup receipt into backup-failure/unknown
evidence, never convert missing backup status to success. External13-check
heartbeat delivery/owner receipt remains R10, not supplied by a local PID.

The focused future verification matrix is:
- Composition:exact roster/files/argv, no missing backup, collisions/unknown
  inventory refused, no inherited duplicate ExecStart/drop-ins, safe paths and
  environment, no unapproved source/config/dependency bytes. No automatic start.
- Permissions:two real UIDs and actual current writers, RO namespace plus DAC,
  atomic replacements/WAL lifecycle, no writes to other accounts/config/source,
  no visibility of webhook in paper namespace; mode/ACL/identity failures fail.
- Initialization:explicit fresh-root-only mutations; refused existing journals,
  inode receipt/cursor/lock exactness; duplicate/refused startup leaves evidence
  intact. Stopped staging never calls application openers.
- Linux manager:isolated parser and effective-graph checks on the intended
  version, followed only when authorized by real restart/duplicate/stop/reboot
  evidence. Retain the accepted policy; active target alone fails acceptance.
- Entry/data/order paths:reuse existing R1/R4/R8/R12 regression gates; strict
  quotes, stale-candle buys versus sells, durable exits and preserved #600/#601.
  New configs must not bypass decision recording, reconciliation or live-off.
- Backup/alerts:consistent isolated copies, no source journal mutation, bounded
  no-overlap schedule, encryption/upload/verify/restore failure and unknowns,
  real delivery only after send approval. HTTP acceptance is not owner receipt.
- Capacity/recovery:source/state inventory before/after, partial writes/staging,
  shared deadlines and owned-unit-only cleanup; false health, process escapes,
  disk pressure and restart storms. Existing72h section9 thresholds unchanged.

Use focused synthetic tests during implementation and one final composed check
plus independent review; do not rerun old market studies or repeat1616 tests
for a document change. Later material source changes determine which accepted
tests need rerunning. No full-harness/Linux/startup claim from a static parser.

## Staging, activation, rollback and remaining boundary

These are future procedures, NOT authorized commands (UNKNOWN_ENV until each
target prerequisite and the concrete installer are reviewed):
1. Freeze new source/operating artifacts; review exact diffs and provenance.
   Resolve sizing and backup/provider/access choices before runnable acceptance.
2. With separate approval, recheck only relevant host identity/base, proposed
   namespace/effective units/drop-ins, ACLs/mounts/dependencies and capacity.
   Retain bounded safe status/reason codes so an unavailable collision query
   is diagnosable; do not infer absence or loop automatically.
3. Separately authorize stopped staging/provisioning with exact newly owned
   paths/users/modes/ACL deltas, dependency acquisition and cleanup authority.
   No enable/start, existing-tree extraction, SQL or credential provisioning
   hidden inside it. Validate staged hashes and parser graph, preserve host
   checkout/#600/#601, collectors/backend/legacy ledgers and every unrelated unit.
4. Separately authorize fresh-state initialization/credential setup and a bounded
   activation, with protected inventory and owned-unit receipt. All required
   roles/config/namespaces must pass before success; do not start an incomplete
   target because its source or version check passed. R10 sends require their
   named recipient/scope and owner receipt, not a dummy successful sender.
5. Failure cleanup stops only receipt-owned target/services/failure instances
   using the accepted exact membership. Verify cgroups/descendants; do not
   delete state/logs, unlink locks or overwrite a live ledger with a backup.
   Remove/revert only demonstrably attempt-owned files/ACL entries when covered
   by that attempt's cleanup approval. Ambiguous ownership or unconfirmed
   recovery stays INCOMPLETE; no broad kills, forced reseals or promised rollback.
6. Only after required evidence/independent review and separate authorization:
   existing72h commissioning, then official-start approval under section9.
   Never backdate the26-week clock or count commissioning as evaluation.

Inspected:current queue/log/Git and relevant branches, frozen archive/tree
hashes, accepted host receipt and existing source/tests/spec. Not inspected:
current host beyond that dated receipt, ACLs/groups/mounts, private runtime
config, credentials, DB contents, external providers or real effective graph.
No services, application loops, package installs, experiments or operational
verification were run. This document is self-checked, not implementation proof.

Assumption1: protected base and intended isolated paper scope remain applicable;
if changed, reconcile only the affected inputs before mutation. Assumption2:
later provisioning can grant required least-privilege access without changing
financial rules or exposing old state; the Linux permission test must establish
that, otherwise this part of the proposal requires revision.

Done:source/role/permission/integration map and failure matrix. Partly done:
access/sizing/backup execution design (explicit unresolved requirements).
Not done:runnable artifact, provisioning, installation, target tests,
delivery/R10 or commissioning. Scope acceptance cannot turn these into done.

What do I know that could change the owner's decision that I have not yet said?
The next increment is not simply adding ExecStart. The watcher needs proven
cross-user access and real journal identities, and the required backup role,
full-position sizing and external-provider integration are not supplied by
the accepted source package. Those can be built or resolved within the existing
objective, but calling the current package deployable would conceal them.

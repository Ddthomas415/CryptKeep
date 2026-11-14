# Owner-approved read-only host preflight, November14

Bot relation: BOT_RULES; actual trading configuration, credentials/accounts and
database contents not read. Remote sample2026-11-14T12:44:32.614425Z, capture finished
12:44:33.324272Z. Observation is non-atomic; loaded application behavior unverified.
Separate Nash retained-evidence GATE2026-11-14T12:48:07Z ACCEPTED_WITH_RISK;
authorization compliance NONCOMPLIANT, overall compatibility INCOMPLETE.
See HOST_PREFLIGHT_REVIEW_20261114.md. No retry or broader authority follows.

**Scope correction,2026-11-14:** Codex's approval question explicitly excluded
"configuration values". The reused packet also retained nonsecret systemd policy
values (including User/Group,Restart,ProtectSystem and NoNewPrivileges). These are
configuration values, even though no configuration file contents or trading
settings were read. That portion exceeded the literal approved scope; prior
packet acceptance did not authorize it for this attempt. Owner was told as soon
as this was recognized. No settings changed and no secret/account/DB contents
were read. O165 records the authorization-to-payload mismatch. Do not call the
attempt fully scope-compliant or use the result to infer broader permissions.

## Practical result

SHOWN: the inspected `/srv/cryptkeep/app` still matches the protected older base
580ca31ea983af6452a1e02ab8d4b51645e9b43c for all11sampled source paths:8expected
absences and3matching old files. All11sampled rows also equal November11's sample.
Current local source is different; no equivalent service elsewhere was searched
or ruled out. This is not corruption/deletion evidence or permission to patch the
running checkout. The local repairs, new profiles and R7freeze were not deployed.

The reference namespace ga724b4785dd62 is the historical proposed release derived
from the preserved724b...archive, NOT a newly selected candidate. Its three exact
release/state/alert-state paths and proposed two service users are absent. This
does not prove a fresh namespace is globally collision-free: unit observations
remain unavailable, and other installations/namespaces were not inspected.

| Retained evidence | Observation and limit |
|---|---|
| Identity/platform | ubuntu-4gb-nbg1-3 / cryptkeep UID1000, Linux aarch64; strict SSH host-key checks plus returned identity validation. Not loaded-service source proof. |
| System/service interpreter | System Python3.12.3 / SQLite3.45.1; inspected checkout venv independently reports the same versions. No application imports. |
| systemd |255; meets source policy254+ version prerequisite only, not effective-unit/permission readiness. |
| Fixed venv package metadata | ccxt4.5.48, PyYAML6.0.3, NumPy2.4.4; pytest absent at inspected site. METADATA reads, not package import tests, dependency lock or global absence proof. |
| Filesystem capacity |33,448,443,904 available bytes (31.15GiB),2,348,061 available inodes; instantaneous availability, not sustained workload/log/archive sufficiency. |
| Memory |3,991,343,104 total bytes,3,066,929,152 available (2.86GiB); not21-service capacity proof. |
| Existing path ownership | /srv/cryptkeep, app and state0750 UID/GID1000; no ACL/group/mount or dedicated-user access proof. releases,/var/lib/cryptkeep,/run/cryptkeep absent at sample. |
| Reference proposed identities | cbp-ga-paper/cbp-ga-alert absent; historical release/state/alert-state exact paths absent; not permission to create them. |
| Existing collector metadata | crypto-edge unit loaded/active/running, cadence unit loaded/inactive/dead. Output freshness and underlying health not inspected; no restart warranted or performed. |
| Collision/policy limits | Proposed44-unit observation unavailable. Its cause is not retained. Existing ReadWritePaths=null means sanitizer could not retain an approved value, not zero writable paths. |

## One connection, unchanged reviewed payload

Owner approved one five-minute read-only SSH connection after the explicit
scope question. Existing compatibility adapter/controller/remote bytes unchanged
from their accepted source pins. Local hash checks and ssh-G preparation passed,
rendered command6fc82e85f03e145e2966d04eb83032e0f5dff351b42cd4fa205545498aaf4527,
16058bytes, before the only connection.

Receipt:compatibility_attempt_20261114T124342Z.json,
SHA2569762941a33f674e22a262100c563848d456d04a999b3e3ea6a8ac21b99caa252.
Start12:44:10.666875Z, finish12:44:33.507334Z, elapsed22.84seconds, exit0,
connection_processes_started1, automatic_retryfalse, owned_group_cleanup
no_live_members, owned_leader_reapedtrue. Descendant reaping not independently
established. Same native session17245 persisted through Tailscale check and
authentication; no second connection. Owner's later done reply did not trigger
another attempt. Approval URL was shown only in chat/tool output, not saved here.

Transport markers show connected/check/authenticated/remote command/exit. The old
reducer's remote_inventory_validatedfalse describes its narrower transport-stage
scope; the compatibility adapter independently validates the typed projection and
returns candidate_compatibility_values_received. Overall receipt stays INCOMPLETE,
full_runtime_readiness_verifiedfalse and atomic_inventoryfalse.

Remote writes: none requested except normal SSH/system/daemon audit effects may
persist. Source was provided in memory on stdin, not uploaded to disk. No service,
permission, config, user, database, schedule, account, trading or R10tool/cloud
operation; no source or deployment changed. Isolated Python stdlib queries,
fixed source hashes/package METADATA and whitelisted path/unit/capacity metadata
only. No arbitrary remote stdout/error or trading configuration values retained.
The nonsecret systemd policy over-read is explicitly disclosed above, not excused
by that whitelist or represented as owner-authorized configuration inspection.

## Next useful boundary

Prepare the existing simulation's updated isolated source/profile delivery package
from reviewed increments, preserving the protected host checkout. The old126-file
archive does not contain subsequent fixes/profiles/R7choices. This is offline
packaging/review, not a new controller, source redesign, installation, permission
change or service start. Do not invoke the old full compositor with a fake backup
reference: R10 remains STOPPED and original commissioning criteria unchanged.
Any actual stopped staging/provisioning, credentials/delivery or activation needs
its own exact approved scope. Unknown unit collisions, effective access and capacity
remain explicit; do not make another SSH request automatically.

DONE: one authorized fresh identity-bound metadata capture and source comparison.
NOTDONE: full runtime/source/dependency import proof, effective ACL/group access,
clear unit namespace, actual candidate/profile/cache provisioning, freshness cadence,
external delivery/R10, commissioning, official start or financial evidence.
Open questions that could overturn scope-limited readiness: uninspected namespaces,
source/process mismatch, missing import/runtime dependencies and sustained resource
use. The preflight alone does not certify any of them.

What do I know that could change the owner's decision that I have not yet said?
The sampled platform versions are suitable prerequisites, but the approved local
simulation has not been installed there. The next step is isolated reviewed delivery,
not more source fixes or an in-place update, and R10 is still explicitly stopped.

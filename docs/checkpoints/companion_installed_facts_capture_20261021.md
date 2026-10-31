# Bounded Installed Facts Capture

2026-10-21. Active role ENGINEER. Risk HIGH: operational inspection and existing
in-container authentication. Implementation requires separate review before use.
User continued after the explicit request for one read-only installed-file and
storage-lineage capture. This does not authorize startup, repair or cutover.

## Scope

Reuse exact original seven and prepared four IDs from the accepted reconciled
manifest/evidence and saved staged metadata. Recheck identities/images and the
selected state/configuration before and after; originals must remain running,
prepared applications created/never-started. Do not discover and substitute IDs.

The single capture may copy only explicitly selected public application/SDK,
startup-helper and article-archive files. Tar members must be regular files with
the exact expected basename, bounded length and no extra entries. Missing files
are diagnostic results, not permission to install them or retry the operation.
No copied Python/shell file is executed on the host.

Use the existing pinned Docker CLI, an empty temporary Docker config, sanitized
selected inspection format, bounded streaming subprocess transport and no host
credential/config environment. No raw Env, arbitrary log or stderr export.
Native command families: container inspect, selected file cp to stdout, and two
fixed read-only exec checks against already-running storage only. No container
create/start/stop/rm/rename/build, network changes or application query.

Storage checks use existing in-container authentication without exporting its
values. PostgreSQL runs a single BEGIN READ ONLY transaction, local statement
timeout, schema and frozen original-snapshot lineage comparisons, aggregate
booleans/counts only, then ROLLBACK. MinIO uses the existing signed bucket HEAD
helper with credentials on private curl stdin; no object writes. Qdrant uses a
fixed local collection GET, no proxy/redirect/retry and bounded response. Database
connection/access logs or server statistics may change; no application-data write
is requested, and this is not a guarantee of zero physical storage activity.

Budget:240seconds overall, normally10seconds/command,200commands maximum,
25MiB total captured file bytes,1MiB text/4MiB binary/2MiB archive per file.
Reserve time for final selected inventory and receipt. No automatic retries.
On failure, preserve sanitized partial evidence and the final inventory if
available; do not stop or clean up containers. Temporary CLI config only may be
removed. A timeout cannot prove daemon cancellation; unknown outcomes stay unknown.

## Acceptance

The capture's result is evidence, not a per-image policy approval. File hashes
must bind actual IDs/images; archive hashes must match the approved local archive;
current database lineage must match the55 saved identities. Independently review
the SDK retry/redirect registration and startup chain before issuing policies.
Every missing/mismatched item remains explicit. A passing file/namespace check
does not establish a working explanation endpoint, market truth or profitability.

The accepted controller, metadata comparator, frozen archive and staged resources
are not edited. Runtime remains INCOMPLETE. No cutover or service startup follows
from this authorization or from a successful read-only capture.

## Frozen Implementation Preflight

Read-only helper: docs/review_artifacts/companion_continuation_20261021/capture_installed_facts.py.
SHA256211170c182a9a125d3b03957002e84675be7348bac980614bc5685a54fa22b7b.
Focused tests: tests/test_companion_installed_facts_capture.py,
SHA25670e7c0218934a2478982edf16b660feff3a10d229999d97b99e4e1c478b3368a.

VERIFIED_ENV offline verification:
`env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_installed_facts_capture.py`
returned10passed0.39s, exit0. Checks cover input hashes, selection, tar refusal,
read-only SQL shape, inert default and unapproved execution refusal. They do not
prove a complete capture, installed policy or native execution. No full suite.
Independent operational-code preflight pending. No native capture has run.

The source command budget bounds native subprocess operations, not an absolute
wall-time bound for arbitrary host filesystem operations or final receipt writes.
No success is inferred from an uncommitted/missing report. Missing or unreadable
file facts may still yield a packet ready for review, not compatibility acceptance.

## R1 Resource-Bound Correction

Independent GATE rejected R1: the aggregate byte error was caught as an ordinary
file error, so its synthetic probe received93MiB, continued storage checks and
reported ready. Preserved receipt: installed_facts_capture_review_r1.json. No
native attempt ran on that version.

R2 makes aggregate exhaustion terminal for ordinary work, bounds each transfer
by remaining allowance including tar overhead and a one-byte overflow probe,
and conservatively charges the full possible transfer on a failed subprocess
because discarded partial stdout has no smaller proven bound. Successful copies
charge actual tar bytes, not just validated payload. Final inventory remains
reserved and partial evidence ends INCOMPLETE. No transport/controller change.
The12-test focused command passed0.49s, including complete synthetic captures
with valid large files and failed partial transfers; both stop before storage,
retain final inventory and stay within the bound. Bounded R2 review pending.

## Reviewed R2 and Actual Single Capture

Separate GATE ACCEPTED_WITH_RISK exact R2 preflight, closing the one R1 finding.
Receipt: installed_facts_capture_review_r2.json. Independent two new regressions
passed0.26s; its whole-capture probe stopped at25MiB, no later storage/HTTP work,
and retained final inventory with INCOMPLETE. Prior rejected receipt preserved.
Executed source SHA256:
`a553e37e9bac1b5f6827fa8fe9ff40d520e7dc6005df4fc81064d03b6259eb76`.
Tests SHA256:
`c4fa5e138e7bfc389a5071784cf97facf3d19f1d863b34bb64678df28cd4eb42`.

After the operator's authorization and tool permission, ran exactly once:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
 docs/review_artifacts/companion_continuation_20261021/capture_installed_facts.py \
 --execute --approved-sha256 a553e37e9bac1b5f6827fa8fe9ff40d520e7dc6005df4fc81064d03b6259eb76
```

Observed2026-10-21T17:47:49.283840Z (13:47EDT). Exit0;5.194seconds;98 Docker
commands;93 selected files captured;6,923,555 saved payload bytes;7,094,272 file
transfer upper-bound bytes. No unreadable files, no frozen-source mismatches,
no capture error. Selected before/after inventory identical for all11 subjects.

SHOWN in this point-in-time capture:
- All43 reviewed application source entries match the actual stopped replacements.
- Installed memory archive manifest/original/derived/query-comparison hashes each
  equal the approved local archive; the archive is present, not merely assumed.
- PostgreSQL public.documents and audit_events exist; all55 frozen original
  identities match hash, URL/source/type, raw-object key and publication/fetch times
  in one read-only snapshot. This is not validation of every database row/body.
- Existing Qdrant documents collection GET reports status ok; existing MinIO
  raw-docs bucket signed HEAD returns200. No object-body integrity proof follows.
- Parent rehashed all93 saved files against the capture report, exit0.

Result directory:
docs/review_artifacts/companion_continuation_20261021/installed_facts_capture/.
Report SHA256:
`7dbda2c14b68b58d372508eda0d34e232bc9e6548bd0b7ff5327b027abbdad2b`.
The exclusive directory is consumed; do not repeat/delete it to rerun. Earlier
unverified archive/identity statements above describe the pre-capture boundary;
this section supersedes them for the exact observed bytes and database snapshot.

No container lifecycle/configuration change, application query, ingestion,
migration, scheduler/account/trading operation or credential export was performed.
Storage checks used existing in-container authentication; access/statistics logs
may reflect those reads. Normal startup/import behavior, full SDK policy and a
usable dashboard explanation are not proven by this capture. Captured evidence
is READY_FOR_INDEPENDENT_REVIEW; separate result review and SDK analysis pending.
Runtime remains INCOMPLETE; no startup or cutover authorized.

## Actual SDK Policy Finding

Separate AUDITOR Plato checked actual captured bytes, not host SDK versions:
14/14 historical memory SDK source hashes equal the prepared image's files.
That closes the specific old-memory-versus-prepared-memory byte-binding gap for
those files, not every image's complete import/entrypoint closure.

SHOWN conditional source defect: captured73_client.py:403 registers the S3 region
redirector separately from standard retries. Captured77_utils.py:1720 registers
needs-retry.s3; its error branch re-resolves an endpoint and returns0 at1838 to
request replay, and can issue a fallback HeadBucket at1865. Captured66_endpoint.py
accepts any non-None event result as retry authorization. Standard attempt-limit
refusal does not veto the separate handler. Parent read these same source paths.

This does not establish that a redirect happened, that traffic escaped to another
host, that proxy suppression failed, or that this caused the old runtime failure.
The capture itself used the reviewed curl HEAD, not the SDK client. Its successful
read-only storage checks are not contradicted by this conditional policy defect.
Detailed hashes/line references: sdk_actual_policy_finding.json.

Next corrective scope: narrow offline repair of restricted S3 replay/redirect
behavior and representative error-response regressions, followed by separate
review. Preserve normal non-restricted behavior and all current captured/prepared
artifacts. No blanket installed-policy approval or another native attempt follows.

## Final Evidence Disposition

Separate GATE ACCEPTED_WITH_RISK the saved capture facts only. Receipt:
installed_facts_capture_result_review.json. It independently rehashed93 files,
recomputed43 frozen-source matches, checked exact11subject before/after identity,
preservation/network bindings, installed archive hashes and the saved storage
response shapes. Report/payloads remain unchanged; reviewer made no native calls
and repeated no tests. Its reproducible assertion command is in the receipt.

Read-only capture objective is complete; do not repeat it. The S3 policy defect
above remains a separate corrective task. Runtime/explanation objective remains
INCOMPLETE, and prepared applications remain stopped. Nothing was deployed.

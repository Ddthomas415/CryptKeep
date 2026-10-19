# Companion installation command and credential-wiring contract

Active role: DIRECTOR. Risk HIGH. READY_FOR_INDEPENDENT_REVIEW.
This is an offline command specification, NOT an executable or authorized
installer. UNKNOWN_ENV for every Docker command below. No command was run.
It supplements `companion_installation_plan_20261016.md`; lifecycle source repair
has separate scoped acceptance and does not grant installation permission.

## Fixed scope and command conventions

CLI: `/Applications/Docker.app/Contents/Resources/bin/docker`.
Endpoint: `unix:///Users/baitus/.docker/run/docker.sock`.
Every argv begins `[CLI, "--config", EMPTY_CONFIG, "--host", ENDPOINT]`.
EMPTY_CONFIG is a private new empty directory, never the user's Docker config.
All operands below are typed, validated data, never shell substitutions. Names
are limited to the four existing application services and collision-checked
rollback names. IDs/network IDs must come from a fresh reviewed inventory.
No shell command strings, Compose up/down, registry login, pull, exec, start,
stop, prune, volume removal, credentials in argv, or blanket inspection output.

The query transport's allowlist stays unchanged: it refuses these installation
operations by design. Do not bypass that refusal, monkeypatch its authorization,
or use a subprocess escape inside the query controller. An installation runner
requires its own reviewed implementation and explicit named operational approval.

## Proposed command sequence

| Order | Argv suffix / action | Required evidence before advancing |
| --- | --- | --- |
| 1 | `container inspect --format SELECTED_PUBLIC_FIELDS OLD_ID` for seven targets | Exact identity/state/mount/port/network and source baseline; only application targets can change |
| 2 | `image inspect --format SELECTED_PUBLIC_IMAGE_FIELDS PARENT_IMAGE_ID` | Parent present locally, known entrypoint/user/workdir; source provenance and no unpreserved writable-layer changes |
| 3 | `image tag PARENT_IMAGE_ID ATTEMPT_PARENT_TAG` for each application | Unique local tag, no collision; public rollback image reference retained |
| 4 | `build --pull=false --network=none --iidfile PUBLIC_IID_FILE --file DOCKERFILE MINIMAL_CONTEXT` | Reviewed installed builder mode demonstrably uses local parent without network resolution; otherwise refuse BEFORE any rename |
| 5 | `image inspect --format SELECTED_PUBLIC_IMAGE_FIELDS NEW_IMAGE_ID` | Immutable new ID, reviewed source context hash, dependency and image-diff evidence; successful build alone is insufficient |
| 6 | `container rename OLD_ID ROLLBACK_NAME` | Original still exited and exact identity; journal intended rename, then confirm actual name/ID even on CLI timeout |
| 7 | `network disconnect NETWORK_ID OLD_ID` | Original endpoint/aliases recorded for rollback; no other network affected; confirm detach |
| 8 | `container create --name ORIGINAL_NAME --network NETWORK_ID --network-alias SERVICE_ALIAS --restart=no --env-file /dev/stdin PUBLIC_CREATE_OPTIONS NEW_IMAGE_ID COMMAND_ARGV...` | Reviewed reconstruction and private env pipe described below; creates only, never starts |
| 9 | `container inspect --format SELECTED_PUBLIC_FIELDS NEW_ID` plus allowlisted source archives | Exact new image/metadata, created state, zero restarts, never-started timestamp, correct aliases; no storage target changed |

Build context contains only explicit regular source files whose hashes are
reviewed. Dockerfile is exactly `FROM ATTEMPT_PARENT_TAG` plus explicit COPY
instructions for those files; no RUN, ADD, remote source, dependency installation,
wildcard COPY or `.env`. `--network=none` does NOT by itself prove that a builder
will avoid registry metadata requests. Installed builder feasibility must be
established separately, not guessed or worked around with network access.
Four derivative images use four respective parents, not one guessed common image.

PUBLIC_CREATE_OPTIONS must encode reviewed loopback publications, read-only
mounts, user/workdir/entrypoint/healthcheck and resource/security settings without
secret-bearing values. Do not replay every inspect key as a CLI flag or silently
discard unsupported settings. Existing labels, anonymous mounts, capabilities,
ulimits, DNS/extra-host settings, entrypoint arrays and healthchecks require exact
reconstruction or a documented refusal. No effective command may include secrets.
Retain normal-route code and the existing read-only `/repo` mount, with frozen
importable source evidence; a dirty broad mount is not an approved source bundle.

Use the existing aliases: audit-log, risk-stub, memory-retrieval, orchestrator;
loopback ports8009,8008,8007,8002 respectively. Old application containers remain
stopped rollback objects. TimescaleDB, Qdrant, MinIO and their image/volume
identities are outside the replacement set. No helper containers may be created
to inspect sources or snapshot storage under this contract.

## Secure configuration wiring

Do not read `.env`, discover alternate tokens, or create plaintext env files.
The future explicitly authorized runner may request ONLY each original target's
effective Config.Env through a private subprocess stdout pipe into one bounded
child's memory. This is credential access and requires explicit authorization;
the earlier selected-metadata inspection did NOT perform or authorize it.
Never emit the raw response, values, hashes, command echo, debug traces or an
exception containing it. Disable core dumps for that process before credential
read. No subprocess receives the inherited host environment or Docker config.

Validate bounded unique KEY=VALUE records before renaming anything. Keys must
match `[A-Za-z_][A-Za-z0-9_]*`; values must be representable losslessly by the
installed env-file parser. Refuse NUL, CR, LF, encoding ambiguity and unknown
parser behavior; do not trim or rewrite a credential to make it fit. Compare
representable values byte-for-byte in offline fixtures, including spaces, #,
equals signs and quotes. Duplicate or missing required fields fail preparation.

Preserve credential values unchanged. Apply only reviewed nonsecret overrides:
NO_TRADING=true, OPENAI_API_KEY empty, MEMORY_READ_ONLY_STARTUP=true,
REQUEST_TIMEOUT_SECONDS=2, PYTHONDONTWRITEBYTECODE=1, and the adapter's exact
internal service/storage origins and namespace names. Review overrides against
each target, not a blanket claim that all settings are already correct.

Feed env records directly to `container create` via an anonymous stdin pipe;
`--env-file /dev/stdin` is a proposed installed-CLI interface requiring synthetic
parser and descriptor verification before use, not a verified working command.
Do not fall back to a disk env file, argv assignments, shell pipeline, user
environment or logging. Drain bounded stdout concurrently to avoid pipe deadlock;
stderr is discarded and failures use fixed sanitized reason codes. Close owned
descriptors and clear references on every path. No forensic memory-erasure claim.
Docker necessarily persists configured environment in container metadata as it
does today; this is not a promise of secret-free daemon storage.

## Deadlines, recovery and operator decision

One installation attempt,300s total, with180s for preparation/replacement and120s
reserved for reconciliation/rollback; per-operation cap min(60s,remaining phase).
No retries. A timed-out create/rename/disconnect may have happened: inspect the
exact IDs/names and attempt label before taking ownership or cleaning up. When
ownership cannot be established, leave objects untouched and report INCOMPLETE.
Never declare rollback complete because only the client process terminated.

Rollback order: remove only proven attempt-owned, never-started replacements
using `container rm NEW_ID` WITHOUT force/volume flags; restore original names
using `container rename OLD_ID ORIGINAL_NAME`, then `network connect --alias
ORIGINAL_ALIAS NETWORK_ID OLD_ID` with all supported original endpoint settings.
Verify original identities, states and metadata. Refuse running/ambiguous objects.
If endpoint restoration needs unsupported settings, resolve before installation,
not during rollback. Record partial recovery truthfully; no automatic second pass.

Leave all seven targets stopped on successful installation. Generate new public
identity/config/source evidence for independent review, not automatic acceptance.
Build cache/daemon records may remain. Data-volume backup/integrity is not proven.
Only after installed policy/namespace preparation and approval can the separate
single-query controller be invoked; this contract contains no invocation for it.

Required decision is specifically permission for an implementation and eventual
operation that builds four local derivative images, renames/disconnects four
stopped application containers, privately reads their existing configuration,
and creates four stopped replacements. It is NOT permission to run services,
change storage, access trading accounts, or relax the normal research scope.
No executable installer exists yet; this document does not imply otherwise.

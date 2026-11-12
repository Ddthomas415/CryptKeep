# R3 disposable Linux process-validation proposal

Bot relation: BOT_RULES; runtime configuration not checked.

Planning and offline packet only. No daemon, container, server or alert operation
is authorized by this document. R3 remains INCOMPLETE. The accepted production
source is unchanged; this packet tests its native process primitives, not an
installed watcher or the research backend.

## Decision and scope

Use one disposable local Linux container rather than the production server or
the existing research containers. Run seven stdlib-only synthetic fixtures:
normal cycle, cycle timeout, active cancellation, parent death before/after the
launch gate, inherited lifetime-lock exclusion, and supervisor SIGTERM. Fixtures
create their own temporary files/processes only. The harness uses Linux subreaper
semantics to reap its own orphaned fixture children; this is not a production
supervisor change. [Linux manual](https://man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html)

`scripts/research/build_group_a_linux_probe_packet.py` builds an exclusive-output,
deterministic archive containing exactly 21 regular Python sources plus a
generated SHA256 manifest. No repo tree, `.git`, `.venv`, configuration, accounts,
credentials, state databases, market data or private Docker settings enter it.
The 20 dependency sources are the observed supervisor import closure; the 21st
is the native fixture harness. This narrow closure imported with `-I -S -B`
without site packages/PyYAML. This does not certify the full application's
dependency environment.

The packet checker verifies members/hashes and imports without running kernel
tests. `--run-linux-fixtures` requires Linux, Python 3.12 and a nonroot UID;
this Mac returns exit 2 rather than marking skipped kernel fixtures as success.
The seven fixtures have not run on Linux yet.

## Current local evidence

Checked 2026-11-05: Darwin 27.2.0 arm64. Docker CLI is an arm64 executable at
`/Applications/Docker.app/Contents/Resources/bin/docker`; Docker.app metadata
says 4.97.0. Captured CLI SHA256:
`3afd9fef319616a55f4ee837ea6dfa3919f8696254c6a3ea421546dbdc9c1198`.
That differs from the October checkpoint. Drift alone is not a repair diagnosis;
no signature or daemon-health conclusion is made. Socket pathname
`/Users/baitus/.docker/run/docker.sock` exists; reachability is UNVERIFIED.

No Docker/Podman command, context/config read, credential helper, existing
container query, image pull/build or startup was performed. No cached clean
Python image has been identified. Native execution is UNKNOWN_ENV until the
bounded preflight below passes, not a universally safe shell recipe.

## Proposed single authorized attempt

If separately authorized, include preflight and at most one fixture container in
one attempt, with no automatic retry. If any prerequisite fails, stop rather
than pull an image, install packages, repair/restart Docker, use an app image,
or switch to the server.

1. Recheck packet/CLI fingerprints. Use the fixed local Unix endpoint and a new
   empty Docker config directory, a cleared client environment, no inherited
   context/TLS/auth variables, no credential helper and no `.env` reads.
2. At most two read-only daemon calls: selected server OS/architecture/API
   metadata and `image inspect python:3.12-slim` restricted to image ID,
   RepoDigests, OS and architecture. Require an existing cached Linux arm64
   Python image with a `python@sha256:` repository digest; record its immutable
   image ID before creation. Do not print image/container environment values.
   Metadata alone is not independent publisher authentication; do not claim it
   verifies a cryptographic supply chain. Missing/ambiguous identity stops.
3. Extract only the reviewed regular-file archive into a new disposable source
   directory. Verify its exact member list and hashes. Source directories are
   0755/readable to the fixture UID; files contain only public code. Bind only
   this source directory, read-only, at `/probe`; never bind the repo/home or
   Docker socket into the fixture.
4. Create exactly one uniquely named/labelled container, record its immutable
   ID, and use that ID for every subsequent action. Select the recorded image
   ID, never the mutable tag. Override the entrypoint with
   `/usr/local/bin/python3`; invoke `-I -S -B
   /probe/scripts/research/verify_group_a_linux_processes.py --run-linux-fixtures`.
   Require `--pull=never`, `--network=none`, no published ports, read-only root,
   `--user=65534:65534`, `--cap-drop=ALL`, `--security-opt=no-new-privileges`,
   `--pids-limit=32`, `--memory=256m`, `--cpus=1`, `--init`, and only a 64 MiB
   `/tmp` tmpfs (rw,noexec,nosuid,nodev,mode=1777). No privileged mode, host
   PID/network namespace, named volume, service/manager access or restart policy.
5. Start/attach once. Capture bounded fixture stdout/stderr and exit status.
   Success requires seven tests, zero failures/errors/skips, exit zero, and
   complete parent-death/cleanup assertions. Refusal, timeout or missing receipt
   is INCOMPLETE/failure, not a passing platform skip or permission to retune.
6. Capture only the owned ID's selected state/labels, then stop it if necessary
   and remove it only after exact ownership and stopped state are established.
   Never use broad stop/prune/remove commands or affect pre-existing containers,
   images, volumes, collectors, settings or processes. Preserve the receipt if
   cleanup is unconfirmed; report the exact remaining ID, not guaranteed rollback.

Bounds proposed: 180 seconds overall elapsed target, 10 seconds per Docker
control/metadata call, 90 seconds for fixtures, with at least 40 seconds reserved
for owned cleanup/final evidence. Initial packet checks and final evidence-file
writes are local. Cap captured output at 64 KiB; overflow fails and triggers
owned cleanup. Native/daemon uninterruptible operations can exceed a target;
never claim a hard real-time or guaranteed cleanup bound. No command is run
merely to check whether it works before authorization.

Docker's [create](https://docs.docker.com/reference/cli/docker/container/create/)
and [run options](https://docs.docker.com/reference/cli/docker/container/run/)
were checked for these controls. A create is itself a daemon mutation, even if
the container is stopped; it is not part of today's read-only inspection.

## Proof still separate

Even seven passing fixtures would establish process behaviour only in that
disposable Linux environment. It would not prove systemd effective units,
production read-only SQLite/WAL mounts, host permissions, sustained 26-week
capacity, actual Slack acceptance, owner receipt or trading readiness. No actual
staging/commissioning is bundled into this test authorization.

What do I know that could change the owner's decision that I have not yet said?
The cached clean image and daemon availability are still unknown. If absent,
this attempt must stop without downloading or substituting an existing app
image; the packet remains reusable for another separately approved Linux target.

## Dated execution update: November 10 New York / 2026-11-11T02:11:24Z

The owner separately approved one official-image pull and test, then directed
continuation after Docker became available externally. The original packet ran
seven Linux arm64 fixtures with zero failures/errors/skips; its owned container
was inspected exited/0 and removed. This supersedes the historical "not run"
statement above for this disposable environment only. See
[native result and limits](NATIVE_RESULT_20261110.md) and the raw receipt. No
production deployment, systemd/namespace proof or actual alert delivery follows.

What do I know that could change the owner's decision that I have not yet said?
The image prerequisite and disposable Linux run are now satisfied; real host
provisioning/capacity/delivery remain separate, with no operational approval inferred.

# Single source-only image proof

Date: 2026-10-17, America/New_York. Active role ENGINEER; risk HIGH.
Implementation proof: READY_FOR_INDEPENDENT_REVIEW. Explanation runtime: INCOMPLETE.

## SHOWN

One actual build succeeded on existing Docker Engine 29.8.2 at 21:05:54-58 New
York (October 18 UTC in the receipt). No retry. Executed command:
`./.venv/bin/python -B /private/tmp/cryptkeep_source_build_proof_20261017.py`.
Exact script archived as `proof_runner.py` beside `receipt.json` and `context.tar`
in `docs/review_artifacts/companion_source_build_20261017/`.

Build argv: `docker build --quiet --pull=false --network=none -`, with explicit
local daemon, hash-verified native CLI, empty temporary CLI config, minimal
environment and DOCKER_BUILDKIT=0. No user Docker credentials loaded.
The 10,240-byte context contains only Dockerfile and 2,511-byte public probe.py.
Dockerfile contains FROM and one COPY, no RUN, ADD or package installation.

Parent: `sha256:a9b205b41e2b7499497e346e49cde29890b36f4d4b1dfee89fb32f4f726953ad`.
Built: `sha256:9ce96d0b388a6ba1f9375fe31209c56dd5d22d27ea4cf5dd86487ba081341aa7`.
The parent's eight layer digests are an unchanged ordered prefix, followed by
exactly one additional layer. Neither image has ONBUILD instructions.

All seven original container IDs/images/states/restart counts/policies match
before and after: exited, zero restarts, policy no. Retrospective Docker container
events returned none during the attempt. This is bounded observation, not global
daemon non-interference proof. No install, rename, detach, create/start/stop,
storage mutation, service query, account, scheduler or trading command invoked.
No existing container environment values requested.

Retained local artifacts: the proof image/cache and parent tag
`cryptkeep-proof-parent:oct17-20e49998928c4c47`. No prune or removal performed.

## Review and verification

Independent preflight found the diagnostic could execute final Docker inspection
after a CLI hash failure. Corrected: every call, including final checks, requires
successful hash verification. Readiness now follows final checks. Source reading
is bounded, regular-file checked, no-follow opened and hash pinned.
Independent static re-review: ACCEPTED_WITH_RISK for this bounded attempt, not
the complete installer. Reviewer did not run Docker.

Post-run independent artifact review: ACCEPTED_WITH_RISK for the recorded build.
Reviewer checked the two regular context members, archive/source hashes, eight
parent layers plus one, identical seven-container metadata, exactly one build/tag,
no lifecycle argv and empty returned event list. It did not recollect daemon
evidence or rerun the negative mock. This narrow disposition does not upgrade the
whole installer or explanation runtime. Frozen runner/receipt/context unchanged.

Syntax parsed. Offline negative check: incorrect CLI hash with subprocess.run
mocked; PASS, zero subprocess calls including final checks. No full suite or
service tests. Existing production installer source unchanged in this scope.

## Limits and next boundary

VERIFIED_ENV: this CLI/daemon built this exact context with the inspected local
parent's layer prefix. Not proof of all four application builds, copied-source
runtime behavior, source completeness, installation, or startup.
One material assumption: no concurrent actor removed or retargeted the unique
parent tag between verification and build.

Registry isolation UNVERIFIED. `--pull=false` prefers local, not a hard fallback
prohibition; `--network=none` controls RUN networking, not registry resolution.
No registry traffic trace collected, so zero external requests is NOT claimed.
[Docker flags](https://docs.docker.com/reference/cli/docker/image/build/) and
[Moby prefer-local selection](https://github.com/moby/moby/blob/v28.5.1/builder/dockerfile/imagecontext.go#L24-L38)
support this distinction; upstream source is not an exact attestation of the
installed Engine 29.8.2. Retrospective events are also bounded by daemon history.

Next: freeze/review complete four-service reconstruction and mounted import/source
coverage for the existing installer. No accepted operational manifest exists.
Replacement, real credential wiring, startup and explanation query remain outside
this proof's authorization. Runtime remains INCOMPLETE.

SHA256:
```text
proof_runner.py 3b1ab5a72def44a33866c69f917e864d6fff30933ff0fc1a6be8703164649fb8
receipt.json    ba89c11cd8215396859086fbe756bc3f666d74569de4388e2306c0065ec7c1f0
context.tar     a8d42e04694b9fc7cbdcb4a9ba6b312cb99507c4c9447a21031c65622672795e
```

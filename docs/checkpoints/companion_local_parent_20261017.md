# Immutable local-parent builder correction

Client date October17 New York. Active role ENGINEER; risk HIGH (installation
boundary). Implementation handoff READY_FOR_INDEPENDENT_REVIEW. No build,
container mutation, private configuration read or startup authorized/performed.

## Finding and chosen path

SHOWN: the previous backend generated a temporary repository tag, then used it
in FROM. pull=false prefers a local image but may enter the registry fallback
when the tag is missing; network=none governs RUN, not registry resolution.
The old proof build remains evidence for its original tag-based command only.

Read-only native CLI version selected only Server.Version and Server.GitCommit:
29.8.2 / 8af9fe3. Native help with DOCKER_BUILDKIT=0 confirmed legacy dispatch;
plain help selects buildx, so the clean child environment is essential. No
credential values, raw inspect, image/cache or container lifecycle was accessed.

Chosen minimal correction: FROM the full bare64-hex parent ID, not a repository
tag and not sha256:hex. The reviewed legacy implementation resolves that ID
locally. Its missing-image pull path parses it as a named reference first;
the pinned reference parser rejects bare64-hex strings before registry I/O.
Both classic and containerd image-store source paths were inspected. This is
source-control-flow evidence, not a live no-egress trace or daemon binary audit.

The backend now checks the exact observed Engine version/commit before private
preparation and again before each build. Different/malformed identity refuses.
It no longer lists or creates temporary parent tags. Existing source hashes,
minimal FROM/COPY-only context, parent ONBUILD refusal, CLI identity check,
private env/label handling, stopped-only lifecycle and rollback are unchanged.
The child environment still forces DOCKER_BUILDKIT=0 and the explicit daemon,
without inherited DOCKER_CONTEXT or user Docker config. No new dependency,
command-line option, service, pipeline or policy acceptance was introduced.

## Primary source evidence

The observed server commit is an abbreviated self-report, not independent binary
attestation. The source references below were opened in this investigation.

- [Engine legacy image resolution](https://github.com/moby/moby/blob/8af9fe3/daemon/images/image_builder.go#L144): named-reference parsing precedes the pull call.
- [Engine containerd image resolution](https://github.com/moby/moby/blob/8af9fe3/daemon/containerd/image_builder.go#L128): the same parse-before-pull ordering.
- [FROM dispatch](https://github.com/moby/moby/blob/8af9fe3/daemon/builder/dockerfile/dispatchers.go#L254): expanded base identifier is passed to image resolution.
- [Engine dependency pin](https://github.com/moby/moby/blob/8af9fe3/go.mod#L44): distribution/reference v0.6.0.
- [Pinned parser](https://github.com/distribution/reference/blob/v0.6.0/normalize.go#L50): bare64-hex rejected by ParseNormalizedNamed; ParseAnyReference accepts it as an image digest.
- [Docker legacy-builder selection](https://docs.docker.com/reference/cli/docker/image/build/): DOCKER_BUILDKIT=0 opts out of Buildx.

Earlier v28.5.1 source was used to locate the relevant logic, then the actual
observed commit was inspected. It is not silently substituted for the server.
Two guessed source paths returned cache-miss errors; corrected paths above
were read successfully. No claim that failed fetches provided evidence.

## Verification

Six new/strengthened cases failed on the previous implementation (6 failed,
43 deselected). After correction the installer module passed49 cases; two
additional regressions cover missing local parent and forced legacy/clean env.
Final command:
```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_companion_installer.py tests/test_companion_runtime_wiring.py
```
SHOWN:55 passed0.55s, synthetic source/build/controller fixtures only. Cases
check bare pinned-ID FROM, absence of tag commands, wrong/malformed Engine
refusal before private preparation/build, missing parent refusing before build,
and no inherited BuildKit/context override. No full repository suite.

Changed source SHA256:
```text
scripts/research/companion_install_docker.py 8912c438204c87b15c081b72ccfbe016a8150b17abc9867ec1b253585a4ee22d
tests/test_companion_installer.py eb81f1de677877ad89aa006fa417d95a6895c9d2a14486fe4f5bbc432d709ad7
```

Previous frozen proof/hash records are preserved. They describe the previous
source; the two changed paths no longer match that older snapshot. The batch
closeout's11-hash match remains a historical observation before this new delta,
not a claim that today's modified files still have the old hash. Reviewed
application sources/recipes/data remain unchanged. Files are untracked, not
claimed committed, published or deployed.

## Limits and next proof

ASSUMPTION: the locally self-reported server version/commit represents the
reviewed upstream behavior. A modified server can spoof this; this check does
not establish a trusted daemon or binary provenance. Scope is registry fallback
for this generated FROM/COPY build, not unrelated daemon background traffic.

UNVERIFIED: an actual successful build with a present bare-ID parent and an
actual missing-parent refusal on this daemon. No negative build was run merely
because it should fail: a build remains an operational request. Independent
review must assess this delta before an explicitly authorized, bounded actual
proof. Do not set builder_local_only=true automatically from this checkpoint.

Mounted import/dependency behavior, accepted whole-install policy, installation,
private transfer and genuine cited explanation remain INCOMPLETE. No scope
reduction, account/schedule/strategy/risk/trading change or profit claim.

## Independent disposition

Separate AUDITOR: ACCEPTED_WITH_RISK for the bounded offline implementation,
no concrete defect found. Independently55 passed0.50s on the exact command and
both changed-file hashes matched. Reviewer did not reopen upstream URLs or run
Docker: the source analysis above is the parent's SHOWN investigation, CLAIMED
to that reviewer. The missing-parent regression stops at mocked inspection; it
does not simulate a daemon losing its parent between inspection and build.
Actual installed positive/negative proof and network behavior remain UNVERIFIED.
No reviewed code/test changed after disposition; no operational approval follows.

Subsequent native positive/negative proof is recorded separately in
`companion_local_parent_proof_20261017.md`: one bare-ID present-parent build
returned the expected derived image; a confirmed-missing bare-ID build returned
the parser refusal; seven selected original snapshots matched. Saved evidence
independently ACCEPTED_WITH_RISK. This supersedes the absence of actual proof
for that diagnostic only, not whole-install/import or general network isolation.

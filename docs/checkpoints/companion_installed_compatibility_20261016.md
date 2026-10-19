# Installed compatibility: read-only evidence and concrete gaps

Active role AUDITOR. State INCOMPLETE. Installation/query not authorized.
Evidence recorded approximately21:49-21:50UTC,2026-10-16.

## Findings

1. SHOWN: installed QdrantClient constructor at captured source line112 copies
   kwargs before forwarding them to QdrantRemote. The reviewed local memory
   repair passes a preconstructed HTTPTransport in those kwargs. A no-network
   host deepcopy probe failed with TypeError; the host HTTPX transport file hash
   equals the installed captured file hash. Independent static review confirmed
   the ordering and supported-kwargs path. The whole installed constructor was
   NOT executed; its exact first exception remains UNVERIFIED. This is a concrete
   compatibility concern in our local repair, not a reason to upgrade dependencies
   or describe the previously mocked constructor tests as installed proof.
2. SHOWN: MinIO's /bin/sh is a link to bash. Both /bin/bash and /usr/bin/curl
   are present as regular ELF files. The existing archive reader deliberately
   rejects links, while adapter source coverage requires /bin/sh. That combination
   cannot certify this observed layout unchanged. Prefer an explicit reviewed
   regular bash path, preserving strict archive checks and the storage image;
   do not enable general link-following or rebuild MinIO to avoid the mismatch.
3. SHOWN: inspected application source/configuration still predates the repair.
   Both inspected shared/probe.py paths were unavailable. All four application
   timeout comparisons differ from2s and no read-only-startup variable appeared.
   All four did match NO_TRADING=true and empty OPENAI_API_KEY. Credential fields
   were nonempty, which proves presence only, not correctness or safe submission.
4. SHOWN: PostgreSQL PG_VERSION contains16. The captured entrypoint checks that
   marker before its initialization branch. This does not prove schema integrity,
   absence of every startup write, or that namespaces exist.

## Collection and independent scope

Seven pinned stopped targets inspected using a selected metadata template.
Only exact expected-value comparisons and presence booleans left Config.Env;
no raw values or secret hashes exported. Initial/final sanitized inventory
matched. Read28 allowlisted file paths, including14 SDK sources and version/
binary metadata. Public source snapshots and hashes are preserved in
`docs/review_artifacts/companion_installed_policy_20261016/report.json`.

The first curl archive exceeded the2.1MB read cap, not a missing-file result.
A bounded follow-up found the3,346,056-byte ELF curl and1,366,952-byte ELF bash;
their hashes are in binary_followup.json. Neither was executed. MinIO remained
exited. Docker build --help documented pull/network flags only: no build or
registry-free-resolution proof. Parent collection took1.37s, not whole task time.

Separate AUDITOR read the captured Qdrant/HTTPX chain and found the deepcopy
obstacle before otherwise supported forwarding. It did not execute constructors,
tests, Docker or credentials and did not approve a whole-install manifest.
Host-only copy probe recorded separately; no copied installed code was imported.

VERIFIED_ENV: read-only native CLI/selected metadata/archive collection and local
host copy probe. UNKNOWN_ENV for actual installed constructors, binary features,
builder resolution, env-file parser/descriptor fidelity and service execution.
No exec, build, rename, create, start/stop, credential-value extraction, storage
query, account, schedule, strategy, trading or explanation request.

## Disposition and next action

Produced a non-executable evidence candidate, manifest_candidate.json, explicitly
INCOMPLETE and incompatible with the installer's accepted-plan schema. No real
accepted policy manifest was fabricated to turn failed/unknown gates true.

Next smallest repair is offline: correct Qdrant transport construction against
the captured constructor behavior and bind MinIO verification/execution to the
observed regular shell binary, with focused regression tests and independent
review. This is a recommendation, not a change performed during this read-only
stage. Preserve all storage images, installed state and prior evidence. Builder,
parser, provenance/reconstruction and namespace/citation evidence still need
their respective proof before any installation/query decision.

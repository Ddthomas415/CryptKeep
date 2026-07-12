# CryptKeep Supply-Chain and Release Verification Policy

Status: `POLICY_DOCUMENTED` · Tooling: `scripts/check_supply_chain.py` (proof-ready)

## Purpose

Define the minimum dependency, build, and release verification expected before
shipping operator-facing artifacts or approving capped-live server deployment.
This policy does not add a new CI gate by itself.

## Current Boundary

SHOWN:

- Runtime dependencies are pinned through `requirements-pinned.txt`.
- CI installs pinned runtime dependencies in the main validation workflow.
- Release workflows already produce artifact hash manifests for distributable
  outputs.
- Signing/notarization is optional and gated by secrets; unsigned builds remain
  allowed for current paper/research operation.

SHOWN (2026-07-10): `scripts/check_supply_chain.py` verifies exact-pin
integrity (rejects ranges/unpinned/conflicting pins within and across the
pinned files), verifies the installed environment matches pins, runs a
best-effort `pip-audit` lane when requested (`--strict-audit` for the
capped-live posture), and writes provenance evidence (git SHA + dirty
flag, requirement-file sha256s, all verdicts) via `--evidence-dest` for
the launch packet.

UNVERIFIED:

- No hash-locked `--require-hashes` install path is enforced.
- No dependency vulnerability audit is a required release gate.
- No SBOM is generated as a required artifact.
- No recurring release attestation has been reviewed for live/capped-live use.

## Paper/Research Policy

For paper and research operation:

- pinned dependencies are sufficient;
- unsigned desktop artifacts are acceptable;
- optional signing/notarization may run when secrets are present;
- dependency-audit failures should be reviewed but do not block paper evidence
  unless they affect credential handling, remote execution, authentication, or
  trading/execution paths.

## Capped-Live Policy

Before capped-live approval, the launch packet must include:

- dependency lockfile freshness review;
- vulnerability audit output or an explicit accepted waiver;
- final artifact hash manifest;
- signed/notarized artifact proof if desktop artifacts are part of the live
  operating surface;
- verification that release/signing secrets are present only in GitHub Actions
  or the approved server secret model;
- a record of the exact Git SHA used for deployment.

If a dependency scanner is adopted, prefer adding it as an explicit
release/live-readiness gate rather than silently expanding the fast PR path.

## Accepted Waiver Path

A vulnerability or missing verification step may be waived only when the
decision record states:

- package or artifact affected;
- severity and exploit path;
- whether the affected code is reachable in paper, shadow, or live mode;
- compensating controls;
- expiry date for the waiver;
- owner responsible for revisiting it.

Waivers must not be indefinite for live/capped-live operation.

## Future Implementation Options

Candidate gates, in increasing strictness:

1. `pip-audit` or equivalent advisory audit over pinned requirements.
2. SBOM generation for release artifacts.
3. Hash-locked dependency installs for release jobs.
4. Signed provenance/attestation for release artifacts.

Do not add all four at once. Add the smallest gate that answers the current
risk question, record expected runtime cost, and keep docs-only PR fast paths
unchanged unless the branch-protection policy is deliberately updated.


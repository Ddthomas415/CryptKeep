# Supply-Chain Local Evidence - 2026-08-31

Status: local pin/environment evidence recorded; host vulnerability audit and
SBOM/hash-lock decisions remain open.

## Scope

- SHOWN: local checkout was clean and aligned with `origin/master`.
- SHOWN: checked commit was `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`.
- SHOWN: this checkpoint did not run a dependency vulnerability audit.
- SHOWN: this checkpoint did not generate an SBOM.
- SHOWN: this checkpoint did not change CI, release policy, dependencies, host
  packages, services, campaigns, gates, or execution behavior.

## Commands

```bash
make check-supply-chain-json
make record-supply-chain
```

## Result

`make check-supply-chain-json` reported:

- `git_sha=c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`
- `git_dirty=false`
- `pin_integrity.ok=true`
- `pin_integrity.pin_count=83`
- `environment.ok=true`
- `environment.checked=83`
- `environment.mismatches=[]`
- `environment.not_installed=[]`
- `vulnerability_audit.ran=false`
- `vulnerability_audit.reason=not_requested`

`make record-supply-chain` wrote:

- `.cbp_state/data/supply_chain/supply-chain-evidence-20260831T053704Z.json`

## Remaining Release-Policy Work

This local artifact narrows the current state for the latest merged SHA, but it
does not close capped-live release policy. Remaining decisions/proofs are:

- run or explicitly waive host-side vulnerability audit for the deployed SHA;
- decide whether SBOMs become required release artifacts;
- decide whether hash-locked installs become required for release/live paths.

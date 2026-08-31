# Hetzner Supply-Chain Audit Attempt - 2026-08-31

Status: read-only host proof attempt; vulnerability audit still open.

## Command

`tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/check_supply_chain.py --audit --json'`

Execution context: approved out-of-sandbox read-only Tailscale SSH command.

## Result

SHOWN:

- Host checkout SHA: `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`.
- Host dirty state: `false`.
- Pin integrity: `ok=true`, `pin_count=83`, `problems=[]`.
- Environment alignment: `ok=true`, `checked=83`, `mismatches=[]`,
  `not_installed=[]`.
- `requirements-pinned.txt` sha256:
  `bd1403c707751d3e3bc8e5803b12b72aa70ae62020dc08d58c614d15064e93bb`.
- `requirements-dev-pinned.txt` sha256:
  `a2ab712551797b1b34a85e38144384ce59067606b019926539fcccb10821bee6`.
- Vulnerability audit: `ran=false`, `reason=pip_audit_unavailable`.

## Interpretation

This confirms the host virtualenv remains aligned with the pinned dependency
set at the checked host SHA.

This does not close the capped-live vulnerability-audit proof. The host cannot
produce that proof until `pip-audit` is available on the host or the operator
explicitly waives the vulnerability-audit requirement.

The host checkout was at `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e` when this
command ran. Current master had advanced by the docs-only paper campaign status
checkpoint; no runtime, dependency, service, or config drift is implied by that
docs-only difference.

No service restart, package install, deploy, config change, or campaign change
was performed.

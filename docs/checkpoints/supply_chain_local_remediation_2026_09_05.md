# Supply-Chain Local Remediation Checkpoint

Date: 2026-09-05 UTC

Status: READY_FOR_INDEPENDENT_REVIEW.

## Scope

This checkpoint records a local supply-chain vulnerability remediation against
the pinned Python dependency set.

It does not install packages on Hetzner, change service runtime configuration,
restart services, change live trading, alter campaign manifests, or modify
promotion gates.

## Finding

Command:

```bash
./.venv/bin/python scripts/check_supply_chain.py --audit --json
```

Before remediation, SHOWN on local master `9aecbaced`:

- pin integrity: `ok=true`
- installed environment: `ok=true`
- vulnerability audit: `ran=true`
- `vulnerable_count=2`
- findings:
  - `gitpython==3.1.58`, fixed by `3.1.59`
  - `tornado==6.5.7`, fixed by `6.5.8`

## Remediation

Pinned files updated:

- `requirements-pinned.txt`
  - `gitpython==3.1.59`
  - `tornado==6.5.8`
- `requirements-dev-pinned.txt`
  - `gitpython==3.1.59`
  - `tornado==6.5.8`

Local venv was updated only for verification:

```bash
./.venv/bin/python -m pip install GitPython==3.1.59 tornado==6.5.8
```

## Post-Remediation Verification

Command:

```bash
./.venv/bin/python scripts/check_supply_chain.py --audit --json
```

SHOWN on the modified working tree:

- pin integrity: `ok=true`
- installed environment: `ok=true`
- vulnerability audit: `ran=true`
- `vulnerable_count=0`
- `findings=[]`

Targeted regression:

```bash
./.venv/bin/python -m pytest -q tests/test_supply_chain_check.py tests/test_script_path_references_exist.py tests/test_operator_reporting_backlog_worklog_sync.py
```

SHOWN:

- `11 passed`

## Remaining Work

- Independent review and CI are required before merging dependency pin changes.
- After merge, repeat the supply-chain audit on the final deployed SHA.
- Hetzner still needs host-side vulnerability audit enablement or waiver:
  read-only inspection showed host pip is `26.2`, but `pip-audit` is not
  installed in `/srv/cryptkeep/app/.venv`.
- SBOM/hash-lock release-gate policy remains an operator decision.

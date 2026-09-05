# Hetzner Supply-Chain Alignment Checkpoint

Date: 2026-09-05 UTC

Active role: ENGINEER

## Objective

Record the post-merge Hetzner checkout and virtualenv alignment after the
dependency remediation merged to master, without restarting services or changing
campaign configuration.

## Boundary

- Host: `cryptkeep@100.86.128.9`
- App path: `/srv/cryptkeep/app`
- Service restart: not run
- Campaign start/stop: not run
- Strategy, gate, execution, or live-routing changes: not run
- Vulnerability audit: not run on host

## SHOWN Evidence

PR #582 merged to master and the local checkout fast-forwarded to:

```text
e38c342de fix: remediate current supply-chain audit findings (#582)
```

Hetzner checkout sync command:

```bash
ssh -o BatchMode=yes cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && GIT_SSH_COMMAND="ssh -i ~/.ssh/cryptkeep_github_readonly -o IdentitiesOnly=yes" git fetch origin master && GIT_SSH_COMMAND="ssh -i ~/.ssh/cryptkeep_github_readonly -o IdentitiesOnly=yes" git merge --ff-only origin/master && git rev-parse --short HEAD'
```

Result:

```text
Updating 9aecbace..e38c342d
Fast-forward
e38c342d
```

Hetzner dependency alignment command:

```bash
ssh -o BatchMode=yes cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && ./.venv/bin/python -m pip install -r requirements-pinned.txt'
```

Result:

```text
Successfully installed gitpython-3.1.59 tornado-6.5.8
```

Post-alignment verifier:

```bash
ssh -o BatchMode=yes cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/check_supply_chain.py --json && ./.venv/bin/python -m pip show GitPython tornado pip-audit 2>/dev/null || true'
```

Result:

- `git_sha`: `e38c342de9eb8209bdd7fdd44ca75cf757901fa2`
- `git_dirty`: `false`
- `pin_integrity.ok`: `true`
- `environment.ok`: `true`
- `mismatches`: `[]`
- `not_installed`: `[]`
- `vulnerability_audit.ran`: `false`
- `vulnerability_audit.reason`: `not_requested`
- `GitPython`: `3.1.59`
- `tornado`: `6.5.8`
- `pip-audit`: not installed in `/srv/cryptkeep/app/.venv`

Post-alignment campaign status:

```bash
make status-hetzner-gateio-challenger
make status-hetzner-binance-challenger
```

Result:

- Gate.io challenger: `1/1 running`, idle `waiting_for_next_day`, `fills=0`,
  `closed=0`.
- Binance challenger: `1/1 running`, idle `waiting_for_next_day`, `fills=0`,
  `closed=0`.

## Remaining Risk

- Host package pins and installed environment are aligned on the deployed SHA.
- Host vulnerability audit remains open because `pip-audit` is not installed
  and `--audit` was not run on the host.
- SBOM/hash-lock release-gate policy remains an operator decision.
- Existing running Python processes may continue using already-imported modules
  until their next normal restart; no service restart was performed in this
  alignment step.

Acceptance state: ACCEPTED_WITH_RISK

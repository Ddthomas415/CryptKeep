# Hetzner Dependency Alignment Runbook - 2026-08-24

## Scope

Prepare the operator-approved command sequence for aligning the Hetzner app
virtualenv with `requirements-pinned.txt`.

This checkpoint is documentation only. It does not install, upgrade, remove, or
restart anything on the host.

## Current Evidence

Read-only dry run:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && ./.venv/bin/python -m pip install --dry-run -r requirements-pinned.txt'
```

Result:

- Command exited `0`.
- No packages were installed because `pip --dry-run` was used.
- The host would install or upgrade exactly these pinned packages:
  `aiohttp==3.14.3`, `click==8.3.3`, `cryptography==50.0.0`,
  `GitPython==3.1.58`, `idna==3.15`, `pillow==12.3.0`,
  `setuptools==83.0.0`, `starlette==1.3.1`, `tornado==6.5.7`,
  `urllib3==2.7.0`.
- The host also reports `pip` can be upgraded from `26.1.2`; the local
  remediation checkpoint used `pip==26.2` because the vulnerability metadata
  listed `26.2` as the fixed version.

## Maintenance Boundary

Allowed by this runbook after explicit operator approval:

- Write a pre-change `pip freeze` file under `/tmp/cryptkeep_supply_chain/`.
- Upgrade Hetzner app virtualenv `pip` to `26.2`.
- Install `requirements-pinned.txt` into `/srv/cryptkeep/app/.venv`.
- Run the repo-local supply-chain check without `--audit`.
- Leave services running; do not restart collectors, campaigns, dashboard,
  timers, or systemd units.

Not allowed by this runbook:

- Service restart, stop, start, or daemon reload.
- Git checkout changes.
- Config changes.
- Host vulnerability audit with `--audit`, unless separately approved because
  it may disclose package inventory to an external vulnerability service.
- SBOM/hash-locked release-policy changes.

## Command Sequence

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 '
  set -euo pipefail
  cd /srv/cryptkeep/app
  mkdir -p /tmp/cryptkeep_supply_chain
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  before=/tmp/cryptkeep_supply_chain/pip-freeze-before-${stamp}.txt
  after=/tmp/cryptkeep_supply_chain/supply-chain-after-${stamp}.json
  ./.venv/bin/python -m pip freeze > "$before"
  ./.venv/bin/python -m pip install --upgrade pip==26.2
  ./.venv/bin/python -m pip install -r requirements-pinned.txt
  ./.venv/bin/python scripts/check_supply_chain.py --json > "$after"
  echo "before_freeze=$before"
  echo "after_report=$after"
  cat "$after"
'
```

## Verification Criteria

The host alignment is acceptable only if the final JSON reports:

- `pin_integrity.ok=true`
- `environment.ok=true`
- `environment.mismatches=[]`
- `environment.not_installed=[]`
- `vulnerability_audit.ran=false` unless a separate audit approval is given

After alignment, run read-only status checks:

```bash
HETZNER_STATUS_TRANSPORT=ssh HETZNER_SSH_TARGET=cryptkeep@100.86.128.9 \
  make status-hetzner-edge-runtime

HETZNER_STATUS_TRANSPORT=ssh HETZNER_SSH_TARGET=cryptkeep@100.86.128.9 \
  make status-paper-hetzner
```

Expected result:

- Hetzner crypto-edge runtime remains ready.
- Hetzner paper campaign remains running or idle without service restart.

## Recovery

The pre-change freeze file is the rollback source. If the post-change check
fails or a service later shows dependency-related errors, restore the previous
environment with:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 '
  set -euo pipefail
  cd /srv/cryptkeep/app
  ./.venv/bin/python -m pip install -r /tmp/cryptkeep_supply_chain/<pip-freeze-before-file>.txt
  ./.venv/bin/python scripts/check_supply_chain.py --json
'
```

The concrete `<pip-freeze-before-file>` is printed by the alignment command.

## Required Approval Text

Use this exact approval when ready:

```text
I approve aligning Hetzner /srv/cryptkeep/app/.venv to requirements-pinned.txt and upgrading host pip to 26.2 with no service restart, using docs/checkpoints/hetzner_dependency_alignment_runbook_2026_08_24.md.
```

## Remaining After Alignment

- Host vulnerability audit still requires explicit approval or waiver.
- SBOM/hash-locked install policy remains a release-policy decision.

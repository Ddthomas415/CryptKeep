# Hetzner Dependency Alignment Proof - 2026-08-28

## Scope

This checkpoint records the operator-approved no-restart alignment of the
Hetzner app virtualenv to `requirements-pinned.txt`.

Approved operator text:

```text
I approve aligning Hetzner /srv/cryptkeep/app/.venv to requirements-pinned.txt and upgrading host pip to 26.2 with no service restart, using docs/checkpoints/hetzner_dependency_alignment_runbook_2026_08_24.md.
```

## Command

Executed from the local repo against Hetzner:

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

## Result

SHOWN:

- Host `pip` upgraded from `26.1.2` to `26.2`.
- The host virtualenv installed the previously mismatched pinned packages:
  `aiohttp==3.14.3`, `click==8.3.3`, `cryptography==50.0.0`,
  `GitPython==3.1.58`, `idna==3.15`, `pillow==12.3.0`,
  `setuptools==83.0.0`, `starlette==1.3.1`, `tornado==6.5.7`, and
  `urllib3==2.7.0`.
- Pre-change rollback artifact:
  `/tmp/cryptkeep_supply_chain/pip-freeze-before-20260828T230654Z.txt`.
- Post-change evidence artifact:
  `/tmp/cryptkeep_supply_chain/supply-chain-after-20260828T230654Z.json`.
- Post-change `scripts/check_supply_chain.py --json` reported:
  - `git_sha=6c0903d318756d27eb6414a01abbfc8c8e879ae5`
  - `git_dirty=false`
  - `pin_integrity.ok=true`
  - `pin_integrity.pin_count=83`
  - `environment.ok=true`
  - `environment.mismatches=[]`
  - `environment.not_installed=[]`
  - `vulnerability_audit.ran=false`

## Post-Change Read-Only Checks

`make status-hetzner-dependency-alignment-json`:

- SHOWN: `environment_alignment.status=aligned`.
- SHOWN: `pip_dry_run.status=no_changes`.
- SHOWN: `mismatches=[]`.
- SHOWN: `not_installed=[]`.
- SHOWN: no deploy, pip install, or service restart was invoked by the
  read-only status command.
- SHOWN: the overall status still returned blocked only because
  `remote_checkout_commit` was behind current local `origin/master`.

`make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=30`:

- SHOWN: `status=hetzner_crypto_edge_runtime_ready`.
- SHOWN: `ok=True`.
- SHOWN: `blocking_checks=0`.

`make status-paper-hetzner HETZNER_STATUS_TIMEOUT_SEC=30`:

- SHOWN: `Campaigns: 1/1 running`.
- SHOWN: `ema_cross_default` remained idle with reason
  `waiting_for_next_day` after recording 2026-08-28 session evidence.

## Remaining

SHOWN:

- Hetzner checkout remains at `6c0903d318756d27eb6414a01abbfc8c8e879ae5`.
- Current local `origin/master` after PR #554 is
  `6f041b53972105663168bcf6c1d75b13f3f360ea`.

UNVERIFIED:

- Host checkout sync to `6f041b53972105663168bcf6c1d75b13f3f360ea` or later.
- Host vulnerability audit, because it may disclose host package inventory and
  still requires separate approval or waiver.
- SBOM/hash-locked release-policy decision.

Acceptance state: `INCOMPLETE`.

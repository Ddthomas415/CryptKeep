# Hetzner Checkout Sync - 2026-08-29

## Scope

This checkpoint records a no-restart fast-forward of `/srv/cryptkeep/app` on
Hetzner to current `origin/master`.

No service restart, package install, config edit, campaign start/stop, gate
change, strategy promotion, order routing, execution, or live-money behavior was
performed.

## Commands

No-restart checkout sync:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 '
  set -euo pipefail
  cd /srv/cryptkeep/app
  before=$(git rev-parse HEAD)
  git fetch origin master
  git merge --ff-only origin/master
  after=$(git rev-parse HEAD)
  status=$(git status --short --branch)
  echo "before=$before"
  echo "after=$after"
  echo "status=$status"
'
```

Post-sync verification:

```bash
make status-hetzner-dependency-alignment-json
make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=30
make status-paper-hetzner HETZNER_STATUS_TIMEOUT_SEC=30
make check-hetzner-paper-host-health HETZNER_STATUS_TIMEOUT_SEC=30
```

## Result

Checkout sync:

- SHOWN: `git fetch origin master` exited `0`.
- SHOWN: `git merge --ff-only origin/master` exited `0`.
- SHOWN: Hetzner `/srv/cryptkeep/app` fast-forwarded from
  `6c0903d318756d27eb6414a01abbfc8c8e879ae5` to
  `0018c1213214f74033a70c59949e9ed86e3cfbad`.
- SHOWN: post-sync git status was `## master...origin/master`.

Dependency alignment:

- SHOWN: `status=hetzner_dependency_alignment_ready`.
- SHOWN: `ok=true`.
- SHOWN: `remote_checkout_commit.status=matches`.
- SHOWN: `environment_alignment.status=aligned`.
- SHOWN: `pip_dry_run.status=no_changes`.
- SHOWN: `mismatches=[]`.
- SHOWN: `not_installed=[]`.
- SHOWN: read-only status command did not invoke deploy, pip install, or
  service restart.

Crypto-edge runtime:

- SHOWN: `status=hetzner_crypto_edge_runtime_ready`.
- SHOWN: `ok=True`.
- SHOWN: `remote_head=0018c1213214f74033a70c59949e9ed86e3cfbad`.
- SHOWN: `blocking_checks=0`.

Paper campaign:

- SHOWN: `Campaigns: 1/1 running`.
- SHOWN: `ema_cross_default` was idle with reason `waiting_for_next_day`.
- SHOWN: `fills=16`.
- SHOWN: `closed=8`.
- SHOWN: `pnl=-2.3183`.
- SHOWN: latest fill was `2026-08-29T00:02:44.159494+00:00`.
- SHOWN: session evidence was already recorded for `2026-08-29`.

Host health:

- SHOWN: `status=hetzner_paper_host_healthy`.
- SHOWN: `ok=True`.
- SHOWN: `artifact_path=/srv/cryptkeep/app/.cbp_state/runtime/snapshots/hetzner_paper_host_health.latest.json`.

## Remaining

UNVERIFIED:

- Host vulnerability audit, because it may disclose host package inventory and
  still requires separate approval or waiver.
- SBOM/hash-locked release-policy decision.
- Any future launch packet should refresh this proof close to the actual launch
  decision.

Acceptance state: `INCOMPLETE`.

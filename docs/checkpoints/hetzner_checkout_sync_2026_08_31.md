# Hetzner Checkout Sync - 2026-08-31

This checkpoint records a no-restart fast-forward of `/srv/cryptkeep/app` on
Hetzner to current `origin/master`.

No package install, service restart, config edit, campaign start/stop, gate
change, live routing, or execution behavior change was performed.

## Pre-Sync Finding

Read-only dependency alignment initially showed a checkout mismatch:

- expected local `origin/master`: `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`
- remote Hetzner checkout: `d3b46e3c2f0541c20897f78739ce071c637d9647`
- remote branch: `master`
- remote git state: clean
- pin integrity: OK
- installed environment: OK
- pip dry-run: no changes
- vulnerability audit: not requested

The mismatch was checkout drift only.

## Sync Command

```bash
tailscale ssh cryptkeep@100.86.128.9 git -C /srv/cryptkeep/app fetch origin master
tailscale ssh cryptkeep@100.86.128.9 git -C /srv/cryptkeep/app merge --ff-only origin/master
```

SHOWN:

- fetch reported `d3b46e3c..c7bd3052 master -> origin/master`;
- merge fast-forwarded from `d3b46e3c` to `c7bd3052`;
- changed files were documentation/checkpoints only.

## Post-Sync Verification

```bash
tailscale ssh cryptkeep@100.86.128.9 git -C /srv/cryptkeep/app rev-parse HEAD
tailscale ssh cryptkeep@100.86.128.9 git -C /srv/cryptkeep/app status --short --branch
./.venv/bin/python scripts/report_hetzner_dependency_alignment_status.py --json --strict --ssh-target cryptkeep@100.86.128.9 --transport tailscale-ssh --app-dir /srv/cryptkeep/app --expected-branch master --expected-commit c7bd305287792993d0a63e01e9bdc5ad3cfacf6e --timeout-sec 15
make status-hetzner-edge-runtime
make check-hetzner-paper-host-health
make status-paper-hetzner
```

SHOWN:

- remote HEAD:
  `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`;
- remote status: `## master...origin/master`;
- dependency alignment status: `hetzner_dependency_alignment_ready`;
- dependency blockers: `[]`;
- pin integrity: OK;
- installed environment alignment: OK;
- pip dry-run: no changes;
- crypto-edge runtime status: `hetzner_crypto_edge_runtime_ready`;
- paper host health: `hetzner_paper_host_healthy`;
- Hetzner paper campaign: `ema_cross_default` `1/1` running, idle
  `waiting_for_next_day`, latest fill `2026-08-29T00:02:44.159494+00:00`.

## Remaining Work

This closes the observed checkout drift to current master for this checkpoint.
It does not close:

- host vulnerability audit or accepted waiver;
- SBOM release-policy decision;
- hash-locked install release-policy decision;
- broader capped-live launch packet.

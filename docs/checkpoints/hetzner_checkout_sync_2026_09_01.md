# Hetzner Checkout Sync - 2026-09-01

Status: Hetzner `/srv/cryptkeep/app` is synced to local/origin master
`f5837f03af3f9292b62f083d50c961847b442728` with no service restart.

## Scope

- SHOWN: the host checkout was clean before sync.
- SHOWN: the host checkout was fast-forwarded only.
- SHOWN: no service restart, package install, dependency install, config edit,
  campaign start/stop, gate change, live routing, or execution action was run.
- SHOWN: all post-sync checks below were read-only.

## Pre-Sync State

Local:

- SHOWN: local `HEAD` and `origin/master` were both
  `f5837f03af3f9292b62f083d50c961847b442728`.
- SHOWN: local checkout was clean on `master`.

Hetzner:

- SHOWN: `/srv/cryptkeep/app` was clean on `master`.
- SHOWN: pre-sync host HEAD was
  `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`.

## Sync Command

```bash
ssh -o BatchMode=yes -o ConnectTimeout=15 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && git fetch origin master && git merge --ff-only origin/master && git rev-parse HEAD && git status --short --branch'
```

Result:

- SHOWN: `git fetch origin master` advanced `origin/master` from
  `c7bd3052` to `f5837f03`.
- SHOWN: `git merge --ff-only origin/master` completed as a fast-forward.
- SHOWN: post-sync host HEAD was
  `f5837f03af3f9292b62f083d50c961847b442728`.
- SHOWN: post-sync host checkout remained clean on `master`.

## Post-Sync Checks

Paper campaign:

- Command:
  `make status-paper-hetzner HETZNER_STATUS_TRANSPORT=ssh`
- SHOWN: `Campaigns: 1/1 running`.
- SHOWN: `ema_cross_default` was idle with reason `waiting_for_next_day`.
- SHOWN: totals were `fills=16`, `closed=8`, `pnl=-2.3183`.
- SHOWN: latest fill was `2026-08-29T00:02:44.159494+00:00`.

Crypto-edge runtime:

- Command:
  `make status-hetzner-edge-runtime HETZNER_STATUS_TRANSPORT=ssh`
- SHOWN: `status=hetzner_crypto_edge_runtime_ready`.
- SHOWN: `ok=True`, `blocking_checks=0`.
- SHOWN: remote branch `master`, remote head
  `f5837f03af3f9292b62f083d50c961847b442728`.

Dependency alignment:

- Command:
  `make status-hetzner-dependency-alignment HETZNER_STATUS_TRANSPORT=ssh`
- SHOWN: `status=hetzner_dependency_alignment_ready`.
- SHOWN: `remote_checkout_branch`, `remote_checkout_commit`,
  `remote_git_clean`, `pin_integrity`, `environment_alignment`, and
  `pip_dry_run` checks were all `ok`.
- SHOWN: `pip_dry_run: no_changes`.
- SHOWN: vulnerability audit was not run in this wrapper invocation:
  `vulnerability_audit_not_run: not_requested`.

Edge cadence:

- Command:
  `CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json`
  on the host.
- SHOWN: `ok=true`, `missing=[]`, `stale=[]`.
- SHOWN: funding, open-interest, and basis snapshots were fresh with capture
  timestamp `2026-09-01T23:44:35+00:00`.

Supply-chain status:

- Command:
  `./.venv/bin/python scripts/check_supply_chain.py --json` on the host.
- SHOWN: `git_sha=f5837f03af3f9292b62f083d50c961847b442728`.
- SHOWN: `git_dirty=false`.
- SHOWN: `pin_integrity.ok=true`, `pin_count=83`.
- SHOWN: `environment.ok=true`, `checked=83`, `mismatches=[]`,
  `not_installed=[]`.
- SHOWN: vulnerability audit was not requested:
  `vulnerability_audit.ran=false`, `reason=not_requested`.

## Remaining Risk

- MEDIUM: records a host checkout sync, but the delivered change is
  documentation only.
- Host vulnerability audit remains open until `pip-audit` is installed/enabled
  on the host or the audit requirement is explicitly waived.
- No restart was performed, so currently running services continue under their
  existing process state until their next restart/reload boundary.
- Acceptance state: `ACCEPTED`.

# Hetzner Checkout Sync - 2026-09-02

Status: Hetzner `/srv/cryptkeep/app` is synced to local/origin master
`bbe2f4b5f64a4b49f36467aebea5d7c57acd3f03` with no service restart.

## Scope

- SHOWN: local `HEAD` and `origin/master` were both
  `bbe2f4b5f64a4b49f36467aebea5d7c57acd3f03`.
- SHOWN: the host checkout was clean before sync.
- SHOWN: the host checkout was fast-forwarded only.
- SHOWN: no service restart, package install, dependency install, config edit,
  campaign start/stop, gate change, live routing, or execution action was run.
- SHOWN: all post-sync checks below were read-only.

## Pre-Sync State

Local:

- SHOWN: local checkout was clean on `master`.
- SHOWN: local `HEAD` and `origin/master` were both
  `bbe2f4b5f64a4b49f36467aebea5d7c57acd3f03`.

Hetzner:

- SHOWN: `/srv/cryptkeep/app` was clean on `master`.
- SHOWN: pre-sync host HEAD was
  `f5837f03af3f9292b62f083d50c961847b442728`.

## Sync Command

```bash
ssh -o BatchMode=yes -o ConnectTimeout=15 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && git status --short --branch && git rev-parse HEAD && git fetch origin master && git merge --ff-only origin/master && git rev-parse HEAD && git status --short --branch'
```

Result:

- SHOWN: `git fetch origin master` advanced remote `origin/master` from
  `f5837f03` to `bbe2f4b5`.
- SHOWN: `git merge --ff-only origin/master` completed as a fast-forward.
- SHOWN: post-sync host HEAD was
  `bbe2f4b5f64a4b49f36467aebea5d7c57acd3f03`.
- SHOWN: post-sync host checkout remained clean on `master`.

## Post-Sync Checks

Paper campaign:

- Command: `make status-paper-hetzner`
- SHOWN: `Campaigns: 1/1 running`.
- SHOWN: `ema_cross_default` was idle with reason `waiting_for_next_day`.
- SHOWN: totals were `fills=16`, `closed=8`, `pnl=-2.3183`.
- SHOWN: latest fill was `2026-08-29T00:02:44.159494+00:00`.
- SHOWN: the wrapper used the accepted default direct SSH transport.

Crypto-edge runtime:

- Command: `make status-hetzner-edge-runtime`
- SHOWN: `status=hetzner_crypto_edge_runtime_ready`.
- SHOWN: `ok=True`, `blocking_checks=0`.
- SHOWN: remote branch `master`, remote head
  `bbe2f4b5f64a4b49f36467aebea5d7c57acd3f03`.

Dependency alignment:

- Command: `make status-hetzner-dependency-alignment`
- SHOWN: `status=hetzner_dependency_alignment_ready`.
- SHOWN: `transport=ssh`.
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
  timestamp `2026-09-02T04:05:39+00:00`.

Supply-chain status:

- Command:
  `./.venv/bin/python scripts/check_supply_chain.py --json` on the host.
- SHOWN: `git_sha=bbe2f4b5f64a4b49f36467aebea5d7c57acd3f03`.
- SHOWN: `git_dirty=false`.
- SHOWN: `pin_integrity.ok=true`, `pin_count=83`.
- SHOWN: `environment.ok=true`, `checked=83`, `mismatches=[]`,
  `not_installed=[]`.
- SHOWN: vulnerability audit was not requested:
  `vulnerability_audit.ran=false`, `reason=not_requested`.

## Remaining Risk

- LOW: records a host checkout sync, but the delivered repo change is
  documentation only.
- Host vulnerability audit remains open until `pip-audit` is installed/enabled
  on the host or the audit requirement is explicitly waived.
- SBOM/hash-lock release-policy requirements remain a separate decision.
- No restart was performed, so currently running services continue under their
  existing process state until their next restart/reload boundary.
- Acceptance state: `ACCEPTED`.

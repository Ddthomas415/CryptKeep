# Hetzner Checkout Sync After PR 569 - 2026-09-02

Status: Hetzner `/srv/cryptkeep/app` is synced to local/origin master
`df06a8b06aadaede0fe3265307aace2512932cca` with no service restart.

## Scope

- SHOWN: PR #569 merged to `master` at
  `df06a8b06aadaede0fe3265307aace2512932cca`.
- SHOWN: local `master` was fast-forwarded to the same SHA.
- SHOWN: Hetzner `/srv/cryptkeep/app` was clean before sync at
  `bbe2f4b5f64a4b49f36467aebea5d7c57acd3f03`.
- SHOWN: Hetzner sync was `git fetch origin master` plus
  `git merge --ff-only origin/master`.
- SHOWN: no service restart, dependency install, config edit, campaign
  start/stop, gate change, live routing, or execution action was run.

## Sync Result

Command shape:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=15 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && git status --short --branch && git rev-parse HEAD && git fetch origin master && git merge --ff-only origin/master && git rev-parse HEAD && git status --short --branch'
```

Result:

- SHOWN: host checkout fast-forwarded from
  `bbe2f4b5f64a4b49f36467aebea5d7c57acd3f03` to
  `df06a8b06aadaede0fe3265307aace2512932cca`.
- SHOWN: post-sync host checkout remained clean on `master`.

## Post-Sync Checks

Hetzner paper campaign:

- Command: `make status-paper-hetzner`
- SHOWN: `Campaigns: 1/1 running`.
- SHOWN: `ema_cross_default` was idle with reason `waiting_for_next_day`.
- SHOWN: latest fill was `2026-08-29T00:02:44.159494+00:00`.
- SHOWN: recommendation was `continue_paper_observation`.

Hetzner crypto-edge runtime:

- Command: `make status-hetzner-edge-runtime`
- SHOWN: `status=hetzner_crypto_edge_runtime_ready`.
- SHOWN: `ok=True`, `blocking_checks=0`.
- SHOWN: remote branch `master`, remote head
  `df06a8b06aadaede0fe3265307aace2512932cca`.

Hetzner dependency alignment:

- Command: `make status-hetzner-dependency-alignment-json`
- SHOWN: `status=hetzner_dependency_alignment_ready`.
- SHOWN: remote checkout branch/commit/git-clean checks all passed.
- SHOWN: pin integrity and environment alignment passed for `83` checked
  packages with `mismatches=[]` and `not_installed=[]`.
- SHOWN: `pip_dry_run.status=no_changes`, `install_candidates=[]`.
- SHOWN: vulnerability audit was not requested:
  `vulnerability_audit.ran=false`, `reason=not_requested`.

Local paper gate:

- Command: `make status-paper-gate-velocity-json`
- SHOWN: policy `slow_daily_single_symbol_v1` remains valid.
- SHOWN: qualified bars complete: `72/60`.
- SHOWN: qualified round trips remain `3/5`, with `2` remaining.
- SHOWN: projected completion is
  `2026-09-23T06:31:42.518899+00:00` if observed cadence holds.

Local research pipelines:

- Command: `make research-pipeline-status-json`
- SHOWN: both wired pipelines are latest-ok:
  `price_action` and `funding_threshold`.

## Remaining Risk

- LOW: docs checkpoint only.
- Host vulnerability audit remains separate because it may disclose host
  package inventory and was not requested.
- SBOM/hash-lock release-policy decisions remain separate.
- Arm-to-halt, enable/resume, and critical audit-write fail-closed host proofs
  remain separate capped-live work.
- Acceptance state: `ACCEPTED`.

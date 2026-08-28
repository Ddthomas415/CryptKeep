# Host Read-Only Proof Blocked - 2026-08-28

## Scope

This checkpoint records an attempted read-only Hetzner proof after PR #552
merged. It does not close any host-side proof and does not mutate host or local
runtime state beyond normal command output.

## Commands

```bash
make status-hetzner-dependency-alignment-json
make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=30
```

## Result

SHOWN:

- Both commands remained read-only.
- Neither command deployed code.
- Neither command installed packages.
- Neither command restarted services.
- Neither command changed campaigns, gates, configs, strategy promotion,
  execution, or routing.

`make status-hetzner-dependency-alignment-json` returned:

```text
ok=false
reason=ssh_operation_not_permitted
transport_fallback.from=tailscale-ssh
transport_fallback.reason=tailscale_cli_preferences_unavailable
stderr_preview=ssh: connect to host 100.86.128.9 port 22: Operation not permitted
deploy_invoked=false
pip_install_invoked=false
pip_dry_run_invoked=false
service_restart_invoked=false
```

`make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=30` returned:

```text
status=hetzner_crypto_edge_runtime_blocked
ok=false
reason=ssh_operation_not_permitted
blocking_checks=1
recommendation=investigate_remote_status_failure
```

## Interpretation

SHOWN:

- The proof is blocked by local transport/permission behavior before the remote
  proof can run.
- The result is not evidence that Hetzner dependency alignment or edge runtime
  is unhealthy.
- The result is not evidence that the host proof is complete.

UNVERIFIED:

- Current Hetzner checkout SHA.
- Current Hetzner dependency alignment against `requirements-pinned.txt`.
- Current Hetzner crypto-edge runtime readiness.
- Host-side backup/restore drill after PR #550.

## Next Action

Use a working Tailscale SSH path or direct SSH path from an environment where
the operator has authorized host access, then rerun:

```bash
make status-hetzner-dependency-alignment-json
make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=30
```

Do not treat this checkpoint as a launch proof.

Acceptance state: `INCOMPLETE`.

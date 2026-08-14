# Host Systemd Dry-Run Checkpoint - 2026-08-14

## Scope

Read-only Hetzner deployment-unit dry run. This checkpoint verifies that the
current host checkout can render and statically verify the packaged systemd
units. It does not install units, reload systemd, restart services, enable
services, or arm live trading.

## Command

```bash
tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/install_systemd_units.py --repo-dir /srv/cryptkeep/app'
```

## Result

```text
static verify ok: cbp-collector.service, cbp-crypto-edge-collector.service, cbp-intent-consumer.service, cbp-reconciler.service, cbp-dashboard.service, cbp-dead-man.service, cbp-edge-cadence.service, cbp-dead-man.timer, cbp-edge-cadence.timer
dry run: would copy rendered units to /etc/systemd/system; rerun with --apply
repo-dir: /srv/cryptkeep/app
NOTE: installing units never arms live trading; arming flows only through the ceremony.
```

## Interpretation

The host checkout can render and verify the packaged unit set in dry-run mode.
The broader deployment installation evidence remains open until an explicit
operator-approved `--apply` run and post-install inventory/status proof are
recorded.

## Boundaries

- No unit install.
- No `systemctl daemon-reload`.
- No service restart.
- No service enablement.
- No campaign change.
- No live/shadow authorization.

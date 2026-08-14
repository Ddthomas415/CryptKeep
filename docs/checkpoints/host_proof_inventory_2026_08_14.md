# Host Proof Inventory - 2026-08-14

## Scope

Read-only host inventory for open deployment, schema, and backup/restore proof
rows. This checkpoint records what is present on the Hetzner host and what is
still absent. It does not install units, initialize schemas, run restore, restart
services, or close capped-live proof.

## Host

- Tailscale target: `cryptkeep@100.86.128.9`
- App directory: `/srv/cryptkeep/app`
- Host checkout: `5eb36cbb5`

## Systemd Unit Inventory

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 'systemctl list-units --type=service --type=timer --all --no-pager --plain "cbp-*"'
```

Observed loaded units:

- `cbp-crypto-edge-collector.service`: `loaded active running`
- `cbp-edge-cadence.service`: `loaded inactive dead`
- `cbp-edge-cadence.timer`: `loaded active waiting`

Expected core deployment units not observed as loaded/running in this inventory:

- `cbp-collector.service`
- `cbp-dashboard.service`
- `cbp-dead-man.service`
- `cbp-dead-man.timer`
- `cbp-intent-consumer.service`
- `cbp-reconciler.service`

Direct status probe also reported:

- `cbp-paper-ema-cross.service`: unit not found
- `cbp-paper-breakout.service`: unit not found

Interpretation: the accepted crypto-edge host runtime is installed and active;
the broader production systemd deployment proof remains open.

## Live Intent History Schema

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_live_intent_history_schema.py --json'
```

Result:

- `ok=false`
- `status=schema_uninitialized`
- `reason=live_intent_queue_db_missing`
- `db_path=/var/lib/cbp/data/live_intent_queue.sqlite`
- `event_history_declared=true`
- `event_history_table_exists=false`

Interpretation: this host has no live intent queue database yet. That is
consistent with paper-only operation, but it does not close the live-intent
history host proof. Schema initialization remains a deliberate host operation
before any live/capped-live use.

## Backup Tooling Availability

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/backup_state.py --help'
```

Result:

- `scripts/backup_state.py` is present and exposes `backup`, `verify`, and
  `restore` subcommands.

Interpretation: backup/restore tooling is available on the host checkout. This
does not execute or close the required backup/restore drill.

## Boundaries

- No service restart.
- No unit install.
- No schema initialization.
- No backup creation.
- No restore.
- No campaign change.
- No live/shadow authorization.

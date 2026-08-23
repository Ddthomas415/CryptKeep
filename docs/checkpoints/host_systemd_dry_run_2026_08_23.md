# Host Systemd Dry-Run Checkpoint - 2026-08-23

## Scope

Read-only Hetzner deployment-unit follow-up. This checkpoint verifies the
current host checkout can render and statically verify the packaged systemd
units, and records the installed `cbp-*` unit inventory observed at the same
time.

No unit was installed, enabled, restarted, reloaded, or modified by this
checkpoint.

## Host Checkout

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && git rev-parse --short HEAD && ./.venv/bin/python scripts/install_systemd_units.py --repo-dir /srv/cryptkeep/app'
```

Result:

```text
a10aca01
static verify ok: cbp-collector.service, cbp-crypto-edge-collector.service, cbp-intent-consumer.service, cbp-reconciler.service, cbp-dashboard.service, cbp-dead-man.service, cbp-edge-cadence.service, cbp-dead-man.timer, cbp-edge-cadence.timer
dry run: would copy rendered units to /etc/systemd/system; rerun with --apply
repo-dir: /srv/cryptkeep/app
NOTE: installing units never arms live trading; arming flows only through the ceremony.
```

## Installed Unit Inventory

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'systemctl list-units --type=service --type=timer --all --no-pager --plain "cbp-*"'
```

Result:

```text
UNIT                              LOAD   ACTIVE   SUB     DESCRIPTION
cbp-crypto-edge-collector.service loaded active   running CryptKeep read-only crypto-edge collector
cbp-edge-cadence.service          loaded inactive dead    CryptKeep crypto-edge collector cadence check
cbp-edge-cadence.timer            loaded active   waiting CryptKeep crypto-edge collector cadence timer

3 loaded units listed.
```

## Interpretation

- The host checkout at `a10aca01` can render and statically verify the full
  packaged systemd unit set in dry-run mode.
- The host's currently loaded `cbp-*` unit inventory remains limited to the
  crypto-edge collector and edge-cadence units.
- The broader core units (`cbp-collector`, `cbp-dashboard`, `cbp-dead-man`,
  `cbp-intent-consumer`, and `cbp-reconciler`) were not observed as loaded in
  this read-only inventory.

## Remaining Risk

- This is not an installation proof.
- This is not a `systemctl daemon-reload` proof.
- This is not a service enablement or restart proof.
- This does not close the deployment installation/post-install item; it only
  refreshes the dry-run and inventory evidence for the current host checkout.

## Dead-Man Tooling Presence

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && ls scripts/check_dead_man.py services/process/heartbeat.py packaging/systemd/cbp-dead-man.timer packaging/systemd/cbp-dead-man.service 2>&1'
```

Result:

```text
packaging/systemd/cbp-dead-man.service
packaging/systemd/cbp-dead-man.timer
scripts/check_dead_man.py
services/process/heartbeat.py
```

## Dead-Man Heartbeat Status

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_dead_man.py --json'
```

Result:

```json
{
  "ok": false,
  "overall": "missing",
  "max_age_s": 180.0,
  "names": {
    "intent_consumer": {
      "status": "missing",
      "age_s": null,
      "path": "/var/lib/cbp/runtime/heartbeats/intent_consumer.json"
    },
    "live_reconciler": {
      "status": "missing",
      "age_s": null,
      "path": "/var/lib/cbp/runtime/heartbeats/live_reconciler.json"
    }
  }
}
```

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_dead_man.py --json --names crypto_edge_collector,edge_cadence'
```

Result:

```json
{
  "ok": false,
  "overall": "missing",
  "max_age_s": 180.0,
  "names": {
    "crypto_edge_collector": {
      "status": "missing",
      "age_s": null,
      "path": "/var/lib/cbp/runtime/heartbeats/crypto_edge_collector.json"
    },
    "edge_cadence": {
      "status": "missing",
      "age_s": null,
      "path": "/var/lib/cbp/runtime/heartbeats/edge_cadence.json"
    }
  }
}
```

Interpretation:

- The dead-man checker is present on the host and fails closed when configured
  heartbeat files are absent.
- The packaged default `cbp-dead-man.service` checks `intent_consumer` and
  `live_reconciler`, but that service/timer is not currently loaded on the host.
- No heartbeat files were observed for the explicit crypto-edge names checked
  under `/var/lib/cbp`.
- This is status evidence only; it does not install the dead-man timer or start
  any heartbeat-producing loop.

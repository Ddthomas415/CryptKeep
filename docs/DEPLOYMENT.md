# Deployment (systemd)

This resolves the "ship deployment units or retire the stale deployment
story" substrate item: CryptKeep's long-running processes are supervised by
systemd with journald logging, restart-with-backoff, and moderate sandbox
hardening. Units live in `packaging/systemd/` and are verified/installed by
`scripts/install_systemd_units.py`.

## Authority boundary (read first)

Installing or enabling these units NEVER arms live trading. The units and
the operator env file deliberately carry no `CBP_EXECUTION_ARMED` or
live-enable state; live authority flows only through the one-time-token
live-enable ceremony and system state, exactly as before. Process
supervision and trading authority are separate planes; the install helper
and the unit tests both fail if an arming token appears in a unit or the
env template.

## Processes

| Unit | Entry point | Run policy |
| --- | --- | --- |
| `cbp-collector.service` | `scripts/collect_market_data_multi.py` (loop mode) | enable on data hosts |
| `cbp-reconciler.service` | `scripts/run_live_reconciler_safe.py` | safe to enable always; recovery must run even when trading is halted |
| `cbp-intent-consumer.service` | `scripts/run_intent_consumer_safe.py` | enable only on the trading host; it still submits nothing unless armed via the ceremony |
| `cbp-dashboard.service` | `scripts/run_dashboard.py` | operator visibility; bind per host policy |

## Host prerequisites (operator review required)

The units ship with placeholder host assumptions — review every one:

1. System user/group `cbp` (no shell, no sudo): `useradd --system --home /var/lib/cbp cbp`
2. Repo checkout at `/opt/crypto-bot-pro` with a venv at `.venv/` owned by `cbp`
3. State directory `/var/lib/cbp/state` owned `cbp:cbp` (matches
   `CBP_STATE_DIR` and the units' `ReadWritePaths=/var/lib/cbp`; systemd does
   not expand env vars in `ReadWritePaths`, so if you relocate state, edit
   both places)
4. Env file: `install -o root -g cbp -m 640 packaging/systemd/cbp.env.example /etc/cbp/cbp.env`, then review every value

## Install

```
python scripts/install_systemd_units.py            # static + systemd-analyze verify, dry run
sudo python scripts/install_systemd_units.py --apply
sudo systemctl daemon-reload
sudo systemctl enable --now cbp-collector cbp-reconciler cbp-dashboard
# cbp-intent-consumer: enable deliberately, per the run policy above
```

## Operations

- Logs: `journalctl -u cbp-reconciler -f` (stdout is unbuffered via
  `PYTHONUNBUFFERED=1`).
- Restart policy: `Restart=on-failure`, `RestartSec=5`, capped at 10 starts
  per 300s (`StartLimit*`); a crash-looping unit lands in `failed` state
  rather than hammering the venue, and the crash-consistency proofs cover
  the restart path.
- Hardening: `NoNewPrivileges`, `ProtectSystem=strict` (writes only under
  `/var/lib/cbp`), `ProtectHome`, `PrivateTmp`. If a process needs another
  writable path, extend `ReadWritePaths` explicitly rather than loosening
  `ProtectSystem`.
- Stop order for maintenance: consumer first, reconciler last.

## Known boundaries

- No watchdog/dead-man integration yet — that is the separate
  "trading-loop heartbeat metrics and dead-man alerting" substrate item;
  these units restart crashes but do not detect silent hangs.
- The dashboard unit does not manage TLS/reverse proxy; front it per host
  policy.

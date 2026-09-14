# Hetzner Deadline Rehearsal

Active role: AUDITOR. VERIFIED_ENV: ubuntu-4gb-nbg1-3, uid 1000, systemd
255.4-1ubuntu8.17. Checkout remains e38c342d at preflight; no sync/deploy run.
User completed Tailscale SSH approval. Temporary package/scripts placed in
/tmp/cryptkeep-es-rehearsal.SecSsm; no production unit files installed.

## SHOWN

- systemd-analyze --user verify on rendered service/timer/stop units: rc=0,
  empty stderr. This checks syntax/dependencies, not actual collector startup.
- Expired deadline guard executed on host: rc=1.
- Unique transient dummy service plus persistent absolute-calendar timer tested
  the stop mechanism. Parent spawned a new-session child deliberately ignoring
  SIGTERM. KillMode=control-group, TimeoutStopSec=2, RuntimeMaxSec=30.
- Timer was active with deadline 2026-09-09 20:00:02 UTC. Before stop cgroup
  contained PIDs 1523215/1523219; after shutdown it was empty, MainPID=0.
- Unit cryptkeep-es-dummy-1788983995972263398.service ended failed/timeout,
  expected for forced cleanup of the resistant child. Test units were stopped
  and failed state reset in finally. Temporary artifacts remain for audit.

First rehearsal assertion incorrectly required inactive; it had already proved
empty cgroup and MainPID=0 but failed on timeout status. Corrected assertion
accepts failed/timeout only alongside empty group and zero main PID. Second run
completed successfully. No real campaign service was targeted.

## Limits

Actual rendered campaign was not started. Expired-start CLI was tested, not an
actual expired collector unit start. The dummy uses a six-second timer and
two-second shutdown grace; it does not prove 30 days of operation, real collector
flush behavior, host-reboot recovery or child effective configuration. Those
claims remain UNVERIFIED. This proof supports only the bounded dummy stop lane.

Local artifact/script: .cbp_state/data/research/es_host_rehearsal/20260909/.
Local package/manifest/recovery tests also passed: 32 in 0.30s.
No app venv, canonical state, gate, campaign, credentials or deployed code changed.
Acceptance state: ACCEPTED for bounded host rehearsal; launch readiness INCOMPLETE.

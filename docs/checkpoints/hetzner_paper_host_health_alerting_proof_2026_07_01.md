# Hetzner Paper Host Health Alerting Proof - 2026-07-01

## Scope

Active role: ENGINEER

Objective:
- Add a read-only, scheduled-safe host-health wrapper for the Hetzner paper
  host.
- Reuse the accepted Hetzner host preflight as the source of truth.
- Write an operator-visible latest artifact and local critical-alert fallback
  when the preflight fails.
- Do not SSH to Hetzner, stop collectors, start collectors, restore campaigns,
  copy state, or migrate canonical `.cbp_state`.

## Reason

Priority 16 requires disk/health alerting before canonical migration. The
accepted storage preflight proves one-shot host readiness, but one-shot
preflight output is not persistent alerting. The repo needed a repeatable
command that can be scheduled by the host and leaves a durable latest artifact.

SHOWN:
- `scripts/hetzner_paper_host_preflight.py` already reports repo, venv, Git,
  NTP, Tailscale, campaign config, backup directory, free-space, and free-inode
  checks.
- `services/alerts/alert_dispatcher.py` already writes a local critical-alert
  JSONL fallback for error-level alerts, even when external alert channels are
  disabled.
- Backup restore rehearsal remains a separate blocker.

## Code Change

Changed:
- `scripts/check_hetzner_paper_host_health.py`
- `services/alerts/alert_dispatcher.py`
- `tests/test_check_hetzner_paper_host_health.py`
- `tests/test_alert_dispatcher_fallback.py`
- `docs/HETZNER_PAPER_HOST.md`
- `scripts/SCRIPTS.md`
- `Makefile`
- `REMAINING_TASKS.md`

Operator command:

```bash
./.venv/bin/python scripts/check_hetzner_paper_host_health.py \
  --config configs/paper_evidence_campaigns.hetzner.example.json \
  --expected-commit <accepted-deployment-sha> \
  --backup-dir /srv/cryptkeep/backups \
  --min-free-gb 2 \
  --min-free-inodes 10000
```

Make target:

```bash
make check-hetzner-paper-host-health
```

The wrapper writes:

```text
.cbp_state/runtime/snapshots/hetzner_paper_host_health.latest.json
```

On failure, it calls `send_alert()` with external channels disabled, so the
existing local critical-alert fallback is written without Slack/email/network
requirements.

## Verification

Compile check:

```bash
./.venv/bin/python -m py_compile \
  services/alerts/alert_dispatcher.py \
  scripts/check_hetzner_paper_host_health.py \
  tests/test_alert_dispatcher_fallback.py \
  tests/test_check_hetzner_paper_host_health.py
```

Result:
- passed

Targeted tests:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_alert_dispatcher_fallback.py \
  tests/test_check_hetzner_paper_host_health.py
```

Result:
- `7 passed in 0.18s`

Root-script bootstrap slice:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_bootstrap_helper_adoption.py \
  tests/test_no_duplicate_script_bootstrap.py \
  tests/test_alert_dispatcher_fallback.py \
  tests/test_check_hetzner_paper_host_health.py
```

Result:
- `20 passed in 0.61s`

## Interpretation

SHOWN:
- The wrapper is read-only by construction and reports
  `ssh_invoked=false`, `restore_invoked=false`, and
  `collector_mutation_invoked=false`.
- Failed preflight checks are surfaced as `failed_checks`.
- A failure can produce both a latest health artifact and local alert fallback.
- Existing alert-dispatcher suppressed-error paths now use the defined
  `logger` object instead of undefined `_LOG`.

UNVERIFIED:
- Current Hetzner host health.
- Host scheduler/systemd/cron configuration.
- External alert delivery.
- Backup age checks.
- Backup restore rehearsal.
- Canonical `.cbp_state` migration safety.

Recommendation:
- Run this wrapper on the Hetzner host after each deploy and from a host-local
  scheduler once the isolated challenger is active.
- Keep backup restore rehearsal open until separately proven against an
  isolated restore directory.

## Acceptance State

Risk: HIGH

Reason:
- Host health alerting affects persistent financial-evidence background jobs
  and migration readiness, even though this implementation is read-only.

Acceptance state: READY_FOR_INDEPENDENT_REVIEW

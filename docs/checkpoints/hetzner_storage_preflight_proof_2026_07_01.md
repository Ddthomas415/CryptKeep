# Hetzner Storage Preflight Proof - 2026-07-01

## Scope

Active role: ENGINEER

Objective:
- Add read-only host storage checks to the Hetzner paper-host preflight.
- Fail closed when the backup directory is missing, free disk space is below
  threshold, or free inodes are below threshold.
- Do not SSH to Hetzner, stop collectors, start collectors, restore campaigns,
  copy state, or migrate canonical `.cbp_state`.

## Reason

Priority 16 requires disk/health alerting before canonical migration. The repo
already had Hetzner host preflight checks for repo files, venv, collector
imports, Git checkout, NTP, Tailscale, and campaign config. It did not check
backup directory presence, disk space, or inode availability.

SHOWN:
- `scripts/hetzner_paper_host_preflight.py` was the accepted read-only host
  readiness surface.
- `docs/HETZNER_PAPER_HOST.md` listed disk usage, inode availability, and backup
  status as host monitoring minimums.
- Persistent alerting and backup restore rehearsal remain separate blockers.

## Code Change

Changed:
- `scripts/hetzner_paper_host_preflight.py`
- `tests/test_hetzner_paper_host_preflight.py`
- `docs/HETZNER_PAPER_HOST.md`
- `scripts/SCRIPTS.md`

The preflight now includes a `storage_health` check with default thresholds:
- backup directory: repo parent `backups` directory
- minimum free disk space: 2 GiB
- minimum free inodes: 10,000

CLI overrides:

```bash
./.venv/bin/python scripts/hetzner_paper_host_preflight.py \
  --backup-dir /srv/cryptkeep/backups \
  --min-free-gb 2 \
  --min-free-inodes 10000
```

The report remains read-only and does not invoke restore/start/stop behavior.

## Verification

Compile check:

```bash
./.venv/bin/python -m py_compile \
  scripts/hetzner_paper_host_preflight.py \
  tests/test_hetzner_paper_host_preflight.py
```

SHOWN:
- passed

Targeted tests:

```bash
./.venv/bin/python -m pytest -q tests/test_hetzner_paper_host_preflight.py
```

SHOWN:
- `12 passed in 0.10s`

Root-script bootstrap slice:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_bootstrap_helper_adoption.py \
  tests/test_no_duplicate_script_bootstrap.py \
  tests/test_hetzner_paper_host_preflight.py
```

SHOWN:
- `25 passed in 0.57s`

## Interpretation

SHOWN:
- The preflight now fails closed for missing backup directory, insufficient
  free disk, and insufficient free inodes.
- Thresholds are explicit and operator-overridable.

UNVERIFIED:
- Current Hetzner host storage status.
- Persistent disk/health alerting.
- Backup restore rehearsal.
- Canonical `.cbp_state` migration safety.

Recommendation:
- Run the accepted preflight on Hetzner before restore or state transfer.
- Treat `storage_health=ok` as a minimum host-readiness check only.
- Keep persistent alerting and backup restore rehearsal open until separately
  proven.

## Acceptance State

Risk: HIGH

Reason:
- Host storage health affects persistent financial-evidence background jobs and
  state migration safety.

Acceptance state: ACCEPTED

Review reference:
- Independently reviewed and accepted by the human operator on 2026-07-01.

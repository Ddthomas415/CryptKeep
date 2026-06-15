# Hetzner Paper Campaign Host

Status: `READY_FOR_INDEPENDENT_REVIEW`

## Purpose

Use a private Hetzner host to improve paper-campaign uptime without changing
strategy behavior, promotion thresholds, or evidence qualification.

This runbook is paper-only. It does not approve live trading, remote dashboard
exposure, or exchange credentials on the host.

## Current Boundary

SHOWN:
- `restore_paper_campaigns.py` is portable because campaign state paths are
  resolved relative to the checked-out repo.
- Public OHLCV paper campaigns do not require exchange trading credentials.
- The existing Docker Compose stack publishes backend and dashboard ports on
  all interfaces.
- The repo's auth guidance does not classify remote/public deployment as
  hardened by default.

Therefore:
- do not deploy `docker/docker-compose.yml` unchanged;
- do not expose the dashboard or backend to the public internet;
- do not copy live exchange credentials;
- use the existing Python collector and recovery path directly;
- migrate one isolated challenger before considering canonical state.

## Stage 0 - Host Preparation

Requirements:
- a supported Linux host with SSH access;
- a non-root service account dedicated to CryptKeep;
- inbound access restricted to SSH from the operator or a private VPN;
- outbound HTTPS and DNS access for public market data and Git;
- synchronized UTC time;
- encrypted backups stored separately from the host.

Suggested repo location:

```text
/srv/cryptkeep/app
```

Prepare the accepted checkout and environment:

```bash
cd /srv/cryptkeep/app
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Before campaign deployment:

```bash
cd /srv/cryptkeep/app
git status --short --branch
./.venv/bin/python -m pytest -q \
  tests/test_paper_campaign_recovery.py \
  tests/test_restore_paper_campaigns.py
timedatectl show -p NTPSynchronized --value
```

Expected:
- the checked-out commit is the independently accepted deployment commit;
- targeted tests pass;
- time synchronization reports `yes`;
- no dashboard or backend listener is enabled.

Automatic startup after host reboot is not approved by this runbook. During the
isolated proof, the operator must explicitly run the reviewed restore command
after verifying host and state health.

## Stage 1 - Isolated Challenger Proof

Start with `ema_cross_default`, not canonical `.cbp_state`.

Use:

```text
configs/paper_evidence_campaigns.hetzner.example.json
```

The example:
- enables only the EMA paper challenger;
- uses its existing isolated state path;
- disables desktop notifications;
- retains the accepted two-attempt fail-closed policy.

### 1. Verify laptop ownership

On the laptop:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/ema_cross_default_daily" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
```

Record the PID, last completed UTC day, evidence counts, and current Git commit.

### 2. Stop the laptop collector

On the laptop:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/ema_cross_default_daily" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --stop
```

Repeat `--status`. Do not continue until `pid_alive=false`.

### 3. Create a content manifest

From the repo root on the laptop:

```bash
(
  cd .cbp_state_challengers/ema_cross_default_daily
  find . -type f -print0 |
    LC_ALL=C sort -z |
    xargs -0 shasum -a 256
) > /tmp/ema_cross_default.sha256
```

Archive or transfer the state directory and checksum through the operator's
authenticated SSH path. Do not put runtime state in Git.

### 4. Verify state on Hetzner

After transfer, from the Hetzner repo root:

```bash
(
  cd .cbp_state_challengers/ema_cross_default_daily
  find . -type f -print0 |
    LC_ALL=C sort -z |
    xargs -0 sha256sum
) > /tmp/ema_cross_default.server.sha256
```

Normalize checksum tool output if laptop and server tools use different command
names, then compare every relative path and digest. Do not start the collector
when any file is missing or mismatched.

### 5. Start and verify the challenger

On Hetzner:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --config configs/paper_evidence_campaigns.hetzner.example.json \
  --restore
```

Then:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --config configs/paper_evidence_campaigns.hetzner.example.json \
  --status
```

Required result:
- `ok=true`;
- `all_running=true`;
- one configured and running campaign;
- state path under the Hetzner repo;
- no matching laptop collector.

## Stage 2 - Observation

Do not migrate another campaign until the isolated challenger has:
- completed one healthy UTC window;
- emitted matching public-OHLCV provenance;
- preserved evidence counts across a host restart;
- produced a health alert or operator-visible failure for a controlled
  collector stop;
- completed one backup and isolated restore rehearsal.

Host monitoring minimum:
- collector process/status;
- last completed UTC day;
- campaign health, not only PID liveness;
- disk usage and inode availability;
- UTC/NTP synchronization;
- backup age and last restore-test result.

## Stage 3 - Canonical Migration

Canonical `.cbp_state` migration is a separate high-risk change. It requires:
- independent acceptance of the isolated challenger proof;
- a maintenance window after a completed UTC campaign;
- laptop stop confirmation;
- content-manifest verification;
- promotion-gate output captured before and after migration;
- one declared canonical owner;
- rollback state retained on the laptop.

Do not run canonical collectors on the laptop and Hetzner simultaneously.

## Rollback

If the Hetzner proof fails:
1. stop the Hetzner collector through the supported `--stop` command;
2. verify `pid_alive=false`;
3. preserve the failed host state and logs for audit;
4. compare it with the pre-migration checksum manifest;
5. copy back only after deciding which host owns the newest valid state;
6. restore the laptop collector with the existing recovery command;
7. verify campaign status and evidence counts.

Never merge two independently advanced SQLite/JSONL state trees.

## Acceptance Proof

Before this runbook is used:
- targeted recovery tests pass;
- the example manifest loads and disables desktop notification;
- an independent reviewer confirms no public service exposure is required;
- an independent reviewer confirms the single-owner and rollback procedures;
- the operator supplies the actual host, SSH, firewall, backup, and monitoring
  configuration through a separate reviewed deployment record.

# Hetzner Paper Campaign Host

Status: `ACCEPTED`

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

## Secure Account Access

Use a new Hetzner token for inventory and deployment planning. Do not reuse the
token that appeared in chat, and do not paste any replacement token into chat,
Git, an environment file, or a command argument.

Store the replacement through the hidden interactive prompt:

```bash
./.venv/bin/python scripts/set_hetzner_api_token.py
```

The command stores the token under the `crypto-bot-pro` OS-keyring namespace.
The account label is historical (`hetzner_cloud:readonly`); the token itself may
be read-only for inventory or short-lived read/write for accepted provisioning.
It does not print the token. Check only whether a token is configured:

```bash
./.venv/bin/python scripts/set_hetzner_api_token.py --status
```

After the token is stored, read the project inventory:

```bash
./.venv/bin/python scripts/hetzner_account_status.py
```

The inventory command performs GET requests only and returns resource counts
plus a non-secret server summary. It does not accept token arguments or use an
environment-variable fallback.

Prefer a persistent read-only token for inventory. If write access is required
for accepted provisioning, create a separate short-lived `Read & Write` token,
store it with the same hidden prompt only for the provisioning window, and
replace it with the read-only token afterward.

## SSH Access Method: Tailscale

Status: `ACCEPTED`

The CIDR-allowlist approach described in "Cloud Safeguards Command" below is
superseded for SSH access. The accepted access boundary is:

- Tailscale is installed on the Hetzner host (`ubuntu-4gb-nbg1-3`) and joined
  to the operator tailnet.
- The operator laptop is present in the same tailnet.
- Tailscale SSH is enabled on the host, so operator access uses the encrypted
  tailnet interface rather than the public IP.
- A Hetzner Cloud firewall named `cryptkeep-tailscale-only` is applied to
  `ubuntu-4gb-nbg1-3` with zero public inbound rules and default outbound
  allow.

This changes the SSH boundary from "public port 22, allowlisted to one CIDR"
to "no public port 22; SSH only reachable over the private Tailscale network."
It removes the dynamic-residential-IP fragility that a CIDR allowlist would
have had.

SHOWN on `2026-06-20T02:05:58Z`:
- `tailscale status` showed both `macbook-pro` (`100.76.178.88`) and
  `ubuntu-4gb-nbg1-3` (`100.86.128.9`) in the tailnet.
- `tailscale ssh cryptkeep@100.86.128.9 'hostname && whoami'` returned
  `ubuntu-4gb-nbg1-3` and `cryptkeep`.
- The Hetzner Cloud Console showed `cryptkeep-tailscale-only` with `0 Rules`,
  `1 Server`, and status `Fully applied`.
- `ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no
  cryptkeep@178.104.145.242 'hostname && whoami'` timed out on public port 22.

Operator access command:

```bash
tailscale ssh cryptkeep@100.86.128.9
```

## Cloud Safeguards Command

Status: `PARTIALLY_SUPERSEDED`

`scripts/hetzner_cloud_safeguards.py` plans cloud-side safety changes for the
paper host and applies them only with explicit operator confirmation.

Do not run this command with `--apply` until it is updated or explicitly
accepted for the Tailscale-only SSH boundary. Its existing SSH-firewall plan is
CIDR-based and creates/corrects `cryptkeep-paper-ssh-only`; the accepted live
boundary now uses the manually applied no-public-inbound firewall
`cryptkeep-tailscale-only`.

The command is dry-run by default:

```bash
./.venv/bin/python scripts/hetzner_cloud_safeguards.py \
  --server-id 126306158 \
  --ssh-source-cidr <operator-or-vpn-cidr>
```

Planned changes:
- create or correct the named SSH-only firewall `cryptkeep-paper-ssh-only`
  using a CIDR allowlist;
- attach that firewall to the selected server;
- enable delete/rebuild protection;
- enable Hetzner backups.

Safety gates:
- no token is accepted on the command line;
- missing SSH source CIDR stops before any Hetzner API request;
- `0.0.0.0/0` and `::/0` are rejected;
- `--apply` requires `--confirm-server-id` matching `--server-id`;
- the script prints JSON status only, never the token.

Apply only after independent review and a written decision on whether the
CIDR-based firewall behavior should be replaced by the accepted Tailscale-only
firewall behavior:

```bash
./.venv/bin/python scripts/hetzner_cloud_safeguards.py \
  --server-id 126306158 \
  --ssh-source-cidr <operator-or-vpn-cidr> \
  --apply \
  --confirm-server-id 126306158
```

Do not use a public-anywhere CIDR. Prefer a stable operator IP, VPN egress CIDR,
or emergency-access CIDR that is narrow enough to preserve the SSH boundary.

## Stage 0 - Host Preparation

Current status as of `2026-06-20T02:05:58Z`: implementation proof is complete
for host-level hardening and the Tailscale-only cloud firewall on
`ubuntu-4gb-nbg1-3`; campaign deployment remains blocked pending backup,
protection, restore, and single-owner proof.

SHOWN:
- `cryptkeep` non-root user exists with home `/srv/cryptkeep`.
- `/srv/cryptkeep/app`, `/srv/cryptkeep/state`, and
  `/srv/cryptkeep/backups` exist and are owned by `cryptkeep`.
- SSH password authentication is disabled.
- `MaxAuthTries` is reduced to `3`.
- Root login remains key-only through `PermitRootLogin prohibit-password`.
- UFW is active with default deny incoming and OpenSSH allowed.
- `fail2ban` is active for `sshd`.
- Hetzner Cloud Console reports `cryptkeep-tailscale-only` with `0 Rules`,
  `1 Server`, and status `Fully applied`.
- Public SSH to `178.104.145.242:22` times out.
- Tailscale SSH to `cryptkeep@100.86.128.9` succeeds.
- Local paper collectors remained on the laptop; no campaign state was copied
  and no server collector was started.
- Earlier read-only inventory on `2026-06-19T01:50:21Z`, before the Tailscale
  firewall change, reported one running server, `ubuntu-4gb-nbg1-3`
  (`id=126306158`, `cax11`, `nbg1`), one SSH key, two primary IPs, zero
  networks, zero volumes, and zero firewalls.

Still blocked:
- Hetzner backups are not enabled.
- Hetzner delete/rebuild protection is not enabled.
- The older CIDR-based `hetzner_cloud_safeguards.py --apply` path is
  superseded for SSH and must not be applied until it is updated or explicitly
  accepted for the Tailscale-only boundary.
- No isolated challenger has completed a server-hosted UTC cycle.
- No backup/restore rehearsal has been performed.

Do not migrate `.cbp_state` or start canonical collectors on this host until
those blockers are independently reviewed and resolved.

Requirements:
- a supported Linux host with SSH access;
- a non-root service account dedicated to CryptKeep;
- inbound access restricted to Tailscale SSH with no public inbound SSH;
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

# Hetzner Isolated Challenger Proof Record

Status: `DRAFT`

Use this template to record the first server-hosted isolated paper challenger
proof. Copy it to a dated file before use, for example:

```text
docs/deployment_records/hetzner_isolated_challenger_proof_YYYY_MM_DD.md
```

This record is for `ema_cross_default` only. It does not authorize canonical
`.cbp_state` migration, live trading, exchange credentials on the host, public
dashboard exposure, or multiple active owners for the same state tree.

## Acceptance Boundary

- Active role:
- Operator:
- Reviewer:
- Date/time UTC:
- Accepted deployment commit:
- Host:
- Tailscale IP:
- Laptop owner:
- Campaign:
- Strategy:
- State directory:

Required acceptance state before start: `ACCEPTED`.

## Preconditions

Record evidence, not intent.

- [ ] SHOWN: PR containing the deployment commit is merged to `master`.
- [ ] SHOWN: `review-stabilized` and `master` are aligned.
- [ ] SHOWN: no public SSH access to the Hetzner host.
- [ ] SHOWN: Tailscale SSH works to the Hetzner host.
- [ ] SHOWN: Hetzner firewall is `cryptkeep-tailscale-only` with zero public
  inbound rules.
- [ ] SHOWN: delete and rebuild protection are enabled.
- [ ] SHOWN: backups are enabled.
- [ ] SHOWN: no dashboard/backend public listener is started.
- [ ] SHOWN: no live exchange credentials are copied.
- [ ] SHOWN: laptop collector status has been captured before stop.
- [ ] SHOWN: single-owner rule is accepted before state transfer.

## Laptop Status Before Stop

Command:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/ema_cross_default_daily" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
```

Record:

```json
{}
```

Evidence summary:
- PID:
- `pid_alive`:
- `last_completed_day`:
- evidence counts:
- current Git commit:

## Laptop Stop Proof

Command:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/ema_cross_default_daily" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --stop
```

Post-stop command:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/ema_cross_default_daily" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
```

Required result:
- [ ] SHOWN: `pid_alive=false`
- [ ] SHOWN: no replacement laptop collector was started

Record:

```json
{}
```

## Manifest Create Proof

Command:

```bash
./.venv/bin/python scripts/paper_state_manifest.py create \
  --state-dir .cbp_state_challengers/ema_cross_default_daily \
  --output /tmp/ema_cross_default.manifest
```

Required result:
- [ ] SHOWN: `ok=true`
- [ ] SHOWN: manifest output is outside the state directory

Record:

```json
{}
```

## Transfer Proof

Transfer method:

Record the exact command used. Do not put runtime state in Git.

```bash
# fill in exact transfer command
```

Required result:
- [ ] SHOWN: state directory exists under the Hetzner repo checkout
- [ ] SHOWN: manifest file exists on the Hetzner host
- [ ] SHOWN: no canonical `.cbp_state` was transferred

## Hetzner Preflight Before Start

Command:

```bash
./.venv/bin/python scripts/hetzner_paper_host_preflight.py \
  --config configs/paper_evidence_campaigns.hetzner.example.json \
  --expected-commit <accepted-deployment-sha> \
  --require-state
```

Required result:
- [ ] SHOWN: `ok=true`

Record:

```json
{}
```

## Manifest Verify Proof

Command:

```bash
./.venv/bin/python scripts/paper_state_manifest.py verify \
  --state-dir .cbp_state_challengers/ema_cross_default_daily \
  --manifest /tmp/ema_cross_default.manifest
```

Required result:
- [ ] SHOWN: `ok=true`
- [ ] SHOWN: `missing=[]`
- [ ] SHOWN: `changed=[]`
- [ ] SHOWN: `extra=[]`

Record:

```json
{}
```

## Hetzner Start Proof

Command:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --config configs/paper_evidence_campaigns.hetzner.example.json \
  --restore
```

Required result:
- [ ] SHOWN: `ok=true`
- [ ] SHOWN: `all_running=true`
- [ ] SHOWN: exactly one configured campaign
- [ ] SHOWN: state path is under the Hetzner repo

Record:

```json
{}
```

## Single-Owner Proof

Laptop command:

```bash
CBP_STATE_DIR="$PWD/.cbp_state_challengers/ema_cross_default_daily" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
```

Hetzner command:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --config configs/paper_evidence_campaigns.hetzner.example.json \
  --status
```

Required result:
- [ ] SHOWN: laptop `pid_alive=false`
- [ ] SHOWN: Hetzner campaign `running=true`
- [ ] SHOWN: only one owner is advancing the state tree

Laptop record:

```json
{}
```

Hetzner record:

```json
{}
```

## First UTC Cycle Observation

Required result after one healthy UTC window:
- [ ] SHOWN: campaign status is healthy
- [ ] SHOWN: `last_completed_day` advanced on Hetzner
- [ ] SHOWN: public-OHLCV provenance exists
- [ ] SHOWN: evidence counts are preserved or advanced
- [ ] SHOWN: no laptop collector restarted

Record:

```json
{}
```

## Backup Restore Rehearsal

This is required before canonical migration. Do not restore over the active
host state.

Required result:
- [ ] SHOWN: backup exists after the hosted proof starts
- [ ] SHOWN: restore rehearsal target is isolated from active state
- [ ] SHOWN: restored state can be inspected without starting a collector
- [ ] SHOWN: restored manifest or evidence counts match the expected snapshot

Record:

```json
{}
```

## Rollback Record

Only fill this section if rollback is needed.

Reason:

Actions:
- [ ] SHOWN: Hetzner collector stopped
- [ ] SHOWN: Hetzner `pid_alive=false`
- [ ] SHOWN: failed host state/logs preserved
- [ ] SHOWN: newest valid owner was selected before copying any state
- [ ] SHOWN: laptop collector restored only after single-owner decision

Record:

```json
{}
```

## Final Decision

Acceptance state:

Allowed values:
- `ACCEPTED`
- `ACCEPTED_WITH_RISK`
- `INCOMPLETE`
- `BLOCKED`
- `REJECTED`

Decision:

Remaining risks:

Next action:

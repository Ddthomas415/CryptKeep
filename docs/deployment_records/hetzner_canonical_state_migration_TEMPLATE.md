# Hetzner Canonical State Migration Record

Status: `DRAFT`

Use this template only for a future canonical `.cbp_state` migration. Copy it
to a dated file before use, for example:

```text
docs/deployment_records/hetzner_canonical_state_migration_YYYY_MM_DD.md
```

This record is for canonical `es_daily_trend_v1` paper evidence state only. It
does not authorize live trading, exchange credentials on the host, public
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
- Reviewed Hetzner canonical campaign manifest:

Required acceptance state before start: `ACCEPTED`.

## Hard Stop Conditions

Stop immediately if any item below is true:

- [ ] UNRESOLVED: a reviewed Hetzner canonical campaign manifest does not exist.
- [ ] UNRESOLVED: laptop and Hetzner runtime ownership payloads are stale.
- [ ] UNRESOLVED: laptop canonical collector cannot be stopped cleanly.
- [ ] UNRESOLVED: state manifest verification reports missing, changed, or
  extra files.
- [ ] UNRESOLVED: host health preflight fails.
- [ ] UNRESOLVED: promotion-gate output after migration loses evidence counts
  or provenance-qualified round trips.
- [ ] UNRESOLVED: rollback owner is unclear.

Never merge two independently advanced SQLite/JSONL state trees.

## Preconditions

Record evidence, not intent.

- [ ] SHOWN: PR containing the deployment commit is merged to `master`.
- [ ] SHOWN: `review-stabilized` and `master` are aligned.
- [ ] SHOWN: Tailscale SSH works to the Hetzner host.
- [ ] SHOWN: Hetzner firewall remains `cryptkeep-tailscale-only` with zero
  public inbound rules.
- [ ] SHOWN: no dashboard/backend public listener is started.
- [ ] SHOWN: no live exchange credentials are copied.
- [ ] SHOWN: isolated `ema_cross_default` Hetzner proof is accepted:
  `docs/deployment_records/hetzner_isolated_challenger_proof_2026_06_20.md`.
- [ ] SHOWN: backup restore rehearsal is accepted for the isolated challenger.
- [ ] SHOWN: storage-health preflight proof is accepted.
- [ ] SHOWN: host-health alerting wrapper proof is accepted.
- [ ] SHOWN: maintenance window is declared.

## Reviewed Hetzner Canonical Manifest

The current Hetzner example manifest owns only `ema_cross_default`. Canonical
`.cbp_state` migration requires a separate reviewed manifest decision before
any state transfer.

Required result:
- [ ] SHOWN: manifest includes `es_daily_trend_v1`.
- [ ] SHOWN: manifest maps `es_daily_trend_v1` to `.cbp_state`.
- [ ] SHOWN: manifest uses strategy `sma_200_trend`.
- [ ] SHOWN: manifest uses `session_strategy_id=es_daily_trend_v1`.
- [ ] SHOWN: manifest has `desktop_notify=false` for headless Hetzner.
- [ ] SHOWN: laptop manifest ownership is updated or otherwise blocked so the
  laptop cannot restart the canonical collector after handoff.
- [ ] SHOWN: manifest change is independently reviewed before runtime use.

Manifest diff or record:

```text
fill in exact manifest path and diff summary
```

## Baseline Laptop And Gate Evidence

Capture before stopping the laptop owner.

Commands:

```bash
make status-paper-all
./.venv/bin/python scripts/report_paper_gate_qualification.py --json
./.venv/bin/python scripts/check_promotion_gates.py --json
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --config configs/paper_evidence_campaigns.laptop.json \
  --status
```

Record:

```json
{}
```

Required result:
- [ ] SHOWN: laptop owns `es_daily_trend_v1` before stop.
- [ ] SHOWN: current fill count is recorded.
- [ ] SHOWN: current all-history closed round trips are recorded.
- [ ] SHOWN: current provenance-qualified round trips are recorded.
- [ ] SHOWN: manual review state is recorded.

## Fresh Runtime Ownership Proof

Capture fresh payloads immediately before stopping the canonical laptop owner.

Laptop status JSON path:

```text
fill in path
```

Hetzner status JSON path:

```text
fill in path
```

Command:

```bash
./.venv/bin/python scripts/check_paper_campaign_runtime_ownership.py \
  --laptop-status-json <fresh-laptop-status.json> \
  --hetzner-status-json <fresh-hetzner-status.json> \
  --json
```

Record:

```json
{}
```

Required result:
- [ ] SHOWN: no duplicate running campaign name.
- [ ] SHOWN: no duplicate `session_strategy_id`.
- [ ] SHOWN: no duplicate normalized state directory.
- [ ] SHOWN: runtime owner split is understood before canonical handoff.

## Laptop Stop Proof

Command:

```bash
CBP_STATE_DIR="$PWD/.cbp_state" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --stop
```

Post-stop command:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --config configs/paper_evidence_campaigns.laptop.json \
  --status
```

Record:

```json
{}
```

Required result:
- [ ] SHOWN: `es_daily_trend_v1` laptop `pid_alive=false`.
- [ ] SHOWN: no replacement laptop canonical collector was started.
- [ ] SHOWN: noncanonical laptop campaigns are intentionally left running or
  intentionally stopped, with rationale recorded.

## Manifest Create Proof

Command:

```bash
./.venv/bin/python scripts/paper_state_manifest.py create \
  --state-dir .cbp_state \
  --output /tmp/es_daily_trend_v1_canonical.manifest
```

Required result:
- [ ] SHOWN: `ok=true`.
- [ ] SHOWN: manifest output is outside the state directory.
- [ ] SHOWN: `file_count` is recorded.
- [ ] SHOWN: `manifest_sha256` is recorded.

Record:

```json
{}
```

## Canonical State Backup Proof

Create a backup before transfer. Do not write the archive into `.cbp_state`.

Backup path:

```text
fill in path
```

Backup command:

```bash
# fill in exact backup command
```

Required result:
- [ ] SHOWN: backup archive exists outside `.cbp_state`.
- [ ] SHOWN: backup manifest exists outside `.cbp_state`.
- [ ] SHOWN: backup path is retained for rollback.

Record:

```json
{}
```

## Transfer Proof

Transfer method:

```bash
# fill in exact transfer command
```

Required result:
- [ ] SHOWN: transfer is scoped to `.cbp_state`.
- [ ] SHOWN: remote replacement target is under the Hetzner repo checkout.
- [ ] SHOWN: no challenger state is overwritten.
- [ ] SHOWN: no live exchange credentials are transferred.

## Hetzner Preflight Before Start

Run after transfer, before starting any canonical collector.

Command:

```bash
./.venv/bin/python scripts/hetzner_paper_host_preflight.py \
  --config <reviewed-hetzner-canonical-manifest.json> \
  --expected-campaign es_daily_trend_v1 \
  --expected-commit <accepted-deployment-sha> \
  --backup-dir /srv/cryptkeep/backups \
  --min-free-gb 2 \
  --min-free-inodes 10000 \
  --require-state
```

Required result:
- [ ] SHOWN: `ok=true`.
- [ ] SHOWN: `storage_health=ready`.
- [ ] SHOWN: `campaign_config=ready`.
- [ ] SHOWN: canonical state directory exists on Hetzner.

Record:

```json
{}
```

## Manifest Verify Proof

Command:

```bash
./.venv/bin/python scripts/paper_state_manifest.py verify \
  --state-dir .cbp_state \
  --manifest /tmp/es_daily_trend_v1_canonical.manifest
```

Required result:
- [ ] SHOWN: `ok=true`.
- [ ] SHOWN: `missing=[]`.
- [ ] SHOWN: `changed=[]`.
- [ ] SHOWN: `extra=[]`.

Record:

```json
{}
```

## Restore Rehearsal Before Start

Before starting the canonical collector on Hetzner, prove the transferred
backup can be restored into an isolated path without touching active state.

Isolated restore path:

```text
fill in path under /srv/cryptkeep/restore_rehearsals
```

Required result:
- [ ] SHOWN: restore target is isolated from active `.cbp_state`.
- [ ] SHOWN: restored manifest verification returns `ok=true`.
- [ ] SHOWN: restored evidence counts match the pre-transfer snapshot.
- [ ] SHOWN: restored runtime PID files are absent or ignored.
- [ ] SHOWN: no collector is started from the restored copy.

Record:

```json
{}
```

## Hetzner Start Proof

Command:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --config <reviewed-hetzner-canonical-manifest.json> \
  --restore
```

Status command:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --config <reviewed-hetzner-canonical-manifest.json> \
  --status
```

Required result:
- [ ] SHOWN: `ok=true`.
- [ ] SHOWN: `all_running=true`.
- [ ] SHOWN: exactly one canonical configured campaign starts.
- [ ] SHOWN: state path is under the Hetzner repo.
- [ ] SHOWN: no matching laptop canonical collector is running.

Record:

```json
{}
```

## Post-Migration Gate Comparison

Commands:

```bash
make status-paper-all
./.venv/bin/python scripts/report_paper_gate_qualification.py --json
./.venv/bin/python scripts/check_promotion_gates.py --json
```

Record:

```json
{}
```

Required result:
- [ ] SHOWN: fill counts are preserved or advanced.
- [ ] SHOWN: all-history closed round trips are preserved or advanced.
- [ ] SHOWN: provenance-qualified round trips are preserved or advanced.
- [ ] SHOWN: no evidence files are missing.
- [ ] SHOWN: manual-review state remains explicit.

## Rollback Plan

If migration fails before Hetzner start:
1. do not start the Hetzner canonical collector;
2. preserve transferred state for audit;
3. restart laptop canonical owner only from the known-good laptop state;
4. verify paper gate output matches the pre-stop baseline.

If migration fails after Hetzner start:
1. stop the Hetzner canonical collector;
2. verify `pid_alive=false`;
3. compare Hetzner state with the pre-migration manifest and backup;
4. choose exactly one owner based on the newest valid state;
5. never merge independently advanced SQLite/JSONL trees;
6. document the chosen owner and discarded state.

Rollback record:

```json
{}
```

## Acceptance State

This canonical migration record must end at `READY_FOR_INDEPENDENT_REVIEW`
until separately accepted by the human operator after evidence is complete.

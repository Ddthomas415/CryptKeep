# Hetzner Isolated Challenger Proof Record - 2026-06-20

Status: `CONTROLLED_STOP_READY_FOR_REVIEW_PENDING_FIRST_UTC_CYCLE`

This record covers only the isolated `ema_cross_default` paper challenger
migration proof. It does not authorize canonical `.cbp_state` migration, live
trading, exchange credentials on the host, public dashboard exposure, or
multiple active owners for the same state tree.

## Acceptance Boundary

- Active role: ENGINEER
- Operator: human repo owner
- Reviewer: human operator, same Codex session
- Date/time UTC: 2026-06-20T15:21Z
- Accepted deployment commit: `a3159aa646634c87fc4b8a2eb6d47928c371215a`
- Host: `ubuntu-4gb-nbg1-3`
- Tailscale IP: `100.86.128.9`
- Laptop owner: `/Users/baitus/Downloads/crypto-bot-pro`
- Campaign: `ema_cross_default`
- Strategy: `ema_cross`
- State directory: `.cbp_state_challengers/ema_cross_default_daily`

Required acceptance state before start: `ACCEPTED`.

## Preconditions

- [x] SHOWN: PR #87 containing the deployment commit was merged to `master`.
- [x] SHOWN: `review-stabilized` and `master` are aligned at `a3159aa64`.
- [x] SHOWN: Tailscale SSH works to the Hetzner host.
- [x] SHOWN: Hetzner preflight returns `ok=true` before state transfer.
- [x] SHOWN: no dashboard/backend public listener was started by this proof.
- [x] SHOWN: no live exchange credentials were copied by this proof.
- [x] SHOWN: laptop collector status was captured before stop.
- [x] SHOWN: single-owner rule is accepted before state transfer.
- [x] SHOWN: transferred state manifest verified on Hetzner after removing
  macOS AppleDouble `._*` metadata sidecars.
- [x] SHOWN: Hetzner collector starts and owns the state tree.

Prior blocker:
- SHOWN: the first Hetzner start failed because the host lacked `pip`, `yaml`,
  and `python3.12-venv`.
- SHOWN: direct `cryptkeep` sudo was unavailable because the account password
  was not known.
- SHOWN: Tailscale SSH as `root` was available and used to complete the host
  dependency setup without changing local campaign ownership.
- SHOWN: as of 2026-06-20T16:20Z, Hetzner `.venv` has `pip 26.1.2`, `import
  yaml` succeeds, importing `services.analytics.paper_strategy_evidence_service`
  prints `collector_import_ok`, and host preflight returns `ok=true`.
- Consequence: the dependency blocker is resolved, but the migration must be
  retried from the beginning because local `ema_cross_default` was restored and
  the stale remote state copy was removed.

## Laptop Status Before Stop

Command:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py --status
```

Record:

```json
{
  "ok": true,
  "all_running": true,
  "campaign": "ema_cross_default",
  "pid": 80259,
  "pid_alive": true,
  "status": "idle",
  "reason": "waiting_for_next_day",
  "last_completed_day": "2026-06-20",
  "state_dir": "/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/ema_cross_default_daily",
  "jsonl_evidence": {
    "fill": 4,
    "order": 4,
    "session": 16,
    "total_records": 42
  },
  "paper_history": {
    "fills_total": 5,
    "closed_trades_total": 2,
    "net_realized_pnl_total": -0.007617610697479266
  },
  "git_commit": "a3159aa646634c87fc4b8a2eb6d47928c371215a"
}
```

Evidence summary:
- SHOWN: canonical `es_daily_trend_v1` and `breakout_default` laptop collectors
  were also running/idle before the isolated `ema_cross_default` migration.
- SHOWN: no local state was transferred before this status capture.

## Hetzner Preflight Before State Transfer

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 'set -eu; cd /srv/cryptkeep/app; \
  git fetch origin master review-stabilized; \
  git checkout --detach a3159aa646634c87fc4b8a2eb6d47928c371215a; \
  ./.venv/bin/python scripts/hetzner_paper_host_preflight.py \
    --config configs/paper_evidence_campaigns.hetzner.example.json \
    --expected-commit a3159aa646634c87fc4b8a2eb6d47928c371215a'
```

Required result:
- [x] SHOWN: `ok=true`
- [x] SHOWN: `python_venv` status is `repo_venv`
- [x] SHOWN: `git_checkout` status is `clean`
- [x] SHOWN: `time_sync` status is `ntp_synchronized`
- [x] SHOWN: `tailscale` status is `running`
- [x] SHOWN: `campaign_config` status is `ready`
- [x] SHOWN: transferred state was still absent before transfer.

Record:

```json
{
  "ok": true,
  "repo_root": "/srv/cryptkeep/app",
  "expected_commit": "a3159aa646634c87fc4b8a2eb6d47928c371215a",
  "campaign_config": {
    "name": "ema_cross_default",
    "state_dir": "/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily",
    "state_exists": false
  }
}
```

## Laptop Stop Proof

Command:

```bash
CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/ema_cross_default_daily \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --stop
```

Post-stop command:

```bash
CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/ema_cross_default_daily \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
```

Required result:
- [x] SHOWN: stop flag was written.
- [x] SHOWN: PID `80259` remained alive because the daily loop was sleeping for
  the configured `300` second poll interval.
- [x] SHOWN: targeted `SIGTERM` to PID `80259` stopped only the isolated
  `ema_cross_default` collector.
- [x] SHOWN: post-stop status reported `pid_alive=false`.

## Manifest Create Proof

Command:

```bash
./.venv/bin/python scripts/paper_state_manifest.py create \
  --state-dir .cbp_state_challengers/ema_cross_default_daily \
  --output /tmp/ema_cross_default.manifest
```

Required result:
- [x] SHOWN: `ok=true`
- [x] SHOWN: `file_count=249`
- [x] SHOWN: `manifest_sha256=b5939d7cd03c6e0a50824ffa133a0f2bea51045b6fe6248e7ec63445a50d1b80`
- [x] SHOWN: manifest output was outside the state directory.

## Transfer Proof

Transfer method:

```bash
tar -czf - \
  -C /Users/baitus/Downloads/crypto-bot-pro .cbp_state_challengers/ema_cross_default_daily \
  -C /private/tmp ema_cross_default.manifest \
| tailscale ssh cryptkeep@100.86.128.9 'set -eu; cd /srv/cryptkeep/app; \
    tar -xzf -; \
    mv -f ema_cross_default.manifest /tmp/ema_cross_default.manifest; \
    test -d .cbp_state_challengers/ema_cross_default_daily; \
    test -f /tmp/ema_cross_default.manifest; \
    echo transfer_ok'
```

Required result:
- [x] SHOWN: `transfer_ok`
- [x] SHOWN: canonical `.cbp_state` was not transferred.
- [x] SHOWN: initial verify had `missing=[]` and `changed=[]`, but failed
  because macOS AppleDouble `._*` metadata sidecars were extracted as extras.
- [x] SHOWN: after removing only `._*` sidecars under the isolated transferred
  tree and the stray `._ema_cross_default.manifest`, manifest verification
  passed exactly.

## Hetzner Preflight Before Start

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 'set -eu; cd /srv/cryptkeep/app; \
  ./.venv/bin/python scripts/hetzner_paper_host_preflight.py \
    --config configs/paper_evidence_campaigns.hetzner.example.json \
    --expected-commit a3159aa646634c87fc4b8a2eb6d47928c371215a \
    --require-state'
```

Required result:
- [x] SHOWN: `ok=true`
- [x] SHOWN: required files present.
- [x] SHOWN: repo-local venv detected.
- [x] SHOWN: Git checkout clean at `a3159aa64`.
- [x] SHOWN: NTP synchronized.
- [x] SHOWN: Tailscale running.
- [x] SHOWN: campaign config state existed before attempted start.

## Manifest Verify Proof

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 'set -eu; cd /srv/cryptkeep/app; \
  ./.venv/bin/python scripts/paper_state_manifest.py verify \
    --state-dir .cbp_state_challengers/ema_cross_default_daily \
    --manifest /tmp/ema_cross_default.manifest'
```

Required result:
- [x] SHOWN: `ok=true`
- [x] SHOWN: `expected_file_count=249`
- [x] SHOWN: `actual_file_count=249`
- [x] SHOWN: `missing=[]`
- [x] SHOWN: `changed=[]`
- [x] SHOWN: `extra=[]`

## Hetzner Start Proof

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 'set -eu; cd /srv/cryptkeep/app; \
  ./.venv/bin/python scripts/restore_paper_campaigns.py \
    --config configs/paper_evidence_campaigns.hetzner.example.json \
    --restore'
```

Result:
- [x] SHOWN: remote start failed with `collector_exit_1`.
- [x] SHOWN: bounded foreground collector run exposed
  `ModuleNotFoundError: No module named 'yaml'`.
- [x] SHOWN: `.venv/bin/python -m pip` failed with `No module named pip`.
- [x] SHOWN: remote host lacks `python3.12-venv`/`ensurepip`.
- [x] SHOWN: remote sudo requires the operator password.
- [x] SHOWN: no Hetzner collector remained running after the failed start.

## Single-Owner Proof

Result:
- [x] SHOWN: local isolated collector was stopped before state transfer.
- [x] SHOWN: Hetzner collector did not start because dependencies were missing.
- [x] SHOWN: local isolated collector was restored afterward as PID `19570`.
- [x] SHOWN: final laptop status reported all three campaigns running.
- [x] SHOWN: stale remote transferred state and manifest were removed.
- [x] SHOWN: final Hetzner preflight without state returned `ok=true`, with
  `state_exists=false`.

Rollback state:
- Local `ema_cross_default` is the active owner again.
- Hetzner has no transferred challenger state.
- Future attempt must rerun stop, manifest, transfer, verify, and start after
  the host dependency setup is corrected.

## First UTC Cycle Observation

Pending.

## Backup Restore Rehearsal

Date/time UTC: `2026-06-20T20:11:43Z`

Scope:
- Rehearsed backup/restore only for the isolated `ema_cross_default` challenger.
- Did not restore over active Hetzner state.
- Did not stop the active Hetzner collector.
- Did not start a collector from the restored copy.
- Did not touch canonical `.cbp_state`.

Backup paths:
- Archive:
  `/srv/cryptkeep/backups/ema_cross_default_20260620T201143Z.tar.gz`
- Manifest:
  `/srv/cryptkeep/backups/ema_cross_default_20260620T201143Z.manifest`
- Isolated restore root:
  `/srv/cryptkeep/restore_rehearsals/ema_cross_default_20260620T201143Z`

Backup manifest:
- [x] SHOWN: manifest create returned `ok=true`.
- [x] SHOWN: `file_count=248`.
- [x] SHOWN:
  `manifest_sha256=fca0c5700899708029c0287d5dde58b8c851bffd6e03b42bd13be273a1c15a8e`.
- [x] SHOWN: manifest path was outside the active state tree.

Restore verification:
- [x] SHOWN: restore target was isolated from active state:
  `/srv/cryptkeep/restore_rehearsals/ema_cross_default_20260620T201143Z/.cbp_state_challengers/ema_cross_default_daily`.
- [x] SHOWN: restored manifest verification returned `ok=true`.
- [x] SHOWN: `expected_file_count=248`.
- [x] SHOWN: `actual_file_count=248`.
- [x] SHOWN: `missing=[]`.
- [x] SHOWN: `changed=[]`.
- [x] SHOWN: `extra=[]`.
- [x] SHOWN: restored evidence file count was `24`.
- [x] SHOWN: active evidence file count was `24`.
- [x] SHOWN: restored runtime pid file count was `0`.
- [x] SHOWN: active Hetzner campaign remained running as
  `ema_cross_default`, PID `1286864`.

Acceptance state:
- `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #91 was merged.

## Controlled Stop And Recovery Proof

Date/time UTC: `2026-06-20T20:21:10Z`

Evidence source:
- Operator-pasted terminal output from
  `/Users/baitus/.codex/attachments/87e72095-522b-4bff-95b8-4bf8d30f096a/pasted-text.txt`.

Scope:
- Stopped only the isolated Hetzner `ema_cross_default` challenger.
- Did not stop or migrate canonical `.cbp_state`.
- Did not stop laptop `es_daily_trend_v1`.
- Did not stop laptop `breakout_default`.
- Restarted through the Hetzner campaign manifest after capturing the
  operator-visible stopped state.

Controlled stop proof:
- [x] SHOWN: stop flag was written to
  `/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily/runtime/flags/paper_strategy_evidence.stop`.
- [x] SHOWN: status after the stop returned `ok=false` at the manifest level.
- [x] SHOWN: `all_running=false`.
- [x] SHOWN: `running_count=0`.
- [x] SHOWN: `status=stopped`.
- [x] SHOWN: `reason=stop_requested`.
- [x] SHOWN: `pid_alive=false`.
- [x] SHOWN: `has_pid_file=false`.
- [x] SHOWN: operator-visible summary text was
  `Paper evidence collector daily loop was stopped by request.`

Recovery proof:
- [x] SHOWN: `restore_paper_campaigns.py --config
  configs/paper_evidence_campaigns.hetzner.example.json --restore` returned
  `ok=true`.
- [x] SHOWN: exactly one campaign was configured.
- [x] SHOWN: `all_running=true`.
- [x] SHOWN: `running_count=1`.
- [x] SHOWN: `ema_cross_default` restarted as PID `1287182`.
- [x] SHOWN: `pid_alive=true`.
- [x] SHOWN: `status=idle`.
- [x] SHOWN: `reason=waiting_for_next_day`.
- [x] SHOWN: `last_completed_day=2026-06-20`.
- [x] SHOWN: state path remained under
  `/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily`.

Acceptance state:
- `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #92 was merged.

## Host Dependency Setup Completed

Root setup command executed by Codex over Tailscale SSH:

```bash
tailscale ssh root@100.86.128.9 'set -e
cd /srv/cryptkeep/app
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3.12-venv
rm -rf .venv
sudo -u cryptkeep python3 -m venv .venv
sudo -u cryptkeep ./.venv/bin/python -m pip install --upgrade pip
sudo -u cryptkeep ./.venv/bin/pip install -r requirements.txt
sudo -u cryptkeep ./.venv/bin/python -c "import yaml; print(\"yaml_ok\")"'
```

Verification:
- [x] SHOWN: package install completed and installed `python3.12-venv`.
- [x] SHOWN: requirements install completed in `/srv/cryptkeep/app/.venv`.
- [x] SHOWN: `yaml_ok` printed on the host.
- [x] SHOWN: `pip 26.1.2` is available from the host venv.
- [x] SHOWN: `import services.analytics.paper_strategy_evidence_service`
  printed `collector_import_ok`.
- [x] SHOWN: Hetzner preflight returned `ok=true`.
- [x] SHOWN: remote state remains absent: `REMOTE_STATE=absent`.
- [x] SHOWN: laptop campaigns remain active and local `ema_cross_default` is
  still the owner.

Next required action:
- Accept and merge PR #89 so the stronger `collector_imports` preflight is on
  `master`.
- Rerun the isolated challenger migration from the beginning: stop local
  `ema_cross_default`, create a fresh manifest, transfer fresh state, verify
  manifest, run preflight with `--require-state`, then start on Hetzner.

## Retry After PR #89 Merge

Date/time UTC: `2026-06-20T20:00:31Z`

Accepted deployment commit:
- `b86105b1f491058aac235dcbb33748729dee7297`

Scope:
- Migrated only `ema_cross_default`.
- Did not migrate canonical `.cbp_state`.
- Did not stop `es_daily_trend_v1`.
- Did not stop `breakout_default`.
- Did not copy live exchange credentials.
- Did not expose a dashboard or public listener.

GitHub/repo state:
- [x] SHOWN: PR #89 merged to `master` as
  `b86105b1f491058aac235dcbb33748729dee7297`.
- [x] SHOWN: local `review-stabilized` fast-forwarded to `origin/master`.
- [x] SHOWN: `review-stabilized` pushed to `origin/review-stabilized`.
- [x] SHOWN: Hetzner checkout updated to `review-stabilized` at
  `b86105b1f491058aac235dcbb33748729dee7297`.

Host preflight before retry:
- [x] SHOWN: Hetzner preflight returned `ok=true` with `require_state=false`.
- [x] SHOWN: `collector_imports` returned `collector_import_ok`.
- [x] SHOWN: `git_checkout` was clean at
  `b86105b1f491058aac235dcbb33748729dee7297`.
- [x] SHOWN: Tailscale was running with `100.86.128.9`.
- [x] SHOWN: remote `ema_cross_default` state was absent before retry.

Local stop proof:
- [x] SHOWN: local `ema_cross_default` stop flag was written.
- [x] SHOWN: the daily-loop collector remained alive while sleeping on its
  configured `300` second poll interval.
- [x] SHOWN: targeted `SIGINT` was sent only to PID `19570`, the local
  `ema_cross_default` daily-loop collector.
- [x] SHOWN: local post-stop status reported `ema_cross_default`
  `pid_alive=false`, `has_pid_file=false`, and `running=false`.
- [x] SHOWN: local `es_daily_trend_v1` remained running as PID `80255`.
- [x] SHOWN: local `breakout_default` remained running as PID `80263`.

Fresh manifest proof:
- [x] SHOWN: manifest create returned `ok=true`.
- [x] SHOWN: `file_count=248`.
- [x] SHOWN:
  `manifest_sha256=d3f3494ada77ff03dd506ebfc573b696f465dbcb596e784695924b56eff17b59`.
- [x] SHOWN: manifest path was
  `/private/tmp/ema_cross_default_20260620.manifest`, outside the state tree.

Transfer proof:
- [x] SHOWN: state transfer completed with exit code `0`.
- [x] SHOWN: transfer was scoped to
  `.cbp_state_challengers/ema_cross_default_daily`.
- [x] SHOWN: remote replacement removed only
  `/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily`.
- [x] SHOWN: tar emitted macOS xattr warnings for
  `LIBARCHIVE.xattr.com.apple.provenance`; content integrity was checked by the
  manifest afterward.

Remote manifest verification:
- [x] SHOWN: manifest verify returned `ok=true`.
- [x] SHOWN: `expected_file_count=248`.
- [x] SHOWN: `actual_file_count=248`.
- [x] SHOWN: `missing=[]`.
- [x] SHOWN: `changed=[]`.
- [x] SHOWN: `extra=[]`.

Remote require-state preflight:
- [x] SHOWN: Hetzner preflight returned `ok=true` with `require_state=true`.
- [x] SHOWN: `python_venv` status was `repo_venv`.
- [x] SHOWN: `collector_imports` status was `collector_imports_ok`.
- [x] SHOWN: `git_checkout` status was `clean`.
- [x] SHOWN: `time_sync` status was `ntp_synchronized`.
- [x] SHOWN: `tailscale` status was `running`.
- [x] SHOWN: `campaign_config` status was `ready` and `state_exists=true`.

Hetzner start proof:
- [x] SHOWN: `restore_paper_campaigns.py --config
  configs/paper_evidence_campaigns.hetzner.example.json --restore` returned
  `ok=true`.
- [x] SHOWN: one campaign was configured.
- [x] SHOWN: one campaign was running.
- [x] SHOWN: `ema_cross_default` launched as Hetzner PID `1286864`.
- [x] SHOWN: status was `idle` with
  `reason=waiting_for_next_day`.
- [x] SHOWN: state path was
  `/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily`.

Single-owner proof:
- [x] SHOWN: local process scan returned only local PIDs `80255` and `80263`
  for the remaining `sma_200_trend` and `breakout_donchian` collectors.
- [x] SHOWN: no local `ema_cross` collector was running after migration.
- [x] SHOWN: Hetzner `ema_cross_default` was running as PID `1286864`.

Current ownership:
- `es_daily_trend_v1`: laptop owner, PID `80255`.
- `breakout_default`: laptop owner, PID `80263`.
- `ema_cross_default`: Hetzner owner, PID `1287182`.

Remaining required proof:
- First server-hosted UTC cycle observation for `ema_cross_default`.
- Human review of the controlled-stop/recovery proof before any canonical
  `.cbp_state` migration.

Acceptance state:
- `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #90 was merged.

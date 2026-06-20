# Hetzner Isolated Challenger Proof Record - 2026-06-20

Status: `READY_TO_RETRY_AFTER_PR89`

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
- [ ] SHOWN: Hetzner collector starts and owns the state tree.

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

Pending. Required before canonical migration.

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

# Hetzner Read-Only Status - 2026-08-24

## Scope

Read-only status refresh after merging the Hetzner dependency-alignment runbook.
No files, services, packages, configs, timers, campaigns, or virtualenv state
were changed on the host.

## Local Repo State

Commands:

```bash
git status --short --branch
git log --oneline -5 --decorate
gh pr list --state open --json number,title,headRefName,baseRefName,mergeStateStatus
./.venv/bin/python tools/repo_doctor.py
```

Result:

- Local checkout: `master`.
- Local/remote state: clean and aligned with `origin/master`.
- Current commit: `2bb6a411c docs: add Hetzner dependency alignment runbook (#531)`.
- Open PRs: none.
- Repo doctor: supported baseline present, no missing baseline dirs, no
  non-canonical duplicates, and no suspicious top-level files.

## Local Paper Campaigns

Command:

```bash
make status-paper-campaigns
```

Result:

- `all_running=true`
- `running_count=2`
- `es_daily_trend_v1`: running, `idle`, reason `waiting_for_next_day`,
  `fills_total=20`, `closed_trades_total=10`,
  `net_realized_pnl_total=31.4368625683357`
- `breakout_default`: running, `idle`, reason `waiting_for_next_day`,
  `fills_total=22`, `closed_trades_total=11`,
  `net_realized_pnl_total=4.277597190923208`

## Local Paper Gate

Command:

```bash
make status-paper-gate-velocity-json
```

Result:

- `policy_id=slow_daily_single_symbol_v1`
- `thresholds_ready=false`
- Round trips: `3/5` qualified, `2` remaining
- Qualified bars: `63/60`, ready
- Overall blocking threshold: `round_trips`
- Projected completion: `2026-09-14T01:58:58Z`
- Diagnostic-only legacy/all-history round trips: `7`

## Roadmap And Operator Queue

Commands:

```bash
make roadmap-tracking-status-json
make operator-next-actions-json OPERATOR_NEXT_ACTIONS_REASON=remaining_capped_live_proof OPERATOR_NEXT_ACTIONS_MAX=8
make operator-read-only-command-status-json
```

Result:

- Roadmap tracking: `ok=true`
- All `13` roadmap-listed commands exist in `Makefile`.
- All `12` linked source docs exist and are linked.
- Operator read-only command registry: `23/23` commands wired.
- Remaining generated capped-live actions are host/operator proof items; this
  checkpoint does not close those proofs.

## Hetzner Crypto-Edge Runtime

Command:

```bash
HETZNER_STATUS_TRANSPORT=ssh HETZNER_SSH_TARGET=cryptkeep@100.86.128.9 \
  make status-hetzner-edge-runtime
```

Result:

- `status=hetzner_crypto_edge_runtime_ready`
- `ok=True`
- `blocking_checks=0`
- Remote checkout: `master`
- Remote head: `a10aca01fc37de181cc32d17a30e5d677050f901`
- Recommendation: keep collector and cadence checker schedules under host
  monitoring.

## Hetzner Paper Campaign

Command:

```bash
HETZNER_STATUS_TRANSPORT=ssh HETZNER_SSH_TARGET=cryptkeep@100.86.128.9 \
  make status-paper-hetzner
```

Result:

- Campaigns: `1/1` running
- `all_running=True`
- `ema_cross_default`: `idle`, reason `waiting_for_next_day`,
  strategy `ema_cross`, fills `15`, closed trades `7`, net PnL `-2.3016`
- Latest fill: `2026-08-24T00:01:55.857611+00:00`
- Recommendation: `continue_paper_observation`

## Hetzner Supply Chain

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/check_supply_chain.py --json'
```

Result:

- Remote checkout: `a10aca01fc37de181cc32d17a30e5d677050f901`
- `git_dirty=false`
- Pin integrity: `ok=true`
- Environment: `ok=false`
- Mismatches remain for the same 10 packages documented in the dependency
  alignment runbook: `aiohttp`, `click`, `cryptography`, `gitpython`, `idna`,
  `pillow`, `setuptools`, `starlette`, `tornado`, `urllib3`
- `not_installed=[]`
- Vulnerability audit: `ran=false`, reason `not_requested`

## Remaining Active Shape

- Local implementation/PR queue is clear.
- Local and Hetzner paper campaigns are running and idle after the
  2026-08-24 daily cycle.
- Hetzner crypto-edge runtime is ready.
- Hetzner dependency-pin alignment remains open and unchanged.
- Host vulnerability audit remains unrun and still requires explicit approval
  or waiver because it may disclose host package inventory externally.

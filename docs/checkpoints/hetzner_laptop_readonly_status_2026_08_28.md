# Hetzner and Laptop Read-Only Status - 2026-08-28

## Scope

This checkpoint records the status refresh after PR #553 merged. It includes one
guarded laptop paper-campaign recovery command and three Hetzner read-only
status commands. It does not install packages, deploy code, restart host
services, change configs, change gates, promote strategies, route orders, or
touch live execution.

## Commands

Laptop campaign recovery:

```bash
make recover-paper-campaigns
```

Hetzner read-only status:

```bash
make status-hetzner-dependency-alignment-json
make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=30
make status-paper-hetzner HETZNER_STATUS_TIMEOUT_SEC=30
```

The Hetzner commands were run outside the sandbox because the sandboxed SSH path
previously returned `ssh_operation_not_permitted`.

## Laptop Paper Campaigns

SHOWN:

- The first sandboxed `make recover-paper-campaigns` attempt was blocked before
  launch by Coinbase public-OHLCV preflight failures.
- The out-of-sandbox retry passed public-OHLCV preflight on the first attempt
  for both configured laptop campaigns.
- `es_daily_trend_v1` launched with PID `40882`.
- `breakout_default` launched with PID `40894`.
- The recovery command returned `ok=true`, `all_running=true`, and
  `running_count=2`.
- Follow-up `make status-paper-soak` reported `Campaigns: 2/2 running
  (all_running=True)`.

Gate status from the same follow-up:

- `ready=False`
- `machine_ready=False`
- `manual_review_required=True`
- `round trips=3/5`, `2` remaining
- `days=115/45`, `0` remaining
- `expectancy=insufficient paper-history fills for calculation`
- `evidence writer=status=ok consecutive=0/3 total=0`

## Hetzner Dependency Alignment

SHOWN:

- Host SSH/Tailscale worked outside the sandbox.
- The command was read-only: `deploy_invoked=false`,
  `pip_install_invoked=false`, and `service_restart_invoked=false`.
- Host branch matched `master`.
- Host checkout was clean.
- Host commit was `6c0903d318756d27eb6414a01abbfc8c8e879ae5`.
- Expected local `origin/master` commit was
  `5b39d051e8d0063a8fc731c68d384f63e1f5a9d3`.
- Pin integrity was OK.
- Environment alignment was still blocked by the same 10 pinned-package
  mismatches:
  `aiohttp`, `click`, `cryptography`, `gitpython`, `idna`, `pillow`,
  `setuptools`, `starlette`, `tornado`, and `urllib3`.
- Read-only `pip --dry-run` returned `0` and would change those 10 packages.
- Vulnerability audit was not requested.

Interpretation:

- Dependency alignment remains open.
- The current blocker is stale host checkout plus pinned-package drift, not SSH
  transport.
- No host package install was run.

## Hetzner Crypto-Edge Runtime

SHOWN:

- `status=hetzner_crypto_edge_runtime_ready`
- `ok=True`
- `read_only=True`
- `remote_head=6c0903d318756d27eb6414a01abbfc8c8e879ae5`
- `remote_branch=master`
- `blocking_checks=0`

Recommendation from the command:

- Keep the collector and cadence checker schedules under host monitoring.

## Hetzner Paper Campaign

SHOWN:

- `Campaigns: 1/1 running (all_running=True)`
- `ema_cross_default`: `idle`, `waiting_for_next_day`
- Strategy: `ema_cross`
- `fills=15`
- `closed=7`
- `pnl=-2.3016`
- Latest fill: `2026-08-24T00:01:55.857611+00:00`
- The campaign had already recorded session evidence for `2026-08-28`.

## Next Actions

1. Sync `/srv/cryptkeep/app` from `6c0903d318756d27eb6414a01abbfc8c8e879ae5`
   to current master.
2. Run the approved dependency-alignment runbook if the operator still approves
   the no-restart host virtualenv update.
3. Preserve pre-change `pip freeze` output before mutating the host virtualenv.
4. Re-run dependency alignment, edge runtime, paper campaign status, and
   supply-chain checks after sync/alignment.

Acceptance state: `INCOMPLETE`.

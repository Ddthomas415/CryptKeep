# Paper Campaign Recovery

Use this runbook after a laptop restart or any event that may have terminated
the detached paper evidence collectors.

Executable guard: `tests/test_paper_campaign_recovery_runbook_guard.py` pins
the operator-facing recovery contract in this document. If recovery commands,
OHLCV blocked-state behavior, ownership split, or restart safety boundaries
change, update that test and this runbook together.

## Status

For the routine check-in across both the laptop and Hetzner paper campaigns,
run:

```bash
make status-paper-all
```

This is read-only. It runs the laptop soak summary and the Hetzner-owned EMA
campaign status in sequence, then exits nonzero if either side reports failure.

For raw local campaign process status, run:

```bash
make status-paper-campaigns
```

This is read-only. It checks the configured canonical and challenger state
directories and exits nonzero if any selected collector is not alive or is
reporting unhealthy campaign status.

For a single local-only check-in that combines laptop campaign health with the paper
promotion gate summary, run:

```bash
make status-paper-soak
```

The `make` shortcut reads `configs/paper_evidence_campaigns.laptop.json` by
default. That manifest reflects the current laptop ownership split:
`es_daily_trend_v1` and `breakout_default` run on the laptop, while
`ema_cross_default` is owned by the Hetzner host through
`configs/paper_evidence_campaigns.hetzner.example.json`.
`make status-paper-soak` uses the same local manifest. Check Hetzner-owned
campaigns through the accepted Tailscale SSH path:

```bash
make status-paper-hetzner
```

This runs the existing remote read-only status command through a timeout-aware
local Tailscale SSH wrapper and formats the returned JSON into a concise
campaign-health summary. It does not start, stop, or restore a campaign. The
Make target waits up to `HETZNER_STATUS_TIMEOUT_SEC=15` seconds by default. If
Tailscale SSH requires browser authentication, fails, times out, or returns
malformed JSON, the command exits non-zero and prints the explicit failure
reason, bounded stdout/stderr previews, and the investigation recommendation.
Known local Tailscale failures are classified before JSON parsing; for example,
`tailscale_cli_preferences_unavailable` means the local Tailscale CLI could not
load preferences, and `tailscale_ssh_auth_required` means Tailscale SSH needs
browser authentication before the remote status can be trusted.

Override the remote target or app directory only when the deployment record
changes:

```bash
HETZNER_SSH_TARGET=cryptkeep@100.86.128.9 \
HETZNER_APP_DIR=/srv/cryptkeep/app \
  make status-paper-hetzner
```

Override the status timeout only when a slower host check is intentional:

```bash
HETZNER_STATUS_TIMEOUT_SEC=30 make status-paper-hetzner
```

## Restore

Run:

```bash
make restore-paper-campaigns
```

The restore command:

1. checks each configured collector;
2. leaves live collectors unchanged;
3. starts only dead collectors through
   `run_paper_strategy_evidence_collector.py --daily-loop --detach`;
4. checks status again and reports the replacement PID.

If a collector is alive but unhealthy, for example parked after an older
`no_public_ohlcv` failure, use guarded recovery instead:

```bash
make recover-paper-campaigns
```

This command is intentionally stricter than plain restore. It runs the
public-OHLCV preflight first, then stops and replaces alive unhealthy
collectors only if their configured data source is reachable. Healthy live
collectors are still left unchanged.

When recovering from a known or suspected exchange-data outage, add the
read-only OHLCV guard:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --restore \
  --preflight-ohlcv \
  --restart-unhealthy \
  --ohlcv-preflight-probe-limit 400 \
  --ohlcv-preflight-attempts 3 \
  --ohlcv-preflight-attempt-delay-sec 2
```

With this flag, restore checks each dead collector's configured
`venue`/`symbol`/`signal_source` before launching it. If the public-OHLCV
source is unreachable, the campaign is reported as `preflight_blocked` and the
collector is not started, preserving daily attempts for a valid data window.
With `--restart-unhealthy`, the same preflight must pass before an alive
unhealthy collector is stopped and replaced. The default restore path does not
replace live processes.
The default probe limit is 400 rows because managed strategy-runner children
fall back to `max_bars=400` unless explicitly configured otherwise. This flag
is optional; plain `--restore` keeps the existing behavior.

To operate on one campaign:

```bash
./.venv/bin/python scripts/restore_paper_campaigns.py \
  --restore \
  --campaign ema_cross_default
```

The active laptop campaign list and launch parameters are in
`configs/paper_evidence_campaigns.laptop.json`. The full three-campaign local
manifest remains available at `configs/paper_evidence_campaigns.json` for
pre-migration or single-host operation. To override the shortcut:

```bash
PAPER_CAMPAIGN_CONFIG=configs/paper_evidence_campaigns.json \
  make status-paper-campaigns
```

## Market-Data Failure Behavior

Public-OHLCV campaigns fail closed when the configured market-data source is
unreachable:

- current collectors preflight the configured public-OHLCV source before
  consuming a daily campaign attempt;
- if the source is unreachable, status is `blocked` with
  `reason=ohlcv_source_unreachable`;
- the blocked record preserves the preflight payload and marks
  `retry_budget_consumed=false`;
- no campaign attempt starts while the source remains unreachable;
- a later successful preflight lets the next loop continue into the normal
  campaign path.

The canonical manifest sets `max_daily_attempts` to `2`, meaning one initial
attempt and one retry for strategy/campaign failures. Known source outages do
not consume that budget under current code. Status can still report
`running=true` while `ok=false` for campaign health. Process liveness is not
evidence validity.

If a pre-merge or manually started parent has already parked after exhausting
attempts, use guarded recovery (`make recover-paper-campaigns`) so it is
replaced only after the configured OHLCV source is reachable.
When that recovery preflight passes, the replacement launch preserves same-day
failure history but grants exactly one fresh same-day recovery attempt by
raising the launch attempt limit to `previous_daily_attempts + 1`. The command
reports this under `recovery_attempt_override`; it does not erase or rewrite
historical session evidence.

## Current Campaigns

| Campaign | Strategy | Signal source | Daily attempts | State directory |
|---|---|---|---|---|
| `es_daily_trend_v1` | `sma_200_trend` | `public_ohlcv_1d` | `2` | `.cbp_state` |
| `breakout_default` | `breakout_donchian` | `public_ohlcv_5m` | `2` | `.cbp_state_challengers/breakout_default_daily` |

Hetzner-owned campaign:

| Campaign | Strategy | Signal source | Daily attempts | State directory |
|---|---|---|---|---|
| `ema_cross_default` | `ema_cross` | `public_ohlcv_5m` | `2` | `.cbp_state_challengers/ema_cross_default_daily` |

## Safety Boundary

The repo does not automatically start these campaigns at OS login. That would
start financial background jobs without a current operator action. This
recovery command reduces the restart workflow to one explicit, idempotent
operation while retaining the collector's existing duplicate-process guard.

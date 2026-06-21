# Paper Campaign Recovery

Use this runbook after a laptop restart or any event that may have terminated
the detached paper evidence collectors.

## Status

Run:

```bash
make status-paper-campaigns
```

This is read-only. It checks the configured canonical and challenger state
directories and exits nonzero if any selected collector is not alive or is
reporting unhealthy campaign status.

For a single local check-in that combines laptop campaign health with the paper
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

This runs the existing remote read-only status command and formats the returned
JSON locally into a concise campaign-health summary. It does not start, stop,
or restore a campaign. The local formatter runs in strict mode, so malformed
remote JSON or `ok=false` campaign status exits non-zero after printing the
investigation recommendation.

Override the remote target or app directory only when the deployment record
changes:

```bash
HETZNER_SSH_TARGET=cryptkeep@100.86.128.9 \
HETZNER_APP_DIR=/srv/cryptkeep/app \
  make status-paper-hetzner
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

Public-OHLCV campaigns fail closed when the strategy runner observes no market
data for the full strategy window:

- campaign status is `failed`, not `completed`;
- the session end record sets `critical_error=true` and records
  `campaign_reason=no_public_ohlcv`;
- no leaderboard evidence cycle or decision record is generated for the
  failed window;
- the detached collector stays alive and retries once after its configured
  poll interval;
- after `max_daily_attempts` is exhausted, status remains failed until the next
  UTC day.

The canonical manifest sets `max_daily_attempts` to `2`, meaning one initial
attempt and one retry. Status can therefore report `running=true` for the
collector process while `ok=false` for campaign health. Process liveness is
not evidence validity. Restore does not replace an alive unhealthy collector;
the existing parent owns the bounded retry.

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

# Paper Campaign Recovery

Use this runbook after a laptop restart or any event that may have terminated
the detached paper evidence collectors.

## Status

Run:

```bash
make status-paper-campaigns
```

This is read-only. It checks the configured canonical and challenger state
directories and exits nonzero if any selected collector is not alive.

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

The authoritative campaign list and launch parameters are in
`configs/paper_evidence_campaigns.json`.

## Current Campaigns

| Campaign | Strategy | Signal source | State directory |
|---|---|---|---|
| `es_daily_trend_v1` | `sma_200_trend` | `public_ohlcv_1d` | `.cbp_state` |
| `ema_cross_default` | `ema_cross` | `public_ohlcv_5m` | `.cbp_state_challengers/ema_cross_default_daily` |
| `breakout_default` | `breakout_donchian` | `public_ohlcv_5m` | `.cbp_state_challengers/breakout_default_daily` |

## Safety Boundary

The repo does not automatically start these campaigns at OS login. That would
start financial background jobs without a current operator action. This
recovery command reduces the restart workflow to one explicit, idempotent
operation while retaining the collector's existing duplicate-process guard.

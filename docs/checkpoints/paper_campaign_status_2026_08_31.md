# Paper Campaign Status - 2026-08-31

Status: read-only operating checkpoint.

## Laptop Campaigns

Command:

`make status-paper-all`

The laptop section completed before the Hetzner sandbox failure.

SHOWN:

- Campaigns: `2/2 running`, `all_running=True`.
- `es_daily_trend_v1`: `idle`, `waiting_for_next_day`,
  strategy `sma_200_trend`, `fills=20`, `closed=10`, `pnl=31.4369`.
- `breakout_default`: `idle`, `waiting_for_next_day`,
  strategy `breakout_donchian`, `fills=23`, `closed=11`, `pnl=4.2183`.
- Canonical gate: `ready=False`, `machine_ready=False`,
  `manual_review_required=True`.
- Active gate progress: `3/5` provenance-qualified round trips,
  `2` remaining.
- Active gate days: `118/45` days recorded.
- Evidence writer: `status=ok`, `consecutive=0/3`, `total=0`.
- Qualification detail: `counted_fills=6/16`, `incomplete=0`,
  `rejected=0`, latest qualified close
  `2026-07-09T00:04:00.377830+00:00`.

## Gate Velocity

Command:

`make status-paper-gate-velocity`

SHOWN:

- Strategy: `es_daily_trend_v1`, target `sma_200_trend`.
- Policy: `slow_daily_single_symbol_v1`, `valid=True`.
- Round trips: `qualified=3`, `required=5`, `remaining=2`,
  `all_history=10`, `excluded_all_history=7`.
- Days threshold: `recorded=118`, `required=45`, `remaining=0`.
- Qualified bars threshold: `recorded=70`, `required=60`, `remaining=0`.
- Blocking threshold: `round_trips`.
- Observed cadence: `10.5` days per qualified round trip.
- Projected completion: `21` days remaining,
  `2026-09-21T05:54:47.809287+00:00`.
- Finding: `legacy_history_excluded`; seven all-history round trips remain
  diagnostic only because they do not satisfy the current provenance contract.

The overall `make status-paper-all` command exited non-zero because the
sandboxed Hetzner SSH check failed with `ssh_operation_not_permitted`. That
failure is an environment boundary, not evidence of a remote campaign failure.

## Hetzner Campaign

Command:

`./.venv/bin/python scripts/report_hetzner_paper_campaign_status.py --strict --ssh-target cryptkeep@100.86.128.9 --transport tailscale-ssh --app-dir /srv/cryptkeep/app --config configs/paper_evidence_campaigns.hetzner.example.json --timeout-sec 15`

Execution context: approved out-of-sandbox read-only Tailscale SSH status check.

SHOWN:

- Campaigns: `1/1 running`, `all_running=True`.
- `ema_cross_default`: `idle`, `waiting_for_next_day`,
  strategy `ema_cross`, `fills=16`, `closed=8`, `pnl=-2.3183`.
- Latest fill: `2026-08-29T00:02:44.159494+00:00`.
- Summary: paper evidence collector is idle; `ema_cross_default` already
  recorded session evidence for `2026-08-31`, waiting for next UTC day.
- Recommendation: `continue_paper_observation`.

## Interpretation

No service restart, campaign restart, package install, deploy, or config change
was performed.

The active paper-evidence state remains observation, not live launch:

- Laptop campaigns are running and waiting for their next scheduled daily
  opportunity.
- Hetzner `ema_cross_default` is running and waiting for the next UTC day.
- Canonical `es_daily_trend_v1` still needs `2` additional
  provenance-qualified round trips under the active gate policy.
- Under current observed velocity, the projected completion date is
  `2026-09-21T05:54:47.809287+00:00`.

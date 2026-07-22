# Strategy Review Artifact - 2026-07-21

Status: advisory review artifact

## Scope

This is the dated weekly strategy-review artifact for the current paper
campaign state. It records read-only status and loss-replay output only. It
does not change strategy configuration, promotion gates, campaign manifests, or
trading behavior.

## Commands

```bash
make strategy-review
./.venv/bin/python scripts/dev/replay_paper_losses.py --strategy-id sma_200_trend --symbol BTC/USDT --limit 10
```

The first command was rerun out of the sandbox because the sandboxed Tailscale
CLI returned `tailscale_cli_preferences_unavailable` for the Hetzner status
wrapper. The out-of-sandbox command completed successfully and remained
read-only.

## Campaign Health

Laptop paper campaigns:

- `es_daily_trend_v1`: running, `idle`, `waiting_for_next_day`,
  `fills=20`, `closed=10`, `pnl=31.4369`.
- `breakout_default`: running, `idle`, `waiting_for_next_day`,
  `fills=13`, `closed=6`, `pnl=-4.1601`.

Hetzner paper campaign:

- `ema_cross_default`: running, `idle`, `waiting_for_next_day`,
  `fills=9`, `closed=4`, `pnl=-2.3157`.
- Latest Hetzner fill: `2026-07-21T00:05:06.659382+00:00`.

## Paper Gate

`es_daily_trend_v1` remains blocked:

- Qualified round trips: `3/10`; `7` remaining.
- Days recorded: `77/30`.
- Paper history: `qualified_closed=3`, `all_history_closed=10`.
- Evidence writer: `status=ok`, `consecutive=0/3`, `total=0`.
- Manual strategy review remains required before any paper promotion.

Rejected evidence is still legacy provenance failure, not a new runtime
failure: `9/16` JSONL fills lack or mismatch required provenance fields, and
`1` qualified fill is not part of a complete qualified round trip.

## Current ES Signal

The diagnostic runner status reported:

- `strategy_id=sma_200_trend`
- `strategy_preset=es_daily_trend_v1`
- `signal_source=public_ohlcv_1d`
- `signal_action=buy`
- `signal_reason=sma200:long:regime:borderline`
- `bars=300`
- `status=stopped`

This is diagnostic only; it does not imply promotion readiness.

## Loss Replay

The default `make strategy-review` invocation used `BTC/USD` before this
checkpoint and returned zero replay fills for `sma_200_trend`. That was a
workflow-default mismatch: the canonical ES paper campaign and journal use
`BTC/USDT`.

The corrected command with `BTC/USDT` returned:

- `fills_count=20`
- `closed_trade_count=10`
- `losing_trade_count=9`
- `net_realized_pnl=31.4368625683357`
- `total_fees=1.0572144791643752`
- `expectancy_return_pct=8.49065180506847`

Interpretation note: `loss_replay.losing_trade_count` is net-of-fees and found
`9` net-negative closed trades. The embedded journal summary reports
`wins=2` and `losses=8`; that summary is gross-PnL classified, so one
gross-positive trade is net-negative after fees. Do not compare those two
counts without the gross-vs-net distinction.

## Decision

Continue paper observation. Do not promote, widen, retune, or change the
strategy config based on this artifact. The binding paper gate is still
qualified evidence count plus manual review after gate readiness.

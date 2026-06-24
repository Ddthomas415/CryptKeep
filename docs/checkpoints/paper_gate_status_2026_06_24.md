# Paper Gate Status - 2026-06-24

Status: ACCEPTED

## Scope

Read-only status snapshot for the laptop-owned paper campaigns and canonical
`es_daily_trend_v1` paper gate.

This checkpoint does not change strategy selection, paper execution,
promotion gates, campaign ownership, Hetzner state, or live behavior.

## Evidence

Command:

```bash
make status-paper-soak
```

SHOWN:
- `Campaigns: 2/2 running (all_running=True)`.
- `es_daily_trend_v1` was idle with `reason=waiting_for_next_day`,
  `strategy=sma_200_trend`, `fills=18`, `closed=9`, and `pnl=32.1776`.
- `breakout_default` was idle with `reason=waiting_for_next_day`,
  `strategy=breakout_donchian`, `fills=9`, `closed=4`, and `pnl=-2.2281`.
- Gate `ready=False`.
- Gate `machine_ready=False`.
- Gate `manual_review_required=True`.
- Canonical provenance-qualified round trips were `2/10`, with `8`
  remaining.
- Days were `50/30`, with `0` remaining.
- Raw all-history reported `9` closed trades, but `7` of those were
  diagnostic-only all-history round trips.
- `9/14` JSONL fills lacked or mismatched required provenance.
- `1` qualified JSONL fill was not part of a complete qualified round trip.
- Expectancy remained insufficient for calculation.

UNVERIFIED:
- Hetzner-owned `ema_cross_default` status was not checked by this command.
  Use `make status-paper-hetzner` or `make status-paper-all` when remote status
  is intentionally needed.

## Interpretation

The campaign is running, but the actionable promotion count is the
provenance-qualified count, not raw all-history closed trades.

Current blocker:
- `es_daily_trend_v1` needs `8` more provenance-qualified round trips before
  the machine paper gate can clear.

Manual review remains required even after the count clears because observed win
rate and average winning/losing trade metrics must satisfy configured backtest
expectations before paper promotion.

# Paper Gate Status - 2026-06-21

Status: `ACCEPTED`

This checkpoint records the June 21, 2026 read-only paper campaign and
promotion-gate state after the accepted laptop/Hetzner campaign ownership
split. It does not change gate policy, campaign state, collector ownership,
Hetzner deployment state, or strategy evidence.

## Commands

```bash
git status --short --branch
git rev-parse HEAD origin/master origin/review-stabilized
make status-paper-campaigns
./.venv/bin/python scripts/check_promotion_gates.py --json
./.venv/bin/python -c 'from services.control.paper_promotion_progress import load_paper_promotion_progress; ...'
tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/restore_paper_campaigns.py --config configs/paper_evidence_campaigns.hetzner.example.json --status'
```

## Repository State

SHOWN:
- Branch: `review-stabilized`.
- Local branch status: synced with `origin/review-stabilized`.
- `HEAD`, `origin/master`, and `origin/review-stabilized` were all
  `7f884c0f7b251b07a8884614d963e922a0493a96`.
- No working-tree changes existed before this checkpoint was written.

## Laptop Campaign Health

SHOWN:
- `make status-paper-campaigns` used
  `configs/paper_evidence_campaigns.laptop.json`.
- `make status-paper-campaigns` returned `ok=true`.
- `make status-paper-campaigns` returned `all_running=true`.
- `campaign_count=2`.
- `running_count=2`.

| Campaign | Strategy | State | PID | Last completed day | Current reason |
|---|---|---:|---:|---|---|
| `es_daily_trend_v1` | `sma_200_trend` | running and idle | `80255` | `2026-06-21` | `waiting_for_next_day` |
| `breakout_default` | `breakout_donchian` | running and idle | `80263` | `2026-06-21` | `waiting_for_next_day` |

Interpretation:
- Laptop-owned paper campaigns are healthy.
- `ema_cross_default` is intentionally not part of the laptop shortcut because
  it is owned by the Hetzner host after the accepted isolated migration proof.

## Hetzner EMA Check

UNVERIFIED in this checkpoint:
- The Hetzner `ema_cross_default` status command was attempted.
- Tailscale required an additional browser authentication check and returned:
  `https://login.tailscale.com/a/l5442b51326264`.
- The command was interrupted instead of waiting on remote authentication.

Interpretation:
- This checkpoint does not disprove Hetzner health.
- It also does not reverify Hetzner health. A later operator check should run:

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/restore_paper_campaigns.py --config configs/paper_evidence_campaigns.hetzner.example.json --status'
```

## Canonical Strategy Gate

SHOWN:
- Strategy: `es_daily_trend_v1`.
- Stage: `paper`.
- `ready=false`.
- `machine_ready=false`.
- `manual_review_required=true`.
- Calendar-day gate passes with `47/30 days recorded`.
- Round-trip gate fails with `1/10` qualified round trips and `9 remaining`.
- Expectancy gate is `unknown` because there are insufficient qualified
  paper-history fills for calculation.

## Raw History vs Qualified Evidence

SHOWN:
- Raw `trade_journal_sqlite` all-history reports `17` fills and `8` closed
  trades for `sma_200_trend`.
- Promotion-gate source is `jsonl_provenance+trade_journal_sqlite`, not raw
  journal history alone.
- Qualified paper-history reports `2` fills and `1` closed trade.
- The gate reports `7` diagnostic-only all-history round trips.
- The gate reports `9/13` JSONL fills lack or mismatch required provenance.
- The gate reports `2` provenance-qualified evidence fills are not part of a
  complete qualified round trip.
- The qualified fill window is `2026-05-26T00:00:09.788947+00:00` to
  `2026-06-21T00:04:06.326871+00:00`.
- The only completed qualified round-trip close timestamp remains
  `2026-06-18T00:04:00.986914+00:00`.
- Unqualified fill dates are `2026-04-20:6`, `2026-05-15:2`, and
  `2026-05-18:1`.

Interpretation:
- Raw history is useful diagnostic context.
- Promotion readiness is blocked by provenance-qualified round trips.
- The current actionable paper-gate counter is `1/10`, not raw `8/10`.
- The new June 21 fill increased all-history fills and incomplete qualified
  evidence, but did not complete a second qualified round trip.

## Manual Review State

SHOWN:
- The daily loss halt simulation is machine-checked and passing.
- The regime-filter blocked-entry check is machine-checked and passing.
- The remaining manual-review blocker is the observed win-rate and average
  winning/losing trade returns versus the accepted backtest baseline.

SHOWN observed qualified metrics:
- `closed_trades=1`.
- `fills=2`.
- `win_rate=0.0`.
- `avg_win_return_pct=null`.
- `avg_loss_return_pct=-2.9003925324454785`.
- `expectancy_return_pct=-2.9003925324454785`.
- `net_realized_pnl=-1.9245102228412403`.

## Current Operational Conclusion

SHOWN:
- Laptop campaign collection is healthy.
- The canonical paper gate is blocked by insufficient provenance-qualified
  closed round trips and by performance comparison against the accepted
  baseline.
- More raw legacy trades will not move the gate unless they carry the required
  non-sample public-OHLCV provenance on entry and exit.

Next action:
- Continue running laptop-owned collectors.
- Re-authenticate Tailscale and rerun the Hetzner EMA status command to refresh
  remote ownership health.
- Do not migrate canonical `.cbp_state` to Hetzner until a separate canonical
  migration plan is reviewed and accepted.

Risk:
- MEDIUM: read-only checkpoint for a high-risk promotion/evidence path.
- No runtime or policy change was made.

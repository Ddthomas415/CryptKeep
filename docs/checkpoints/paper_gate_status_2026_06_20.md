# Paper Gate Status - 2026-06-20

Status: `READ_ONLY_CHECKPOINT`

This checkpoint records the June 20, 2026 read-only paper campaign and
promotion-gate state. It does not change gate policy, campaign state, collector
ownership, Hetzner deployment state, or strategy evidence.

## Commands

```bash
git status --short --branch
./.venv/bin/python scripts/restore_paper_campaigns.py --status
./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
CBP_STATE_DIR="$PWD/.cbp_state_challengers/ema_cross_default_daily" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
CBP_STATE_DIR="$PWD/.cbp_state_challengers/breakout_default_daily" \
  ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status
./.venv/bin/python scripts/check_promotion_gates.py --json
```

## Repository State

SHOWN:
- Branch: `review-stabilized`.
- Local branch status: synced with `origin/review-stabilized`.
- No working-tree changes existed before this checkpoint was written.

## Campaign Health

SHOWN:

| Campaign | Strategy | State | PID | Last completed day | Current reason |
|---|---|---:|---:|---|---|
| `es_daily_trend_v1` | `sma_200_trend` | running and idle | `80255` | `2026-06-20` | `waiting_for_next_day` |
| `ema_cross_default` | `ema_cross` | running and idle | `80259` | `2026-06-20` | `waiting_for_next_day` |
| `breakout_default` | `breakout_donchian` | running and idle | `80263` | `2026-06-20` | `waiting_for_next_day` |

SHOWN:
- `restore_paper_campaigns.py --status` returned `ok=true`.
- `restore_paper_campaigns.py --status` returned `all_running=true`.
- `restore_paper_campaigns.py --status` returned `campaign_count=3` and
  `running_count=3`.
- Each configured collector had already recorded the `2026-06-20` UTC evidence
  session and was waiting for the next UTC day.

## Canonical Strategy Gate

SHOWN:
- Strategy: `es_daily_trend_v1`.
- Stage: `paper`.
- `ready=false`.
- `machine_ready=false`.
- `manual_review_required=true`.
- Calendar-day gate passes with `46/30 days recorded`.
- Round-trip gate fails with `1/10` qualified round trips and `9 remaining`.
- Expectancy gate is `unknown` because there are insufficient qualified
  paper-history fills for calculation.

## Raw History vs Qualified Evidence

SHOWN:
- Raw `trade_journal_sqlite` all-history reports `16` fills and `8` closed
  trades for `sma_200_trend`.
- Promotion-gate source is `jsonl_provenance+trade_journal_sqlite`, not raw
  journal history alone.
- Qualified paper-history reports `2` fills and `1` closed trade.
- The gate reports `7` diagnostic-only all-history round trips.
- The gate reports `9/12` JSONL fills lack or mismatch required provenance.
- The gate reports `1` qualified JSONL fill is not part of a complete qualified
  round trip.
- Unqualified fill dates are `2026-04-20:6`, `2026-05-15:2`, and
  `2026-05-18:1`.

Interpretation:
- Raw history is useful diagnostic context.
- Promotion readiness is blocked by provenance-qualified round trips.
- The current actionable paper-gate counter is `1/10`, not raw `8/10`.

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
- Local campaign collection is healthy.
- The paper gate is blocked by insufficient provenance-qualified closed round
  trips and by performance comparison against the accepted baseline.
- More raw legacy trades will not move the gate unless they carry the required
  non-sample public-OHLCV provenance on entry and exit.

Next action:
- Continue running the local collectors unless explicitly executing the
  accepted Hetzner isolated challenger proof.
- If executing the Hetzner proof, use
  `docs/deployment_records/hetzner_isolated_challenger_proof_TEMPLATE.md` and
  preserve single-owner evidence before state transfer.
- Do not migrate canonical `.cbp_state` to Hetzner until the isolated
  challenger proof, first server-hosted UTC cycle, and backup restore rehearsal
  are accepted.

Risk:
- MEDIUM: read-only checkpoint for a high-risk promotion/evidence path.
- No runtime or policy change was made.

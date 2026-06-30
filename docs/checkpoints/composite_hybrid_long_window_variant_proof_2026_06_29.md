# Composite Hybrid Long Window Variant Proof - 2026-06-29

## Scope

Active role: ENGINEER

Objective:
- Add two additional research-only synthetic evidence windows for the accepted
  `composite_hybrid_v1_breakout_sma200_research` candidate.
- Keep the candidate out of paper, runtime strategy registry, promotion
  behavior, and order routing.

## Reason

The accepted long-window proof in
`docs/checkpoints/composite_hybrid_long_window_research_proof_2026_06_27.md`
showed the composite candidate can participate when the 200-SMA confirmer has
enough bars, but it only produced realized participation in one synthetic
window.

SHOWN:
- The active backlog requires comparison evidence across at least three
  realized synthetic windows before any paper decision is revisited.
- `sma_200_trend` needs enough history for its 200-SMA confirmer path.
- The current composite remains research-only and unregistered from runtime
  dispatch.

Implementation consequence:
- Add more long-window synthetic variants to the research evidence pack.
- Do not add a paper campaign or production path.

## Code Change

Changed:
- `services/backtest/evidence_cycle.py`
- `services/backtest/evidence_windows.py`
- `tests/test_backtest_evidence_cycle.py`

Added windows:
- `long_trend_breakout_retest`
  - bars: `332`
  - warmup bars: `20`
  - pattern: long 200-SMA warmup, breakout acceleration, sharp retest
- `long_trend_failed_extension`
  - bars: `334`
  - warmup bars: `20`
  - pattern: long trend, final upside extension, failed continuation

The existing `long_trend_confirmation` window remains in place. The three long
windows now provide the minimum realized synthetic-window coverage for the
current composite definition.

## Verification

Targeted tests:

```bash
./.venv/bin/python -m pytest -q tests/test_backtest_evidence_cycle.py tests/test_backtest_leaderboard.py tests/test_composite_hybrid_parity.py
```

SHOWN:
- `26 passed in 5.07s`

Read-only aggregate comparison command:

```bash
./.venv/bin/python -c 'from services.backtest.evidence_cycle import run_strategy_evidence_cycle; from services.backtest.leaderboard import COMPOSITE_HYBRID_RESEARCH_CANDIDATE; out=run_strategy_evidence_cycle(base_cfg={}, symbol="BTC/USDT", initial_cash=10000, fee_bps=10, slippage_bps=5); row=next(r for r in out["aggregate_leaderboard"]["rows"] if r["candidate"]==COMPOSITE_HYBRID_RESEARCH_CANDIDATE); print({k: row[k] for k in ("rank","decision","evidence_status","confidence_label","avg_return_pct","max_drawdown_pct","closed_trades","closed_trade_window_count","active_window_count")}); print(row["research_acceptance"])'
```

SHOWN:
- `rank=2`
- `decision=improve`
- `evidence_status=synthetic_only`
- `confidence_label=low`
- `avg_return_pct=5.007706036335235`
- `max_drawdown_pct=8.66715642593119`
- `closed_trades=3`
- `closed_trade_window_count=3`
- `active_window_count=3`
- `research_acceptance.accepted=false`

## Interpretation

SHOWN:
- The current composite candidate now has realized synthetic participation
  across three windows.
- The candidate still has no attributed persisted paper history.
- The candidate remains `synthetic_only`, `low` confidence, and not research
  accepted.

Recommendation:
- Do not start a persistent composite paper campaign yet.
- Use this as accepted implementation proof that the synthetic participation
  floor is now met.
- Keep paper advancement blocked until a separate accepted decision explicitly
  changes the research acceptance requirement or starts a scoped paper proof.

## Acceptance State

Risk: HIGH

Reason:
- This changes financial strategy research evidence and can affect future
  candidate ranking and campaign selection.

Acceptance state: ACCEPTED

Acceptance reference: independently reviewed and accepted by the human operator
on 2026-06-29 after PR #143 was opened for review.

# Composite Hybrid Long Window Research Proof - 2026-06-27

## Scope

Active role: ENGINEER

Objective:
- Add one research-only synthetic evidence window long enough for the accepted
  `composite_hybrid_v1_breakout_sma200_research` candidate to exercise its
  `sma_200_trend` confirmer.
- Do not add a paper campaign, runtime registry entry, promotion behavior, or
  order-routing path.

## Reason

The accepted comparison checkpoint
`docs/checkpoints/composite_hybrid_leaderboard_comparison_2026_06_27.md`
showed zero realized participation for the current composite candidate.

SHOWN:
- The default evidence windows had `104` to `180` bars.
- `sma_200_trend` needs `200` bars for SMA history.
- `sma_200_trend` also needs enough ATR/regime history before entry can be
  allowed.

Implementation consequence:
- A fair comparison window needs more than `200` bars.
- The added window uses `320` bars so the 200-SMA confirmer can warm up, emit a
  confirmed entry, and then observe an exit.

## Code Change

Changed:
- `services/backtest/evidence_cycle.py`
- `services/backtest/evidence_windows.py`
- `tests/test_backtest_evidence_cycle.py`

Added window:
- `window_id`: `long_trend_confirmation`
- bars: `320`
- warmup bars: `20`
- pattern: long trend, breakout pulse, sharp reversal, shallow recovery

The duplicated default-window definitions were updated together so
`evidence_cycle` and `evidence_windows` stay aligned.

## Verification

Targeted tests:

```bash
python3 -m pytest -q tests/test_backtest_evidence_cycle.py tests/test_backtest_leaderboard.py tests/test_composite_hybrid_parity.py
```

SHOWN:
- `26 passed in 1.86s`

Static checks:

```bash
python3 -m py_compile services/backtest/evidence_cycle.py services/backtest/evidence_windows.py tests/test_backtest_evidence_cycle.py
git diff --check
```

SHOWN:
- both passed

Read-only comparison artifact:

- `/private/tmp/composite_hybrid_leaderboard_comparison_long_window_20260627.json`

SHOWN:
- `ok=true`
- `window_count=9`
- `candidate_count=10`
- as_of: `2026-06-28T00:06:51Z`

## New Aggregate Result

| Rank | Candidate | Strategy | Decision | Evidence | Score | Net Return After Costs | Max DD | Closed Trades |
|---:|---|---|---|---|---:|---:|---:|---:|
| 1 | `breakout_default` | `breakout_donchian` | `improve` | `synthetic_only` | `0.714335` | `24.5059%` | `8.4781%` | `6` |
| 2 | `ema_cross_default` | `ema_cross` | `improve` | `synthetic_only` | `0.548599` | `6.0679%` | `6.2510%` | `2` |
| 3 | `composite_hybrid_v1_breakout_sma200_research` | `composite_hybrid_v1` | `freeze` | `synthetic_only` | `0.415494` | `2.0568%` | `6.4690%` | `1` |
| 4 | `sma_200_trend_default` | `sma_200_trend` | `retire` | `paper_supported` | `0.302440` | `-0.0394%` | `21.3578%` | `1` |
| 5 | `momentum_default` | `momentum` | `retire` | `synthetic_only` | `0.169321` | `-3.3531%` | `31.0268%` | `15` |

## Composite Row Detail

SHOWN:
- Rank: `3/10`
- Decision: `freeze`
- Evidence status: `synthetic_only`
- Confidence: `low`
- Leaderboard score: `0.415494`
- Net return after costs: `2.0568%`
- Slippage sensitivity: `0.0263%`
- Max drawdown: `6.4690%`
- Closed trades: `1`
- Closed-trade window count: `1`
- Active window count: `1`

Research acceptance:
- accepted: `false`
- status: `not_accepted`

Remaining blockers:
- Persisted paper history only has `0` closed trades; research floor requires
  `30`.
- Only `1` represented window produced realized closed trades; research floor
  requires `3`.
- Evidence status is `synthetic_only`; research floor requires
  `paper_supported`.
- Confidence is `low`; research floor requires at least `medium`.

## Interpretation

SHOWN:
- The long window fixes the original mechanical participation problem: the
  composite candidate now produces a closed synthetic round trip.
- The candidate is still not accepted for paper because its evidence is
  synthetic-only, low confidence, and represented in only one realized window.

Recommendation:
- Keep `composite_hybrid_v1_breakout_sma200_research` research-only.
- Do not start a persistent paper campaign.
- If this path continues, add more long-window variants so the candidate can be
  tested across at least three realized synthetic windows before any paper
  decision is revisited.

This proof was independently reviewed and accepted by the human operator on
2026-06-28 after PR #126 checks passed. The accepted conclusion is that the
long-window proof fixes the mechanical warmup/participation gap, but the
candidate remains blocked from paper.

## Acceptance State

Risk: HIGH

Reason:
- This changes financial strategy research evidence and can affect future
  candidate ranking.

Acceptance state: ACCEPTED

Acceptance reference: independently reviewed and accepted by the human operator
on 2026-06-28 after PR #126 checks passed.

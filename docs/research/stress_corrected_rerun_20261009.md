# BTC+ETH stress test rerun under the corrected contract - 2026-10-09

Research only. Original stress test, JSON, verdict and workbook unchanged. Closes the last item-8 gap.
Output `research/research_corrections_20261009/stress_corrected_v1.json` (core + grid parts, same script hash
1f98513a...5907, shared math d07ae717..., original source and both input hashes checked before merge).
Script `scripts/research/rerun_frozen_stress.py`; tests `tests/test_rerun_frozen_stress.py` (2 passed).
Change: decisions at a close execute at the next day's open via shared rebalance(); every registered rule kept,
including the study's own 1.2% primary cost. Stored rows are [time, open, high, low, close, volume] (verified).

## Result: verdict unchanged - REJECT

| Check (registered 1.2% cost) | Original | Corrected |
|---|---|---|
| Required 1 (beat BTC and fixed mix on drop and Sharpe, 2 of 3 periods incl. A) | fail (B only) | fail (B only) |
| Required 2 (>= 10 of 13 variants beat fixed mix, full period) | 5 of 13 | 5 of 13 |
| Grid share beating fixed mix (105 settings) | 43.8% | 43.8% |
| 8-week block bootstrap of Sharpe difference, 90% range | -0.22 to +0.41 | -0.22 to +0.41 |
| Full period, rule / fixed mix / hold BTC | $50,217 / $21,265 / $133,297 | $50,448 / $21,275 / $133,390 |

Cross-check against an independent implementation: at 0.50% the corrected rule's periods B and C end at $9,919.59
and $1,779.58, identical to the separately written `majors_next_open_v2.json` (A differs only because this study's
A starts 2016-08-01, not 2016-07-01). Next-open execution changes Coinbase daily results by well under 1%.

Status: READY_FOR_INDEPENDENT_REVIEW.

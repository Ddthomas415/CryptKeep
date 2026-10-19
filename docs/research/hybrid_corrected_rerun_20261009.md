# Binance research strategies (hybrid.py) rerun under the corrected contract - 2026-10-09

Research only. Not promotion evidence; not a holdout. Originals unchanged. Closes the hybrid.py gap in checklist item 8.
Output `research/research_corrections_20261009/hybrid_corrected_v1.json`: 96 results (12 strategies x 4 fees x
strict/outage) merged from 4 parts with identical script (40becc58...38d2), shared-math, source and 484-input hashes.
Script `scripts/research/rerun_frozen_hybrid.py`; tests `tests/test_rerun_frozen_hybrid.py` (7 passed).

## Contract

Frozen: all 12 strategies (no selection), weight rules executed from the hashed original, weekly Sunday decisions,
continuous run from 2020-01-01, TRAIN 2020-23 / TEST 2024-01-01..2026-10-08, 0.05% slippage, current-listed universe
(survivorship limitation unchanged). Corrected: execution at Monday's open via shared rebalance(); no 0% return for
missing candles (strict INCOMPLETE; outage NAV unknown); fees 0.50% primary, 0.10% original, 0.60/1.20% stress.

Correction made during this work, recorded: the first primary run showed LUNAUSDT's candles stop at 0.00005 on
2022-05-13 and resume 2022-05-31 at 1.0 as a different asset (Terra 2.0). An identity-break guard (>100x across a
gap stops the run) was added; the pre-guard part is preserved in `_superseded_hybrid_parts_pre_identity_guard/`.
The original hybrid.py also carried the same symbol across that switch (missing returns set to 0, then the new
coin's returns), so its four affected results inherit that flaw.

## Results, TEST 2024-01-01..2026-10-08 (continuous account from 2020; marked balances, not realized profit)

| Strategy | Original test % (0.6% fee) | Corrected test % (0.6%) | Corrected at 0.5%: status, marked end | Sharpe vs BTC, 90% block range (0.5%) | Corrected test % at 0.1% |
|---|---:|---:|---|---|---:|
| BTC hold | +93.3 | +93.3 | complete, $11,291 | - | +93.3 |
| Trend each coin, vol-scaled, 28d | +5.1 | +5.1 | complete, $3,536 | -0.51 [-1.17, 0.15] | +20.2 |
| Hybrid momentum+trend, BTC filter, vol-scaled, 28d | -4.4 | -4.4 | complete, $3,155 | -0.64 [-1.58, 0.37] | +9.8 |
| Trend each coin, 28d | -40.5 | -40.5 | complete, $4,812 | -0.92 [-1.62, -0.27] | -25.0 |
| Hybrid ... 90d | -29.9 | -29.9 | complete, $1,980 | -1.09 [-1.97, -0.12] | -19.7 |
| Top-5 momentum + BTC filter, 28d | -72.7 | -72.7 | complete, $2,182 | -0.96 [-1.87, 0.11] | -60.1 |
| Top-5 momentum + BTC filter, 90d | -85.9 | -85.8 | complete, $845 | -1.34 [-2.19, -0.25] | -80.2 |
| Top-5 momentum, 28d | -97.0 | -97.0 | complete, $125 | -1.64 [-2.45, -0.86] | -94.4 |
| Equal-weight top 20 | -72.3 | n/a | INCOMPLETE 2022-05-14 (LUNA) | - | n/a |
| Trend each coin, 90d | -50.0 | n/a | INCOMPLETE 2022-05-14 (LUNA) | - | n/a |
| Trend each coin, vol-scaled, 90d | -1.2 | n/a | INCOMPLETE 2022-05-14 (LUNA) | - | n/a |
| Top-5 momentum, 90d | -98.2 | n/a | INCOMPLETE 2022-05-14 (LUNA) | - | n/a |

Outage mode cannot rescue the four LUNA cases: each stops at the identity break (2022-06-06 or 2022-09-12).

## Reading

- Next-open execution changes nothing material here: Binance daily opens equal the prior close to within rounding.
  The material corrections are data validity: four strategies have no valid full-period result.
- The two variants positive at the 0.1% fee stay positive (+20.2%, +9.8%) and turn about flat or negative at
  0.5-0.6%. All trail BTC's +93.3%. Their Sharpe-difference ranges vs BTC include zero, so underperformance is
  likely but not established for those two; five others have ranges entirely below zero.
- "Test" here is the second half of one continuous account, previously studied: not fresh holdout evidence.

Status: READY_FOR_INDEPENDENT_REVIEW. No economic acceptance or promotion claim.

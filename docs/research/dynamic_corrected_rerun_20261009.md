# Coinbase dynamic-universe simulation rerun under the corrected execution contract - 2026-10-09

Research only. Not promotion evidence; not a holdout (data previously studied). Originals unchanged.
Output: `research/research_corrections_20261009/dynamic_corrected_v1.json`: 96 results merged from 20 part files,
one script hash (d31871fb...2712), shared math d07ae717...9047, 775 hashed input files (cb/h1, cb2/h1).
Script `scripts/research/rerun_frozen_dynamic.py`; tests `tests/test_rerun_frozen_dynamic.py` (8 passed).
Parts from an earlier script hash (3fc1c7f7...) were moved, not deleted, to `_superseded_dynamic_parts_hash_3fc1c7f7/`
after fee/mode arguments were added to fit the laptop's per-call time limit; every reported part was rerun.

## Contract

Frozen: all 8 original strategies (no selection) and their decision logic, run from the hashed original
source on its own forward-filled closes, 10 bps slippage, both original windows.
Corrected: fills at the open of the decision hour's bar instead of the last completed close; no fill without a
bar; held coins never valued or sold at forward-filled prices (strict = INCOMPLETE; outage = keep, NAV unknown,
sale deferred to next observed open). Fees 0.50% primary, 0.60% / 1.20% stress.

## Results, $1,000 start, 0.50% fee

| Strategy | Last 60 days (strict = outage) | Prior 10 months, outage | Prior 10 months, strict stop |
|---|---:|---:|---|
| Hold BTC | $1,292 | $582 | 2025-10-25 16:00 |
| Hold ETH | $1,312 | $476 | 2025-10-25 16:00 |
| Rotation 7d top-1 daily | $304 | $0.00 | 2025-10-25 16:00 |
| Rotation 7d top-3 daily | $1,146 | $1.78 | 2025-10-25 16:00 |
| Rotation 24h top-3 daily | $579 | $1.86 | 2025-10-25 16:00 |
| Rotation 7d top-3 weekly | $558 | $15.27 | 2025-10-25 16:00 |
| Breakout 15% trail | $1,566 | $126.88 | 2026-05-08 02:00 |
| Breakout 8% trail | $1,025 | $270.44 | 2026-05-08 02:00 |

- Corrections barely move these results: hourly next-open vs last close differ little. Same-fee (0.60%) comparison with
  the originals: 60 days breakout-15 $1,544.39 -> $1,542.22, top-1 rotation $280.76 -> $291.92;
  10 months breakout-15 $116.81 -> $116.60, top-1 rotation $0.00 -> $0.00. No verdict changes.
- 2025-10-25 16:00 UTC has no Coinbase bar for any product, BTC included (exchange-wide gap): every strategy holding
  anything then stops in strict mode. 2026-05-08 02:00 is the same gap the breakout portfolio diagnostic found.
  The outage runs carry 5-21 unknown-NAV hours; no prices were invented.
- Last-60-day breakout-15 still depends on one trade (USELESS +150%). It made no DIMO or RLC trades.
- Paired 56-day block Sharpe vs BTC (prior 10 months, outage, 0.50%): breakout-15 -1.26 [-4.08, 0.97],
  breakout-8 -1.30 [-3.63, 1.93], rotations -0.75 to -1.68, every interval including zero, even for runs
  that lost ~100%. With ~300 daily returns this test has little power here; the dollar outcomes are the clearer
  evidence. Weekly rotation: INCOMPLETE (unknown day-end NAV). Last 60 days: not computable (< 113 days), as preregistered.

Status: READY_FOR_INDEPENDENT_REVIEW. No economic acceptance, promotion or holdout claim.

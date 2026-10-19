# Short-hold top-gainer study rerun under the corrected contract - 2026-10-09

Research only. Not promotion evidence; not a holdout. Originals unchanged. Closes the short_hold gap in item 8.
Output `research/research_corrections_20261009/short_hold_corrected_v1.json`: 168 results (14 strategies x 2 windows x
3 fees x strict/outage) merged from 12 parts with one script hash (dcaf8a81...5980) and the original source hash
(0c68bf1c...9ffa). Script `scripts/research/rerun_frozen_short_hold.py`; tests `tests/test_rerun_frozen_short_hold.py` (5 passed).
Contract as written in the script header (decision on frozen marks, fill at next hourly open, no forward-filled
prices, strict/outage). Fees 0 (deciding check), 0.50% primary, 1.20% stress, plus 10 bps slippage.

## Results ($1,000 start, outage mode unless noted; marked balances)

Last 60 days (2026-08-10..10-09):
- Zero fees: 13 of 14 lose; top-3 by 24 h gain held 12 h ends $1,352 (original $1,379). Mean trade +0.95%.
- 0.50% fees: all 14 lose ($0 to $737). 1.20%: all lose ($0 to $319).
- Corrections move zero-fee results little except the 4 h take-profit/stop variant ($873 -> $641) and the
  1 h/1 h rotation, whose strict run stops at a BASECAT-USD missing bar (2026-09-14 11:00).

Prior 10 months (2025-10-09..2026-08-10):
- All 14 strict runs stop at the exchange-wide 2025-10-25 16:00 gap; outage runs (10-12 unknown-NAV hours) end at
  $0 to $21 at zero fees and $0 to $2 at 0.50%.

## Correction to earlier summaries

The research summary said short holds "lost at every hold length, even with zero fees". That is wrong for one
variant: top-3 by 24 h gain held 12 h was positive at zero fees in the last 60 days in the ORIGINAL output too
($1,379) and remains so corrected ($1,352). The conclusion that matters is unchanged: at the 0.50% observed fee
every version loses in both windows. One positive zero-fee variant out of 28 window/strategy cells is consistent
with chance and does not survive costs.

`fwd.py` (no-cost forward-return event study on the same signal) is not rerun: it reports no portfolio or cost
result, and its question is answered by the zero-fee rows above.

Status: READY_FOR_INDEPENDENT_REVIEW.

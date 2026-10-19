# Top gainer -> pullback -> green study

Fixed before the download completed: 182 completed UTC days, current eligible
Coinbase USD universe from the saved 15:02 UTC paginated snapshot. Rank daily
close-to-close returns among available markets. Record every daily leader event.
After leadership, follow the running closing-price peak for up to 30 days.
Test 10% and 20% closing-price drawdowns separately. Buy at next day's open.
Exit after the first positive daily close-to-close return, at the next open;
otherwise exit at 30 days. Keep terminal open, missing and pending events.
Gross exit return is measured from the actual modeled entry, not the rolling
return label. No future full-window requirement controls entry admission.

Assumptions: daily close returns approximate a fixed-time 24-hour leaderboard;
today's eligible universe substitutes for unavailable historical listing flags.
If false, reconstructed leaders differ from actual historical live leaders.
These are event studies with overlap, not a reinvested portfolio or holdout.
No private APIs, orders, new scheduled jobs or campaign changes.

Raw responses are preserved in research/coinbase_leader_daily_raw_20261012.json;
analysis output planned at research/coinbase_leader_pullbacks_20261012.json.
Three targeted tests passed: loss despite green, gap retention, unfinished
position retention, and independence from a gap after an already completed exit.
Financial interpretation requires separate review. READY_FOR_INDEPENDENT_REVIEW.

## Completed download and exploratory results

403/403 requested markets downloaded after a slower sequential retry. Original
partial download retained (90 successes); repaired dataset saved separately as
research/coinbase_leader_daily_repaired_20261012.json. Historical availability
is 370-403 markets per day, not proof of the actual historical listing universe.
181 daily leader observations; repeated coins and overlapping events are retained.

Final artifact: research/coinbase_leader_pullbacks_final_20261012.json, with
dataset and final script hashes. Earlier intermediate outputs remain preserved.

| Closing-peak pullback | Above purchase close within 30 days | No above-entry close in 30 days | Recovery window unfinished | No entry |
| --- | ---: | ---: | ---: | ---: |
| 10% | 120 | 50 | 7 | 4 |
| 20% | 124 | 42 | 6 | 9 |

Mean time to first above-entry completed close among recoveries: 85.8 hours
(10% arm), 67.94 hours (20% arm); medians 48h and 24h. This secondary audit
follows the full 30-day recovery window independently of the first-green exit.
It is descriptive, not a fill at that close or a portfolio return.

First-green next-open exit policy: 91/175 closed events profitable gross for
10% dips; 92/169 for 20% dips. Arithmetic average exit returns -1.49% and
-0.36%; medians +0.87% and +1.57%. Worst exit -70.27% in both arms. No dollar
compounding is reported because events overlap. Unresolved events excluded from
closed-only statistics are separately retained, not called wins or losses.

These observations support investigating recovery patterns but contradict a
universal guaranteed recovery within 30 days. They do not disprove all variants
of mean reversion. Daily resolution misses intraday recoveries and leader changes.
10/20% means drawdown from the observed post-leadership closing peak, not the
displayed rolling24h percentage reaching -10/-20%. Five final tests passed.
Separate final review pending; original pre-result contract and inputs preserved.

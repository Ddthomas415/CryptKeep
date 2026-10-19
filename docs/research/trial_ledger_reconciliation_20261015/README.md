# Historical trial-ledger reconciliation (2026-10-15)

Read-only reconciliation of every strategy configuration tested so far, so the selection-bias correction for any future experiment uses an evidence-based trial count.
Scope: new files in this folder only. No existing artifact, registry, verdict, brief or mandate was changed. No new trial was run.

## Result
- **Raw executed configurations: at least 690**, against the historical "~576". Nine families still have unestablished counts, so 690 is a floor.
- The Oct 11 table's own rows sum to 566, not 576. Recounted from the artifacts they total 577; four sources differ (hybrid 10 vs 11, top-10 3 vs 4, dynamic 6 vs 8, three ideas 24 vs 9).
- 113 configurations were omitted from, or run after, the Oct 11 count. The largest is the Oct 8 strategy horizon scan (40).
- **Distinct mechanisms: 9. Research programs: about 35.**
- **Effective independent trials: a range, about 9 to 35** depending on method, with 690 as the upper bound. The Oct 11 figure of 10-15 is preserved as historical. No method has been independently checked.
- **Data reuse:** Coinbase BTC/ETH daily history (2015/2016 to 2026-10) has been used by at least nine artifacts. No untouched historical BTC/ETH data remains; only data after the rule froze is genuinely new.
- **Prior art for the template's carry experiment (3a):** `funding_carry_feasibility_20261012.md` already found, at $1,000 over 30 days, about +$2 of funding, -$5 after costs and -$25 after the server.

## Files
| File | Contents |
|---|---|
| `trial_inventory.csv` | 42 rows: every source, its configurations, count basis, Oct 11 value, count status (VERIFIED / VERIFIED_FIELD / REPORTED / DISCREPANCY / UNRESOLVED / EXCLUDED), recorded verdict, datasets |
| `data_overlap.csv` | 14 datasets: venue, symbols, period, location, which experiments used them, status for future tests |
| `count_reconciliation.md` | Oct 11 audit, revised counts, effective-trial methods, DSR hurdle sensitivity, unresolved items |
| `SHA256SUMS` | Hashes of the files above |

## Method and labels
- **VERIFIED:** counted from the artifact's own results by script (distinct parameter combinations; fee levels and periods are not counted again).
- **VERIFIED_FIELD:** taken from a count field the artifact records.
- **REPORTED:** taken from the result document's text; not recounted from raw results.
- **UNRESOLVED:** no count established yet.
- **EXCLUDED:** not a trading trial (NY Numbers).
- Earlier "e01-e03" documents are audits and decision briefs, not trials; they are not counted. Note the ID overlap with the 90-day plan's E1-E5 labels.

## Not done here
- No DSR was recomputed. The hurdle table in `count_reconciliation.md` is a sensitivity input only.
- The 9 unresolved counts, the comparator questions and two dataset attributions remain open (see `count_reconciliation.md` section 7).
- No work-log entry was written; that needs separate approval.

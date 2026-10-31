# Saved hourly archive audit, October 27, 2026

Role: AUDITOR. Risk: LOW; saved-file integrity, schema shape and timestamps only.
Disposition: ACCEPTED for this bounded audit; experiment readiness INCOMPLETE.

## Answer

SHOWN: both compressed Coinbase archives and all 48 selected payloads match
their existing checksum indexes. This verifies preservation, not whether the
original market observations were accurate or executable. No prices, volumes,
signals or returns were analyzed.

| UTC window, end exclusive | Files checked | Complete full window | Complete final 300 hours | Rows |
| --- | ---: | ---: | ---: | ---: |
| August 10 to October 9, 2026 | 24 | 21 | 24 | 34,537 |
| October 9, 2025 to August 10, 2026 | 24 | 0 | 22 | 174,966 |

SHOWN: all selected files are nonempty, strictly timestamp-ascending, with zero
malformed six-field rows, invalid/hour-misaligned timestamps, duplicate timestamps
or out-of-window rows. OHLC/volume field values were not validated.

In the recent archive, OP lacks 4 internal hours, PYTH 1 and WIF 18. None lacks
leading or trailing hours; all three still contain the final 300 consecutive
hours. In the older archive, OP and WIF also lack hours within its final
300-hour interval; their full-window internal missing counts are 97 and 52.

All 24 selected older histories lack the same two five-hour intervals:

- October 25, 2025, 16:00 through 21:00 UTC, end exclusive.
- May 8, 2026, 02:00 through 07:00 UTC, end exclusive.

These overlap outages already described in
`../dynamic_corrected_rerun_20261009.md`; this audit does not establish their
cause or reopen those studies. Per-product missing runs are in `result.json`.

MATIC remains in the declared 25-symbol scope. It has no matching hourly filename
in the inspected indexes and is delisted/disabled in the separately captured
October 27 metadata. It was not silently removed or replaced by POL. The content
audit selected the other 24 product candidates; that selection is not approval
of their identity, historical trading status or account eligibility.

## Reproduction and evidence

Executed once, in VERIFIED_ENV, exit 0, 3.727387 seconds:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B docs/research/ed002_defaults25_archive_audit_20261027/audit_saved_hours.py
```

The script refuses to overwrite its existing result. Do not rerun it in this
folder as a verification step. Inspect the saved result and its source bindings
instead; any future independent reproduction must use a separate output location
and disclose the script-path change.

- 50 checksum comparisons: 2 compressed archives plus 48 selected members.
- 7 source bindings rechecked after completion; all matched.
- 3 synthetic self-checks cover gap, empty-list and duplicate classification.
- 12,092,815 selected payload bytes streamed in memory; no extraction to disk.
- Zero network requests, strategy imports/runs, return calculations or repairs.
- No full pytest run: ledger, bridge and strategy behavior were not changed.

`result.json` SHA256:
`677d8b426266ec661d77ba74c01fded2efa503a14591dcde9b862e86305e2ca2`.
It binds the audit source, universe config, saved metadata comparison, checksum
indexes and both compressed archives. The original indexes and archives remain
unchanged. This is a local selected-file check, not verification of every member
in either archive or full-system proof.

## Consequence and remaining limits

The recent archive provides contiguous final 300-hour historical panels for
24 candidates, but not complete 60-day panels for all 24. The older archive
cannot supply a continuous full-window panel without an explicitly agreed
missing-data treatment. No gap was filled, no observation discarded to improve
returns, and no alternate data was substituted.

These inputs have already been used in research and end October 9. They are not
fresh confirmation data, current warm-up data, or evidence of an untouched
holdout. Candle-open timestamps do not establish when each candle was available;
the six-field schema carries no per-candle observation timestamp. Current
product metadata does not prove historical eligibility.

Next decision: finalize the comparison's dated eligibility, missing-data and
precision/cost contracts using these demonstrated limits, before any protocol
freeze or separately authorized market-data experiment. Preserve all 25 scope
labels and distinguish missing research inputs from permission to trade. No
new fetch, backfill, statistical calibration, activation or operation follows
automatically from this audit.

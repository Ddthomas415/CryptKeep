# Risk-sink flag clear review (deferred live-money item 14, manual reconciliation override) - 2026-10-05

Reviewer: Claude. Scope: `scripts/repair_risk_sink_failed.py`, the command that removes
`risk_sink_failed.flag` (the file that makes `place_order` refuse every new order).
Result: patch 0065 (`5c3b64df`), bundle rev76 folder 73. READY_FOR_INDEPENDENT_REVIEW,
LIVE-PATH. Not pushed.

## Findings

| Sev | Finding | Evidence |
|---|---|---|
| P1 | The command removed the flag whatever its cause. It only checked for journaled fills missing from daily risk. | Probe, previous code: drift flag (local 0.001, exchange 0.501), nothing to replay -> `missing_before=0`, `missing_after=0`, `repair_complete`, exit 0. Same for a fill absent from the journal and an unreadable flag. |
| P2 | A fill with no exchange PnL could only be replayed as 0.0 (`--allow-null-pnl`), or not at all. | Test: a 10.00 loss replayed that way left daily loss at 0. |
| P2 | Clearing the flag wrote no operator event; the script had no tests. | Source. |

## Patch 0065

- Clears only when the flag's own cause is verified: the invariant checker's mismatch, or a named fill now in both the journal and the daily risk ledger.
- Other causes keep the flag (exit 1). `--force-clear --reason "..."` once you have resolved them; it does not bypass a failed replay.
- Every clear needs a `risk_sink_flag_clear` operator event first; if it cannot be written the flag stays.
- Fills with no PnL are replayed with the position store's figure.

11 tests, 9 fail on the previous code. Full suite: 4824 passed, 33 skipped, 0 failed.

## Not fixed

- The flag file holds one cause, the last written.
- A replayed loss counts on the day of the replay, not the day of the fill.
- A position-store replay of an old fill uses the current average cost.
- The ledger join is case-sensitive on venue.
- Deleting the flag file by hand is still possible and unrecorded.

## Laptop state (read-only, checkout `620bc8dbe`)

`.cbp_state/data/risk_sink_failed.flag` is present, written 2026-09-23. Its contents are
quoted in the session report. The journal has 0 fills and none is missing from daily risk,
so the previous command would have removed this flag and printed `repair_complete`. I did
not touch it.

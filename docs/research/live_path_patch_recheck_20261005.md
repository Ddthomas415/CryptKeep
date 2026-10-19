# Re-check of my live-path patches against the documented rules - 2026-10-05

Reviewer: Claude. Why: two patches of this series needed a later correction (0071's note;
0057 by 0074). I re-read `docs/AUTHORITY_MATRIX.md` and the drills in
`docs/LAUNCH_CHECKLIST.md` against 0057-0059, 0062, 0065, 0069-0074.
Result: patch 0075 (`7242a23b`), bundle rev86 folder 83. READY_FOR_INDEPENDENT_REVIEW,
LIVE-PATH. Not pushed. **Review 0057, 0074 and 0075 as one change.**

## Consistent with the documents

Order rows (filled, canceled, open stays submitted, not-found before and after the stale
age, with 0074); "override reconciliation: CLI only"; "change live risk limits: environment
+ restart"; balances; drills 3.1, 3.2, 3.3, 3.5.

## Clarifications (no code change)

1. Drill 3.4 expects `error: stale_order_not_found`. Master gave
   `error: stale_order_fetch_error:OrderNotFound:...`; 0074 gives the documented text.
   **Not verified:** what a real venue raises for a fake order id. If it is not
   `OrderNotFound`, the series keeps the intent `submitted` where master closed it as error.
   Use a well-formed id in the drill.
2. 0069's rationale: `resume_if_safe` also requires a consumed token inside the resume
   window. True on the token path; on the wizard path resume refuses. The fix stands.
3. `docs/AUTHORITY_MATRIX.md` says `resume_if_safe()` restores `execution.live_enabled`; the
   code and its docstring say it never writes it. They disagree; neither changed.

## Finding (P2, a side effect of 0057)

The reconciler listed the newest 60 `submitted` and newest 60 `submit_unknown` intents per
pass. Before 0057 an order past the stale age was closed after five minutes; since 0057 a
working order or one whose lookup keeps failing stays tracked, and nothing bounds the set.

| Tracked | Result before 0075 |
|---|---|
| 61 | the oldest was never looked at; when it filled, the fill was not accounted |
| 150 | 60 were looked up |

## Patch 0075

Each pass lists up to 1000 intents per status; if a listing reaches the limit, the status
file carries `tracked_over_scan_limit` and an error is logged.

3 tests, all fail before the patch. Full suite: 4904 passed, 33 skipped, 0 failed.

## Not fixed

Each tracked intent costs one venue lookup per pass. Nothing cancels or closes an intent
that stays tracked for good.

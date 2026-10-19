# R03 quote qualification - POLICY ACCEPTED by operator 2026-10-09 (implementation pending)

Author: Claude (cloud session), 2026-10-09 ~11:20 UTC, at Damian's "get it done". Policy text only; no code
changed. The integrating session (or another reviewer) must review it; the author does not accept it.

## What the evidence actually contains (checked in real captures)
- Ticker capture (all snapshots so far): payload bid, ask, price, size, time, trade_id, volume. `price/size/time`
  describe the LAST TRADE, not the book. No bid/ask size. Client fields request_started_utc, received_utc,
  response_sha256. Example 05:09 ETH-USD: round trip 44 ms; last trade 0.50 s before receipt.
- Level-1 capture (from the 13:52 run on, --capture-level1): bids/asks [[price, size, num_orders]], sequence,
  auction_mode, server `time`. Example probe BTC-USD 10:59: best ask size 0.00766 BTC (~$632); server time 1.9 s
  before local receipt (includes any laptop clock offset). Sizes are aggregate base quantity at that price.
- Book requests run after the ticker pass, so book and ticker for the same coin are seconds apart, not simultaneous.

## Four separate properties (alignment is not the others)
1. ALIGNMENT (accepted, unchanged): coin and BTC received within 60 s. Says nothing about quote age or size.
2. PROVENANCE: exact Coinbase product ID from the accepted identity map; response_sha256 present; collector_sha256
   in the named accepted set {108d9da4... (pre-10:54), e97f93fa... (post-10:54)}; identity_eligible true at the
   first observation. Fail -> EXCLUDED_PROVENANCE.
3. FRESHNESS: proposed limits (operator to confirm before 2026-11-08, the first primary day):
   a. request round trip (received - request_started) <= 5 s, else STALE_CAPTURE;
   b. where a level-1 book exists: |received - book time| <= 10 s, else STALE_BOOK;
   c. last-trade age (received - ticker time) > 60 min is reported as ILLIQUID_FLAG (not an exclusion: a quiet
      book can still be a live book).
   No limit uses the 60 s pairing as evidence of freshness.
4. EXECUTABLE SIZE: entry needs level-1 best ask size x ask >= registered notional; exit needs best bid size x bid
   >= position size. Proposed notional: $100 (matches the confirmation study's entry_notional_quote). Ticker-only
   captures -> SIZE_UNVERIFIED (never assumed). Level-1 shows displayed size only; it is not fill proof.

## How results would be reported (no loosening of the registered evaluation)
- REGISTERED view: exactly as pre-registered (all structurally valid events, 1.2% per side). Unchanged.
- QUALIFIED view: only events passing 2, 3a/3b and 4 at entry AND at the selected endpoint.
- Every exclusion counted by reason and horizon. Gate (with Damian's all-ranges rule): BOTH views must pass.
  This only tightens. Because the first primary day is 2026-11-08 and level-1 capture starts 2026-10-09, every
  primary event can carry level-1 evidence if the flag stays on.

## Decisions needed from Damian
- Accept the four limits as written (5 s, 10 s, 60 min flag, $100), or change them, BEFORE 2026-11-08.
- Confirm "both views must pass" for the gate.

## OPERATOR DECISION (Damian, 2026-10-09 ~11:15 UTC): ACCEPTED AS DRAFTED
Limits 5 s round trip, 10 s book age, 60 min last-trade flag (report only), $100 displayed size at entry and exit;
registered and qualified views both reported and both must pass. Decided before any outcome exists.
Implementation: integrating session; independent review: CLOUD. Status: POLICY_ACCEPTED, IMPLEMENTATION_PENDING.

## Implementation (Claude cloud session, 2026-10-09 ~22:10 UTC) - READY_FOR_INDEPENDENT_REVIEW
New files only (cmc_book_evidence.py and run_cmc_diagnostic_report.py untouched):
- scripts/research/cmc_quote_qualification.py - qualify_capture() applies the four rules to one capture (entry = buy,
  quantity 100/book ask; exit = sell with the entry quantity); all_ranges_above_zero() = operator gate condition.
- scripts/research/run_cmc_qualified_report.py - wraps the integrated report: registered view unchanged, qualified view
  = DIAGNOSTIC outcomes whose entry AND selected endpoint capture qualify; exclusions counted by horizon/leg/reason;
  gate condition shown for both views; primary_gate = BLOCKED_STATISTICAL_METHOD_NOT_CERTIFIED (R05 NO_CERTIFIED_SAMPLE).
- tests/test_cmc_quote_qualification.py - 10 tests (each limit, clock-offset tolerance, flag-only liquidity, exit quantity,
  gate rule, two end-to-end runs, exchange nanosecond timestamps). 45 pass with book/report/statistics tests.
Real-data check, 13:53 capture as hypothetical entries: 19 Coinbase-listed trending rows -> 7 QUALIFIED; exclusions:
10 identity not eligible, 5 displayed ask below 100 USD (2 of them identity-eligible). Smoke run of the wrapper on all
snapshots: 101 HISTORY_UNCERTAIN, NOT_READY_90_DAYS, nothing scored (as expected).
Design choices for the reviewer: BTC benchmark quotes stay structural-only (policy names coin captures); a missing book
excludes (SIZE_UNVERIFIED), it is never assumed; negative book age within 10 s is accepted as clock offset.

## Bounded correction after independent review, October 10

Entry quantity now uses $100 divided by the registered ticker ask, not the later book ask. This preserves the registered return calculation while checking displayed book capacity for the same position. Exit capacity retains that entry quantity. Invalid/nonfinite/nonpositive/boolean quantities and entry asks are excluded rather than crashing the report.

The descriptive all-ranges condition now requires exactly the named 7/14/28-day sensitivity set and finite positive ordered lower/upper bounds for every interval. Missing evidence cannot satisfy the condition. Primary scoring remains blocked; no statistical certification follows from these repairs.

Verification: 48 targeted quote/book/report/statistics tests passed. Implementation status: READY_FOR_INDEPENDENT_REVIEW; original artifacts and thresholds unchanged.

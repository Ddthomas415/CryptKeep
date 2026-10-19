# Paper ledger (deferred hygiene item 7): independent review of apply_fill

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or
deployed; no config or account change. Patch 0041 (commit 969585bb, cloud
clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev52.zip`,
folder 49. Zip SHA-256:
910c0fad76477f07942c384089a07ff8c2154639e5221c3a2caebb16ea3ce66a

## What holds

One transaction covers order, fill, position, cash and realized PnL. A repeated
fill on a filled order is idempotent. A flat round trip with fees realizes the
fees as a loss.

## Findings (real store, cash 1000)

1. P2, reachable by any strategy that exits in parts.
   - buy 0.3, sell 0.1, sell 0.2: the second sell was rejected
     `insufficient_position`; the position stayed at 0.19999999999999998.
   - buy 0.1, buy 0.2, sell 0.3: a position of 5.55e-17 with an average price
     remained.
   The canonical campaign trades one fixed size per round trip: not affected.
2. P3, the ledger trusted its caller.
   - buy fill with qty -1: cash 1100, position -1.
   - buy at price -100: cash 1100.
   - fill of 5 on an order for 1: accepted.
   - buy with fee -50: cost basis halved.
   - NaN price or fee: stopped only by NOT NULL (IntegrityError).

## Correction in 0041

- `apply_fill` returns `invalid_fill:<reason>` and changes nothing unless price
  and quantity are positive finite numbers, the fee is finite and not negative,
  and the fill is not larger than its order. The order stays open.
- Quantity comparisons use a relative tolerance of 1e-9: a sell within rounding
  of the whole position closes it exactly; a remainder within rounding is
  stored as 0. The engine's submit check uses the same tolerance.

29 new cases, 26 fail on the previous code. Full suite: 4549 passed, 33
skipped, 19 failed (the same 19 as master).

## Not changed

- Positions are keyed by symbol only, not venue.
- A negative fee (maker rebate) is refused, not modelled.
- The fill price is the latest tick, with no age check at fill time.

## Addendum, same day: fill-time quote freshness (patch 0042)

Commit 77545877 (cloud clone only), bundle rev53, folder 50. Zip SHA-256:
6999aa8139b2e27725c6cf0dfcae3ae5cb2fb35de5a48ba60129d8c693ebba65

- SHOWN with the real engine, snapshot reader and market-quality guard: a
  market buy accepted with the tick at 60000 was filled at 40020.0 after the
  snapshot was rewritten with that symbol's tick three hours old at 40000. The
  submit gate checks snapshot age (5 s) and tick age (default 600 s); the fill
  step checked neither.
- Change: `evaluate_open_orders` applies the same market-quality check to a
  snapshot quote before filling. If it fails, the order stays `new` and is
  counted as `deferred`; it fills on a later cycle once the quote passes.
- No effect expected in normal running, where submit and fill use the same
  tick in the same loop.
- 5 new cases, all fail on the previous code. Full suite: 4554 passed, 33
  skipped, 19 failed (the same 19 as master).

Not changed: the guard skips the age check for a tick with no timestamp and
passes when there is no quote data unless `block_when_unknown` is set (backlog
item 29); paper queue intents have no time-to-live.

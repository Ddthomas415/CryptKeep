# Where a live order would come from: independent review

Date: 2026-10-05. Reviewer: Claude (AUDITOR). No patch: nothing here is a
bounded defect I am authorized to fix (see "Why no patch").
Reviewed at master `97c24c8e` plus the unpushed series through 0059; this
checkout is `620bc8dbe`. Live is not enabled here.

Scope: the canonical live consumer (`live_intent_consumer.run_forever`) from
queue to submit, and what feeds each live path.

## Finding 1: neither live path has a working source of orders

SHOWN by reading every call site and by running the one script:

- The strategy runner, the meta strategy runner, the signal router, the
  execution plan writer and the pipeline intent writer all write to
  `IntentQueueSQLite` (the paper queue, `intent_queue.sqlite`).
- Nothing in `services/`, `scripts/` or `dashboard/` writes to
  `LiveIntentQueueSQLite` (`live_intent_queue.sqlite`), which is the only
  thing the canonical live consumer reads. Only tests insert there.
- The legacy executor reads `ExecutionStore` intents with `mode="live"`. The
  only writer is `scripts/live/live_submit_intent.py`, which calls
  `ExecutionStore.submit_intent`. That method does not exist. Run against a
  scratch state directory it ends in
  `AttributeError: 'ExecutionStore' object has no attribute 'submit_intent'`.
  Its test passes because it substitutes a fake store that has the method.

This checkout's data agrees: `live_intent_queue.sqlite` holds 8 rows, all
`rejected`, all stamped `2026-01-01T00:00:00Z` (fixture rows);
`execution.sqlite` has no `intents` table; the paper queue holds the 174
strategy fills.

Consequence: enabling live with the code as it stands would place no orders.
Eight live-path patches in this series (0037, 0039, 0045, 0055 to 0059)
harden a path that nothing currently feeds. They are still correct, and they
matter the day a producer exists, but the promotion step "paper to shadow to
capped live" has a missing piece that I did not find recorded in the backlog:
the component that turns a strategy decision into a live intent.

## Finding 2: a transient block ends an intent for good

Read in code (`run_forever`), and pinned by
`tests/test_live_intent_consumer_orphan_fix.py`: a market-quality block, a
clock-skew block, a guard error or a risk refusal moves the intent to
`rejected`, which is terminal. The intent TTL (300 s) is not used as a retry
window. A sell that exits a position, refused because the quote was stale
for one second, is gone. The strategy runner derives the intent id from the
bar, so for a daily strategy the exit would not be offered again until the
next bar.

## Finding 3: the consumer's own daily caps are off when unset

SHOWN by probe: with no `risk.live` block, `live_risk_cfg()` returns
`max_trades_per_day: 0` and `max_daily_notional_quote: 0.0`, and
`atomic_risk_claim` treats 0 as "no limit": 500 claims of 1e9 notional each
were all accepted. This checkout's `user.yaml` has no such caps set. The
order boundary (`place_order`) is separate and does fail closed: it requires
`CBP_MAX_TRADES_PER_DAY`, `CBP_MAX_DAILY_LOSS`, `CBP_MAX_DAILY_NOTIONAL` and
`CBP_MAX_ORDER_NOTIONAL`, which this checkout's `.env` sets to 10, 15, 50
and 25. So an order would still be capped, by the second gate only.

## Finding 4: every limit applies to exits as well as entries

Read in code: the trade-count, daily-notional and daily-loss limits do not
look at the side. Once the daily loss limit is reached, a sell that would
close the losing position is refused like any other order. The risk claim is
also taken before the router decision and the submit, so refused and failed
attempts use up the day's trade count.

## Other facts

- This checkout's `live.exchange_id` is `binance` with `sandbox: false`
  (`enabled: false`). Paper runs on Coinbase, and Binance needs
  `CBP_ALLOW_BINANCE`.
- `risk.max_daily_loss_quote` is 0.0 here; the loss limit that would apply
  is the `.env` value.

## Why no patch

- Finding 1: writing a live producer, or repairing the manual script, makes
  live orders possible. That is your decision, not a defect fix.
- Finding 2: retrying needs a `submitting -> queued` transition the pinned
  lifecycle map does not have.
- Findings 3 and 4 are policy: what an unset cap means, and whether limits
  should let a position-reducing order through.

## Decisions for the operator

1. Which live path is meant to run, and what feeds it.
2. Whether a transiently blocked intent should retry within its TTL.
3. Whether an unset consumer cap should refuse instead of allowing.
4. Whether loss and count limits should exempt orders that reduce a position.

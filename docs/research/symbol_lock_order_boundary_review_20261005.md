# Symbol loss lock at the live order boundary - 2026-10-05

Reviewer: Claude. Scope: `services/execution/place_order.py`. Result: patch 0070
(`4990c292`), bundle rev81 folder 78. READY_FOR_INDEPENDENT_REVIEW, LIVE-PATH (restrictive
only). Not pushed.

## Finding (P2 for live)

The fill sink locks a symbol for `CBP_SYMBOL_LOCK_MINUTES` after `CBP_SYMBOL_LOSS_LIMIT`
consecutive losing closes (`.env` here: limit 3). The only reader of that lock was the
legacy executor. Test with the real fill sink and execution store: after three losing round
trips on BTC/USD the lock row existed, and a BTC/USD buy through `place_order` (sync and
async) reached `create_order`. The canonical consumer submits through that boundary and has
no lock check of its own.

## Patch 0070

- The boundary refuses a buy on a locked symbol (`CBP_ORDER_BLOCKED:symbol_locked`).
- A lock that cannot be read refuses the buy.
- Sells are not refused at the boundary.

7 tests, 3 fail on the previous code. Full suite: 4866 passed, 33 skipped, 0 failed.

## For you to confirm

Buys only is my choice: on a spot account a sell reduces the position, and refusing it would
hold a losing position open for the length of the lock. The legacy executor still holds
back both sides.

## Not fixed

- The canonical consumer marks a refused order as terminal `rejected`; a locked entry is not
  retried when the lock ends.
- The lock is keyed by the fill's symbol string and compared with the order's symbol string.

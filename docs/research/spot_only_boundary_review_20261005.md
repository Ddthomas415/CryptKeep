# Derivatives boundary at the order chokepoint: independent review (backlog item 15)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW, HIGH risk (live order boundary; the
change only refuses). Patch 0055 (`7c9ed268`), bundle rev66, folder
`63_spot_only_order_boundary`. Not pushed, not applied to this checkout.

## Result

No reachable defect found. Item 15's deliverable is a roadmap document and a
test of its wording. In code, a contract symbol (`BTC/USDT:USDT`) is refused
today on every venue traced, but only as a side effect:

- Binance and Gate market rules come from spot endpoints.
- Every other venue except Coinbase has no rule fetcher, so all its live
  orders are refused.
- On Coinbase the quote of `BTC/USDC:USDC` parses as `USDC:USDC`, which is
  not a portfolio currency.

Extra order parameters (margin mode, leverage) are filtered and the executor
passes none. This checkout's runtime config contains no contract symbol.

## Finding (P3, hardening, shown by test)

Nothing named the boundary. With the other gates satisfied as the existing
boundary tests satisfy them, a sell of a contract symbol by an account
holding the base asset reached `create_order`. The Coinbase rule fetcher
returned tradable rules for a contract market if one was looked up.

## Correction

- `place_order`: a symbol containing `:` is refused (`non_spot_symbol`); a
  market the client describes as non-spot is refused (`non_spot_market`).
  Runs before the kill-switch and arming checks, sync and async. A spot pair
  also offered on margin is not refused.
- Coinbase rule fetcher: non-spot market yields inactive rules (`NOT_SPOT`).

## Verification

18 new tests, 13 fail on the previous code (the other 5 are spot-order
controls). Full suite at the code of 0055: 4690 passed, 33 skipped, 19
failed (the same 19 as master).

## Not covered

A venue that enables margin on a spot account server-side is outside what
this check can see.

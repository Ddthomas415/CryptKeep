# Live position cap: preferred-path trace and treatment boundary

2026-10-28. Active role AUDITOR. Source trace SHOWN; treatment INCOMPLETE.
No production source, runtime policy, account, credential, store or scheduler changed.

## Practical Outcome

A check_live-only patch would miss the preferred submission route. Reuse the
existing place_order/place_order_async authority instead of inventing another
order router, exchange client or reconciliation service. The cap must count
reserved/in-flight buys as well as filled holdings; spendable balance alone is
not the position size. Do not implement an untrusted extra intent field as proof.

One material operator decision remains before specifying the financial scope:
does the configured cap cover ALL holdings in the venue/account (including manual
holdings and pending buys across quote pairs), or only reliably bot-owned holdings?
Recommend all holdings per base asset in that venue/account; it measures actual
exposure but can refuse new bot buys where manual holdings already exceed the cap.
It must not liquidate those holdings or disable reducing sells merely because
the cap is exceeded. Bot-only scope needs reliable ownership evidence, not a tag.
Neither option grants access to accounts, changes the cap value or arms trading.

## SHOWN Source Trace

- `services/execution/live_intent_consumer.py:371` calls _risk_check_and_claim;
  line412 calls services.live_router.router.decide_order, and line479 calls
  LiveExchangeAdapter.submit_order. This path does not call the earlier
  LiveRiskGates.check_live method. This is source wiring, not deployed-process proof.
- `services/execution/live_intent_consumer.py:98` passes only global trade/day
  notional limits to `storage/live_intent_queue_sqlite.py:458` atomic_risk_claim.
  The transaction increments daily counters; it has no asset/side/position input.
  It is not a per-asset exposure reservation despite its atomic name.
- `services/live_router/router.py:44` calls the existing safety gates;
  `services/execution/safety.py:34` checks minimum order size, daily trades and
  daily loss, not the declared per-position cap. Optional gates can still reject
  orders; no claim that every protection is bypassed.
- `services/execution/live_exchange_adapter.py:94` delegates to place_order.
  `services/execution/place_order.py:693` and :721 share _enforce_fail_closed
  (line570) before the final synchronous/asynchronous create_order call.
  Other arming, kill, health, daily-risk, market-rule and funding gates remain
  meaningful and must not be removed or reordered casually.
- `services/execution/place_order.py:179` uses fetch_balance to test spendable
  funding. `_extract_spendable_balance` (line131) prioritizes free/spendable
  amounts; it is not a total-held-position or pending-buy valuation contract.
  `coinbase_portfolio_guard.py` checks availability of a quote account, not the cap.

## Existing Position Sources: Reuse, But Do Not Equate Them

`storage/live_position_store_sqlite.py:98` returns local filled qty/avg_price;
missing rows return zero, and this accessor omits stored updated_ts. Fills update
the ledger idempotently through the canonical fill sink. It does not prove a
complete fresh account snapshot, manual holdings, or unfilled-order exposure.

`storage/position_state_sqlite.py:77` exposes qty plus updated_ts and raw data,
but `services/execution/reconciliation.py:17` writes it from fetch_balance using
a permissive numeric fallback. That helper can map unknown/invalid numbers to
zero. Do not treat every flat row as a verified absence or automatically trust
this cache for a fail-closed cap. No actual stored row was opened in this review.

The existing October9 section of
`docs/decisions/position_truth_resolution_authority.md` already records HALT AND
ADJUDICATE, persistent drift confirmation and canonical kill-switch binding.
`services/reconciliation/position_truth.py:108` implements a one-pass entry point.
Preserve that recorded decision; do not ask the operator to choose resolution
authority from scratch or infer its scheduled deployment from the document.
Its drift hysteresis is not permission to admit oversized buys while waiting
15minutes for confirmation, nor an automatically adopted cap-snapshot freshness rule.

## Recommended Bounded Treatment After The Scope Decision

Reuse the same existing authenticated client/portfolio identity that supplies
the submission path; no extra credential authority. Complete balance pagination
and identity/source provenance (queued fix1) must be handled before treating a
missing holding as zero. Total holdings, available funds and order reservations
are separate quantities. Fix1's sync/async and raw-row merging requirements remain.

Design one atomic exposure-increase check/reservation at the common raw-order
authority, covering both sync and async routes. Pin venue/account/base identity,
full current holdings, as-of/receive time, pending unfilled buys and conservative
USD valuation. Define fee/FX/partial-fill treatment before implementing; do not
silently equate a quote token with USD or cost basis with current exposure.
No reservation may disappear merely because a submit reply is ambiguous.
Reconcile fills without counting the same units as both filled and outstanding.

Fail closed for increases on unknown/stale/incomplete evidence. Preserve reducing
sells and the independent existing arming/funding/kill/daily constraints; no new
authority to sell unknown quantities or bypass other gates. Do not add automatic
liquidation, drift auto-correction or a new background job to make the cap pass.

Required future synthetic proof: held40+proposed25 versus cap50, manual/locked
holdings, two concurrent buys, sync/async bypass attempts, same base across pairs,
account isolation, balance page failure, stale/unknown marks/FX, partial fills,
cancel/submit_unknown/restart reservation retention, and reducing sells. These
are specified tests, not tests run or new tables/migrations authorized here.

## Current Limits And Collector Status

Only source text/AST was inspected; production modules/clients were not imported,
no DB or private endpoint opened, and no live/armed/server state established.
Source hashes are saved separately. This is not full-system audit or live proof.
Original selected-method probe remains unchanged evidence; no failed backtest,
200-test repetition or financial result was generated.

At10:20UTC (06:20NewYork), the first public pilot slot was still due10:35UTC;
its namespace held only two empty logs. No forced or duplicate capture occurred.
This treatment trace does not modify any pinned collection source. The operator
scope question affects this live repair only, not the already-authorized pilot.
Production treatment remains INCOMPLETE pending that decision and implementation
proof with independent/human high-risk review.

# Reconciliation execution-price and quantity evidence

Active role ENGINEER. Risk HIGH. State READY_FOR_INDEPENDENT_REVIEW.

## Bounded treatment

An order's limit price is not its execution average. Removed that substitution
from the cumulative synthetic-fill fallback. If no priced trade evidence exists
and the order average is missing, nonnumeric, nonfinite or nonpositive, the order
remains accounting-incomplete with no fabricated fill. Complete priced trade
records may still finish reconciliation without an order average.

Added an optional remote-quantity bound to atomic fill persistence. The
reconciler passes the exchange's reported cumulative filled quantity. Inside
the same BEGIN IMMEDIATE transaction, recorded quantities are validated and
the proposed new quantity cannot exceed that bound. Duplicate IDs do not
consume quantity twice. This protects against real-trade and synthetic writers
racing after reading the same earlier local snapshot; exceeding the bound is
refused before fill or delivery evidence is committed.

This does not reconstruct a missing partial VWAP/fee distribution, invent
remaining trades, convert fee assets or retroactively restate accounting.
Missing partial history continues to be explicit and pending. An order's
reported average remains venue evidence, not an independently audited value.

## Proof

VERIFIED_ENV: temporary databases/state, clean subprocess environment, fake
exchange, no repository conftest/network/orders/operator databases.
Final five-file targeted run: 46 passed in 0.71 seconds. Eleven additional
cases cover six invalid/missing averages, closing with complete trade evidence,
stale synthetic snapshot, late real trade, actual two-thread writer race and
duplicate quantity. Existing datetime warnings remain.

Files tested: test_live_executor_shadow_and_trade_reconcile.py,
test_reconcile_accounting_delivery.py, test_symbol_loss_fill_once.py,
test_fill_sink_live_position_integration.py, test_fill_sink_logging.py.
No full-suite, CI, remote-host, genuine exchange concurrency or power-loss proof.

## Limits

The bound applies to this reconciler's writes, not every caller of add_fill.
Unexpected persistence failure still interrupts a reconciliation call; it is
not a successful delivery. Orders with conflicting or missing evidence require
operator/reviewer disposition, not automatic history rewriting. Historical
cutover and prior treatment release restrictions remain in force.

Independent financial/concurrency review is required. The prior review agent
was unavailable due to usage limits; no independent approval is claimed.
No config/account/collector/order/publication/deployment change.

## Human acceptance

The user approved the 46-test treatment handoff. Bounded disposition:
ACCEPTED_WITH_RISK through human review, not independent-agent acceptance.
This does not authorize deployment, database migration, process restart or
historical fill reconstruction. Full-suite, CI and host verification remain
outstanding before a release decision.

# Live position cap: account-wide per-asset repair contract

2026-10-28. Active role DIRECTOR. Risk HIGH (financial admission and concurrency).
Design READY_FOR_INDEPENDENT_REVIEW; production repair INCOMPLETE.

## Adopted Operator Scope

The operator directly selected "All account holdings per asset (Recommended)"
in this chat. This adopts the exposure boundary, not production implementation,
account access, a new cap value, arming, liquidation or deployment.

Count manual and bot holdings and pending buys across quote pairs within the
same venue/account/base-asset boundary. A manual holding can therefore refuse a
new bot buy. Preserve the existing configured cap; its current effective value
has not been established here. Do not present the synthetic $50 probe as a
verified live setting.

Claude's separately read October28 addendum proposes a dedicated Coinbase
portfolio. That is a preservation alternative, not permission to create one,
move funds, obtain a key or silently narrow "all account holdings" to whichever
portfolio an existing key happens to expose. If the account boundary includes
multiple portfolios, their required evidence must be complete or admission is
unknown. The authenticated identity and intended risk boundary must agree.

This record supersedes the pending scope question in the earlier source trace;
that historical trace and its hashes remain unchanged.

## Integration And Data Contract

1. Reuse the common `place_order` / `place_order_async` raw-order authority,
   shared by preferred and legacy paths. A legacy `check_live` patch alone is
   insufficient. Preserve the other arming, kill, health, funding, daily and
   market-rule gates. No parallel router, client or background service.
2. Key exposure by verified venue, account boundary and canonical base-asset
   identity, not strategy, ticker text, API-key identity or quote pair. Verified
   distinct accounts remain isolated; aliases must not split the same asset.
3. Require complete, strictly parsed total holdings, including locked amounts,
   with source identity, page-completeness evidence, exchange as-of time where
   supplied and local receipt time. Missing, malformed or inaccessible data is
   unknown, not zero. Free balance is for funding, not total exposure. Existing
   local filled-position caches cannot alone prove manual account holdings.
4. Include remaining unfilled external/manual buys and durable local queued,
   submitting, submitted, held and uncertain-submit buy obligations. Reconcile
   order/client IDs and fills so known identical obligations are not added twice.
   Unknown identity/overlap cannot justify releasing exposure. A pending sell
   does not free capacity before its confirmed fill is coherently reflected.
5. Admission and durable reservation must be atomic across participating bot
   writers and sync/async routes. Reuse existing transaction patterns; daily
   count/notional claims are not an asset reservation. A caller-supplied balance
   or intent tag is not independent proof. This design authorizes no migration.
6. USD exposure is total held base units plus remaining committed buy units,
   valued conservatively using identified, timestamped marks and required FX.
   Do not assume USDT/USDC equals USD or use cost basis as the current mark.
   Bound proposed buy quantity/price consistently with the actual order type;
   an unbounded market fill cannot promise a hard maximum notional. Unknown
   valuation or an unsupported order envelope refuses an exposure increase.
7. Define fee currency explicitly. Quote-currency fees belong to affordability,
   not extra base units. Conservatively retaining base units before any base-fee
   deduction is permissible; never assume a fee deduction creates buy capacity.
   Do not charge the same fee twice or change configured fees in this repair.
8. Reserve before submission. Retain reservations through ambiguous submission,
   restart, partial fill, unresolved cancel or unreadable queue. Release only on
   authoritative terminal evidence and a coherent holdings/fill baseline. If
   overlapping balance/order observations cannot be reconciled, retain a
   conservative hold or refuse increases rather than guess an exact exposure.
9. Missing/stale evidence fails closed for increases. Freshness bounds must be
   explicit reviewed inputs covering balances, orders, marks and FX, with
   age/skew tests; no permissive default and no invented live setting. The
   October9 drift-observation window is not this admission freshness policy.
10. A genuinely reducing spot sell is not newly refused merely because this cap
    is exceeded or increase-evidence is unavailable. It still needs existing
    quantity/ownership, no-oversell and independent gate checks. Unknown-side,
    short, margin and derivative orders are not deemed reducing by assertion.

Keep the existing HALT AND ADJUDICATE drift authority; no automatic correction,
disarm, liquidation or new reconciliation schedule. Drift hysteresis does not
permit oversized entries while waiting for drift confirmation.

## Arithmetic Acceptance Cases (Required Future Tests)

These are proposed deterministic fixtures, not newly run tests or account facts.
With an invented cap of $50 and a fixed valid USD mark:

- Held $40, no pending buys, proposed $25: refuse ($65).
- Held $40, no pending buys, proposed $10: exact-cap admission is eligible ($50),
  subject to all other gates and proven order bounds.
- Held $40, pending $8 across another pair, proposed $5: refuse ($53).
- Manual holdings $70, proposed bot buy $1: refuse; do not liquidate.
- Held $65, reducing sell $20: this cap adds no refusal; other checks still apply.
- Held $35, two simultaneous buys of $10: at most one can reserve/admit; the
  next sees $55, not the original $35. Prove this using real local transactions.

Also require tests for manual/locked holdings, pair aliases, account isolation,
all-page completeness, invalid/negative/nonfinite quantities, stale/future/skewed
observations, FX failure, market order bounds, partial fills, duplicate IDs,
unknown submit/cancel, restart, store failure and sync/async bypass attempts.
No fake-gate unit result is full-account or exchange-concurrency proof.

## Limits, Proof And Next Boundary

SHOWN: the earlier source trace identifies the common order authority and the
absence of per-asset reservations in the inspected daily claim. No current
account, DB, credentials, private API or live/armed state was inspected.

UNVERIFIED: availability and coherence of complete account-wide holdings/orders
from the installed client. The separately queued balance-pagination repair is a
dependency for trustworthy zero holdings, not an excuse to silently use one page.
Separate exchange API reads are not a transactional account snapshot.

Bot serialization cannot prevent an external manual order, transfer or price
move after observation. This is an admission safeguard against observed exposure
plus retained obligations, not a guarantee that an account never exceeds its cap.

Next: review this contract, including account identity/completeness, observation
coherence and explicit freshness inputs, then a separately scoped synthetic
implementation using existing authority/store surfaces. Inspect source before
patching; no private evidence acquisition or production behavior change follows
from this document. Independent/human high-risk review remains required.

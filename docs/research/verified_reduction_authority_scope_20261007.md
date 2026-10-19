# Verified spot reduction authority: decision scope

DIRECTOR. HIGH risk. Proposal only; no live-routing edit or migration.

## SHOWN inspected boundaries

Canonical submission gates market quality and timestamp symbol locks without
side/reduction classification. Risk gates also do not receive side or position
when evaluating daily loss/trade count. Sell/reduce_only metadata is not proof.
LivePositionStore in execution database tracks venue/symbol fills, rejects
accounting oversells, and offers read-only exchange comparison. get_position
returns qty/avg_price, not a reconciliation freshness assertion. Post-fill
oversell rejection does not prevent an oversized order reaching the venue.
No atomic pre-submit sell-quantity reservation in inspected executor path.

## Recommended bounded policy, pending operator decision

Only verified spot risk-reducing sells may bypass symbol loss cooldown and
entry-quality vetoes. Keep auth, explicit live arming, global emergency halt,
reconciliation validity, valid instrument/order constraints and submission
integrity mandatory. Do not implicitly exempt daily loss/trade counters or
other gates; each requires separate explicit classification.

Reduction proof must identify exact account/venue/symbol, finite reconciled
positive holdings, fresh reconciliation evidence and available quantity after
all in-flight sell reservations. Claim intent and reserve quantity atomically
in the same execution database; preserve reservation across unknown submit,
partial fill, cancellation and restart. Release only on authoritative terminal
evidence. Never trust caller metadata or a stale read alone.

## Proof required before integration

Buy/oversized/unknown-position/unknown-reservation proposals remain blocked;
verified bounded sell passes only the two selected vetoes. Concurrent sell
claims cannot exceed holdings. Unknown submission cannot free a reservation.
Partial fills and terminal reconciliation apply once. Auth/arming/global halt
and order validation still block. No venue calls in initial tests; independent
review mandatory. Full-system protective exits remain unverified until reviewed
integration evidence exists. No campaign/account changes or live activation.

## Decision needed

Approve the two-veto exception for verified reductions, or retain current
all-orders blocking. This contract changes live risk policy and cannot be
inferred solely from acceptance of the runner quantity correction.
Implementation INCOMPLETE pending this material policy choice.

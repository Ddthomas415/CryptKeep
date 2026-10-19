# Proposed spot-exit account ownership contract

Active role: DIRECTOR. Objective: define the account boundary required before
integrating the unwired protective-exit reservation and receipt prototype.
Risk: HIGH. Proposal only; no runtime contract is implemented here.

## Evidence

SHOWN in inspected code: credentials_loader selects credentials by venue, not
an account identifier. live_positions uses (venue,symbol), live_position_fills
uses (venue,fill_id), and order_dedupe uses (exchange_id,intent_id). The isolated
receipt adapter binds venue/order/symbol but has no account field. Locally built
sessions do not themselves prove authenticated account identity.

Consequently, the current evidence cannot justify a cross-account-safe live
bypass. This is an integration limitation, not a claim of an observed wrong-
account trade. No stored credentials were loaded or printed for this inspection.

## Recommended initial contract

Use one dedicated execution database per verified venue account, with an
immutable non-secret account binding. Verification must cover the venue,
environment (sandbox versus production), and relevant portfolio/subaccount.
All intent, dedupe, fill, position, reservation and receipt writers must use that
same bound database and authenticated account context. Every entry point checks
binding before using evidence. A database path or operator label alone is not
account proof. API-key fingerprints alone are not stable account identifiers.

The trusted session factory must supply independently verified account context;
caller metadata is insufficient. Venue-specific verification capability is
UNVERIFIED. If identity cannot be established, do not grant the new bypass;
retain existing protective-exit behavior rather than globally disabling exits.

Credential rotation for the same verified account may preserve the binding.
Changing account, subaccount or environment must not reuse old holdings or
order evidence. No automatic rebinding, deletion or reset. Existing unbound
databases stay unbound until provenance is established; a new empty database
does not imply that the remote account has no holdings or open orders.

## Preservation alternative

A shared database could instead add account/environment identity to every
relevant primary/unique key and every writer/read query, with a separately
reviewed migration. It preserves multi-account operation in one file but is a
larger change. The dedicated-database recommendation does not remove any agreed
platform capability; it limits only the initial prototype integration.

## Required proof before integration

- Wrong account, subaccount, environment or venue cannot consume old evidence.
- Rotation on the same account is distinguished from account replacement.
- All writers/readers use the bound account; direct legacy writes cannot bypass it.
- Account-provenance failure does not disable existing protective exits.
- Existing holdings and orders reconcile before any new database is used.
- Independent review covers binding, recovery and venue-specific verification.

Decision needed: dedicated database per verified account, or shared-database
account-key migration. No implementation or live authorization is inferred from
this proposal. Acceptance: BLOCKED on account-boundary choice and verification
contract; unaffected existing behavior remains unchanged.

Independent review: Hume found no actionable finding in the proposal after
source/document inspection. Implementation remains BLOCKED; no implementation,
bypass or deployment approval. Venue verification and enforcement are unverified.

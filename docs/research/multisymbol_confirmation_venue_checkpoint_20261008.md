# Confirmation venue and cost checkpoint

AUDITOR. Scope: find existing account-cost evidence and confirmation authority,
not open a trading account, change credentials or start a campaign.

SHOWN: multisymbol_baseline_v1 used public OKX spot hourly archives, with
10/25/60bps per-side fee scenarios. These are not actual account fees.
Its three phase runs and exploratory calendar diagnostics are preserved.

SHOWN: docs/research/coinbase_authenticated_scope_proof_20261007.md records
an October7 laptop Keychain-backed Coinbase permissions observation, separately
reviewed for bounded interpretation. It does not establish current session
availability, account commission rates or any OKX account identity.

SHOWN: docs/research/crypto_edge_source_decision.md authorizes public OKX
derivatives context collection only, not private credentials or execution.
The separate spot baseline registration authorizes public research data, not
an authenticated OKX account. The documented paper7.5bps assumption and
existing ES trial fees are not the measured fee tier for this new experiment.

UNVERIFIED: intended confirmation execution venue/account, its spot fee tier,
product/pair coverage, measured slippage, and current private-session access.
No account-fee endpoint was called and no secrets were read/displayed here.
No evidence was found in the inspected research/checkpoint documents establishing
an authenticated OKX spot fee observation; this is not proof no OKX account exists.

Recommendation: align confirmation data with the operator's actual intended
venue/account before treating its fees as applicable. If Coinbase is chosen,
use separately registered Coinbase market data and costs; do not relabel the
OKX baseline. If OKX is chosen, establish its account-specific read-only fee
evidence through an existing authorized credential path, not a generic table.

One decision required: which venue/account should confirmation target?
Only venue-dependent collection/confirmation is BLOCKED by that missing fact.
All frozen results remain intact. Cycle-floor window and prospective sample
requirements must be explicit before candidate selection; no winner is promoted.
No source/config/account/campaign change, credential write or private request.

## Operator resolution and subsequent evidence

Operator chose Coinbase; do not ask the resolved venue decision again.
Subsequent separately reviewed read-only observation returned current spot
maker25bps/taker50bps. Public catalog covers all five coins againstUSD/USDT.
See coinbase_confirmation_cost_preflight_20261008.md. Prior text records the
checkpoint before that request, not denial of the subsequent observation.
OKX results unchanged; product-specific fees and confirmation contract pending.

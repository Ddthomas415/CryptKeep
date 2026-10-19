# Spot exit settlement checkpoint

## Acceptance checkpoint

Operator wrote INDEPENDENTLY_REVIEWED AND ACCEPTED for this checkpoint.
Independent Hume review: ACCEPTED_WITH_RISK, bounded to unwired primitive,
no blocking finding within trusted-receipt contract. Reviewer inspected only;
20-test run remains implementing-agent execution, not independent execution.
Remote order ID is presence-checked, not yet bound to the intent; the future
trusted producer must establish that binding. Real-schema integration and
transaction failure injection remain required before live wiring.
No publication, deployment or account mutation inferred from acceptance.

ENGINEER HIGH. Isolated9wbPbN primitive only, no production routing changes.
Added durable terminal receipt and settlement tables. settle requires receipt
venue/symbol/remote identity, matching terminal intent, bounded reported filled
quantity, exact recorded fill coverage, completed canonical deliveries and
matching applied live-position fill records. Atomically records settlement and
removes reservation. Settled intent cannot reserve again. Partial/unknown
orders retain full reservation; generic canceled status alone is insufficient.

20 focused tests passed0.35seconds. Zero-fill canceled release once, restart
idempotency, missing receipt retention and partial-fill accounting tested.
Fixtures manually supply trusted receipts: no receipt producer wired or proven.
No real schema migration/runtime, crash injection or full-suite proof.
Float equality may cause conservative refusals. Position version/provenance,
all-writer coordination and authoritative terminal evidence remain integration
requirements. No live gate bypass, account/state change or deployment.
Independent review requested; READY_FOR_INDEPENDENT_REVIEW.

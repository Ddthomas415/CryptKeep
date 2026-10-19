# Reconciliation writer-conflict isolation

Active role ENGINEER. Risk HIGH. READY_FOR_INDEPENDENT_REVIEW.

Reproduced both real-trade and synthetic-write conflicts with actual SQLite:
two new tests fail before correction with the quantity-bound ValueError.
A competing writer inserts a complete durable fill between the caller's read
and write. The losing writer must leave the intent pending, report incomplete,
and allow a second zero-fill canceled intent to finish in the same pass.
Next pass delivers the winner once and terminalizes only after coverage checks.

Both fill-persistence call sites now use a bounded helper. Ordinary persistence
exceptions are logged, durable coverage is re-read diagnostically, and the
affected intent remains incomplete even if that read succeeds. Failed writes
do not increment added-fill or latency-fill counters. Unknown coverage remains
incomplete. No bound relaxed and no competing quantity accepted.

VERIFIED_ENV: denied network/operator-home contents and writes except dependency
reads, clean env/null keyring, disposable DBs, fake venue. Seven-file result:
109 passed, 16 existing datetime warnings, 1.70s. JUnit and candidate source at
/private/tmp/cryptkeep-writer-treatment-20261007/writer_results.xml and source/.
No revised full-suite/CI/real venue/power-loss proof.

Independent re-review requested from Hume for finding3 only. Profit/loss ordering
finding remains unresolved; overall publication candidate remains REJECTED.
This isolates fill-write failures only, not all possible per-intent exceptions.
No accounts/config/credentials/cohort/process/orders/publication/deployment change.

Independent GATE: Hume ACCEPTED finding3 correction after read-only source and
JUnit inspection. No independent test execution or live proof claimed.
Overall candidate remains REJECTED for distinct-event ordering. Before repairing
that finding, select durable journal receipt order versus exchange execution-time
order with an explicit late-event policy; no financial ordering decision inferred.

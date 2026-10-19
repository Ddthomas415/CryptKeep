# Accepted intent lookup correction

Human-accepted bounded correction, not deployment authorization.

## Patch base

`accepted_lookup_correction.patch` is incremental. It requires base
`97c24c8e4884629347a5492ae848133becd9027b` plus folder 1 (cooldown)
and folder 6 (protective exit) from
`cryptkeep_review_bundle_2026-10-02_1.zip`.
It does not include or require folder 5 (PnL reporting).
Do not apply it directly to the dirty main working checkout.

The patch changes only the queue existence query, its protective-exit caller,
and associated tests. It preserves source/symbol/status matching semantics.
It does not add atomic order reservation, cover all lifecycle states, fix
multi-symbol processing, or authorize campaigns or live execution.

## Evidence

The earlier isolated six-file selection passed 99 tests, including reporting.
Packaging verification reconstructs the stated base with folders 1 and 6,
checks patch application, and reruns cooldown/runtime/protective-exit tests.
See the dated work-log entry for the reproduced packaging result.

Integration must preserve this handoff and its work-log evidence. Acceptance
of this incremental correction is not blanket acceptance of its dependencies.

# Symbol-loss retry treatment

Active role: ENGINEER. Risk: HIGH. State: READY_FOR_INDEPENDENT_REVIEW.

## Bounded objective

Make the canonical fill sink's symbol-loss side effect retryable without counting a fill twice or allowing an old profitable fill to reset subsequent losses. This is a prerequisite for reconciliation retries, not the complete reconciliation treatment.

## Change

ExecutionStore records a permanent marker keyed by venue and fill ID in the same BEGIN IMMEDIATE transaction as the symbol counter update. Duplicate delivery returns the original event's counter result without rewriting the current counter or lock expiry. Conflicting symbol/PnL replays and nonfinite PnL are refused. The sink reports a failed loss update as not-ok and writes the existing unhealthy-accounting flag rather than claiming success.

Existing loss policy is preserved: negative realized PnL increments the symbol-wide counter; nonnegative PnL resets it. This does not redesign portfolio ownership, fee-inclusive loss policy, or cross-venue symbol scope.

## Evidence

Nine new tests passed in a disposable directory outside repository conftest with a clean environment, explicit temporary database paths, disabled plugin autoload and bytecode writes. Tests cover restart replay, lock expiry preservation, stale profit replay, concurrent duplicates, transactional rollback after marker-write failure, conflicting replay, venue identities, nonfinite values and sink retry after daily accounting already committed. A subsequent combined run with the six existing fill-sink/live-position integration tests passed all 15 tests (0.10 seconds). Diff whitespace verification also passed. Existing datetime deprecation warnings remain.

## Limits and release conditions

- This introduces a database table. No operator database was migrated during verification.
- Historical fills have no marker establishing whether their legacy symbol-loss update succeeded. Do not bulk replay old fills or infer completion from daily accounting alone. The approved cutover described below preserves them without asserting historical completeness.
- Reconciliation still needs durable pending-fill completion and terminal-status protection. It is not changed by this patch, and may still discard a failed sink result.
- The existing flag clear/repair concurrency contract is not repaired here. Success on retry does not automatically clear the unhealthy flag.
- No full suite, CI, host integration, exchange order, power-loss durability or deployment proof. No configuration/account/collector changes.

Independent review is requested on the source diff and tests. Do not deploy or start reconciliation using this unaccepted prerequisite.

## Approval checkpoint

The user approved the treatment after the 15-test handoff. This is human acceptance of the bounded change, not permission to deploy, migrate historical accounts or bulk replay fills. The requested reviewer agent returned a usage-limit error without a review; no independent review result is claimed. Historical cutover remains a release blocker. Further accounting implementation must not depend on an inferred historical completion state.

## Approved cutover implementation

The user approved preserving existing counters and applying new completion markers only after a durable cutover. Before the first updated sink delivery is journaled, a serialized transaction snapshots existing canonical fill identities into a legacy exclusion table and records the activation time once. Existing markers from this treatment's earlier version are not excluded. Existing counters and lock expiry are untouched by activation. Legacy replays cannot increment losses or reset newer counters.

The boundary is local observation/journaling identity, not exchange execution time: a previously unseen late-arriving exchange fill is new evidence. Restart does not advance the boundary. Failed snapshot creation rolls back the activation record and prevents the delivery from reporting success. Direct counter application without activation is refused.

Deployment remains unauthorized. Stop all old-version writers before any approved deployment: an old writer racing across cutover cannot provide the new completion contract. Unjournaled legacy fills and pre-cutover incomplete loss updates are not reconstructed or declared repaired. This is an explicit preservation policy, not proof that legacy counters were correct.

Verification: 22 isolated tests passed, including legacy counter/lock preservation, old profit/loss replay, new loss progression, restart boundary preservation, rollback and missing-cutover refusal. Two logging tests now use temporary file databases rather than disconnected in-memory connections. No operator database was opened for mutation. Final cutover state: READY_FOR_INDEPENDENT_REVIEW; no completed independent review claimed.

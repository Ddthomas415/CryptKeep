# Dashboard Companion Boundary

## Scope

Continue intelligence restoration, not trading activation. Historical data and credentials are not changed. Authenticated dashboard companion requests cannot follow redirects; absent credentials return unavailable before transmission. Companion timeout is separately configurable with `CK_PHASE1_API_TIMEOUT_SECONDS`: default 30, valid finite range greater than zero through 90 seconds. This bounds socket operations, not total wall-clock response time. The disposable verifier bounds the dashboard subprocess to 90 seconds.

## Proof

- Dashboard HTTP and existing view/runtime tests: 87 passed.
- Separate reviewer HTTP tests: nine passed; ACCEPTED_WITH_RISK for this boundary.
- Verifier tests: seven passed, including repository interpreter/working directory and invalid-proof rejection. Separate review accepted disposable execution with risk.
- Reviewer caught a wrong interpreter path before execution; corrected to the repository parent and added regression coverage.
- Real dashboard-client proof is recorded in `companion_stack_verification_20261011_r4.json`: PASSED_LOCAL_STACK_CHECKS, source cited, execution disabled, provider fallback (backend deterministic explanation, not dashboard static fallback). Owned temporary stack removed. A passing client response is not actual browser-rendering proof.

## Remaining Boundaries

Persistent historical-volume startup requires credential reconciliation; disposable-stack success does not authorize replacing historical databases. Browser rendering, sustained operation, external deployment and profitable trading remain unverified. No campaign settings, live execution, accounts, schedules or persistent credentials changed.

# Companion local runtime checkpoint

Current-state update: see companion_persistent_check_20261011.md. Persistent services were subsequently observed running, existing database credentials verified, and actual dashboard-client access succeeded. The stopped-state and credential-unverified descriptions below are preserved historical checkpoints, not current claims. Browser rendering and sustained-operation proof remain outstanding.

## Accepted result

Separate GATE review: ACCEPTED_WITH_RISK for one disposable local runtime check, not production readiness.

Final receipt: companion_stack_verification_20261011_r3.json.
Status: PASSED_LOCAL_STACK_CHECKS; OWNED_STACK_REMOVED.

The rebuilt 12-service stack used fresh project-scoped volumes and credentials, random loopback ports, no existing .env, no OpenAI key and forced research-only settings. It fetched the authentic Bitcoin FAQ over the repaired public TLS path, parsed and stored it, retried the duplicate, retrieved it after restarting memory, rejected an unauthenticated explanation request, produced a source-linked fallback explanation and returned a nonempty execution-disabled chat response.

Document hash: a2abe8de6b956ab7a9a5dbb884106ab3f9020763c2c6994c7bb17bf817b6d6e6.
Published date stayed unknown; BTC was an explicit curated-source asset hint, not an inferred event or alpha claim.

## Corrections discovered by real integration

First run was INCOMPLETE: the verification tool reused a dynamic published port after restart. Refreshing the endpoint corrected the test. Initial commentary overstated restart retrieval; that claim was explicitly withdrawn before the rerun.

Second run was INCOMPLETE: actual orchestrator tool calls lacked service credentials, received 401 and substituted canned market/context samples. Corrected internal calls to authenticate only configured service origins, refuse redirects/proxies and transmit nothing when the token is absent. Removed fabricated fallback prices, narratives, regimes and evidence. Local focused regression: 34 passed. Separate reviewer reproduced 34 passes and accepted the bounded correction with risk. A partial editing error and stale fallback test assertions were corrected before the final tests; no failed result was treated as accepted evidence.

The original two runtime receipts are preserved. Smoke checker now authenticates without CLI credentials and refuses redirects, independently accepted with risk (9 tests). Verification-tool safety tests cover local Docker pinning, exclusive evidence output and owned cleanup.

## Preservation and cleanup

Docker Desktop was opened for this check and remains available. No historical container was started by the verification tool. Read-only pre/post listings showed the old stopped containers and prior volume names still present. This is not a content-checksum or old-data integrity proof. Independent reviewer confirmed no third-run project-labelled containers or volumes remained.

## Still not complete

- Persistent deployment against six-month-old volumes and their credentials is not reconciled or authorized by this disposable test.
- Actual dashboard/browser rendering and its authenticated request path have not been tested end to end. The root dashboard client imports successfully, but that is not operating proof.
- Full RSS/archive coverage, raw object-store readback, real TLS negative cases, sustained uptime and collector scheduling are not certified by this run.
- Code remains local; no commit, push, production deployment, paper/live campaign or account mutation occurred.

The root dashboard HTTP helper still uses default redirect handling with a service authorization header. This requires a bounded correction before authenticated dashboard activation; the smoke checker correction does not repair that separate caller.

Next accepted direction: finish the dashboard request boundary and its integration proof, then resolve persistent startup without discarding old memory. No profitability claim follows from restoration.

# Companion boundary correction batch

Role: ENGINEER. Risk: HIGH. No service activation or trading changes.

## Changes

- Shared public fetch validates all resolved addresses, pins the connection to a vetted IP, retains Host/TLS server name, rechecks redirects and disables environment proxies. Standard HTTP/HTTPS ports only; HTTPS cannot downgrade. Total timeout, redirect limit and raw-body size limit apply. Compression is explicitly refused to avoid unbounded decompression before the cap.
- Article, RSS and archive public reads use that helper; private service calls are separate. Archive parser/memory calls now forward service authorization and missing-token calls fail before submission. Its missing hmac import is repaired.
- Local Compose ports bind to loopback; repository mounts are read-only. Required database/object-store/service credentials have no Compose fallback. The shared application environment carries POSTGRES_PASSWORD consistently; Settings percent-encodes it into the owned copilot database DSN. This overrides DATABASE_URL when POSTGRES_PASSWORD is set. Existing .env was not edited. Existing persistent volumes require operator credential reconciliation; this is not a password rotation.
- Gateway/orchestrator require real FastAPI rather than fake substitutes.
- Retrieved document citations retain document ID and source URL. Missing market context returns unavailable rather than an invented price direction.

## Proof

Combined targeted regression before the last three route regressions: 102 passed. Final boundary/auth/config/gateway/orchestrator slice: 37 passed, 78 lifecycle warnings. Disposable PostgreSQL/Qdrant proof: 6 passed. The imported branch uses actual parser and memory ASGI routes, persists through an injected index outage, retries canonical data, reopens the index, and verifies the actual citation builder preserves URL/identity.

The initial database attempt failed on sandbox shared-memory restrictions; approved unsandboxed disposable run passed. A streaming-test fixture initially returned pre-consumed responses; fixed to supply real async streams and reran. Neither failure is hidden as a product pass.

## Limits and remaining completion criteria

Synthetic HTML, audit stubs, local Qdrant and substituted database wiring are explicitly test lanes. Actual TLS handshake/SNI behavior, authentic feed content, object storage, orchestrator HTTP integration, dashboard browser output, Docker build/lifespans and sustained runtime remain unverified. No full repository test run or full-stack acceptance is claimed. Mandatory dependencies need the isolated/full companion environment, not the trading environment.

Original restoration artifacts remain. Source is currently gitignored; local restoration is not publication. No live settings, accounts, credentials or running collectors were changed.

## Frozen file hashes

```text
d1126e7c156866b2406c4a36330f997dbb27fdcb3a2f067280ab8b0b915962b6  phase1_research_copilot/shared/public_fetch.py
63f987b33792b12e5e97da53e44f550d23f9c91943cc175ce61f650951bb9097  phase1_research_copilot/shared/config.py
602c4b874d41bf870e248921fb5b85c1a1bc40cfd99e23ffc84c016b186d550e  phase1_research_copilot/parser_normalizer/main.py
736fdabf6225b32b6a7a34eae26c01e2209b2b4bfabba80c8ea0edb4ea64ad2d  phase1_research_copilot/news_ingestion/main.py
7c3f666bb39f1251e5ceea2fd92c7343266224005b8aaa12944f48364d69b4f1  phase1_research_copilot/archive_lookup/main.py
d2f7df95998a1748c56973d798a63210e4e1db9b9f73e07e9fcfa03af9044886  phase1_research_copilot/gateway/main.py
c6895922a6e3f6ad85ec269f64436cb2f83eed990345745dd9b572dcfe5a4440  phase1_research_copilot/orchestrator/main.py
bd61e7fd7cd755594d6e56bcdca2e91ef3201074bf33e9851ba399e06aa3e4d5  phase1_research_copilot/docker-compose.yml
b33cc40d1341fde732667a656984846431937dbb3c41675a4d59ef28113f6f11  tests/test_companion_public_fetch.py
3be7eebe927f56f239b3bec056583df31145b790bcf605a0d09c86be0beabd45  tests/test_companion_restored_routes.py
3bd1fe9229b68c3bb76a8ba122a3fcedadc39c4cea6dfd0366d37b9abe0a486f  tests/test_companion_memory_persistence.py
```

Acceptance: ACCEPTED_WITH_RISK for boundary corrections. Separate reviewer reran a four-file slice (36 passed, 78 warnings); the engineer's five-file slice includes the additional configuration test (37 passed). Separate citation/proof review: 9 independently passed. None approves full-stack readiness.

# Persistent Companion Check

## SHOWN

Read-only inspection on October 11 found the historical companion services already running. PostgreSQL and MinIO started at 18:45 UTC; memory and orchestrator followed at 18:46 UTC. This check did not start, restart or recreate them. The initiating actor was not established.

The running services use the historical named PostgreSQL and MinIO volumes. Inspected published ports bind to localhost only. Memory health returned database, Qdrant and MinIO healthy; orchestrator health returned `no_trading: true`, `openai_enabled: false`.

Credential comparison disclosed no secret values. Local service token and object-store credentials match the running memory and orchestrator containers. The existing DATABASE_URL password matches the database container's stored password after URL decoding. Authentication to PostgreSQL succeeded with default_transaction_read_only enabled. Documents: 55; rows with a raw object key: 55. This is not object-content readback or historical-integrity proof.

The actual repository dashboard client, supplied existing credentials only in its temporary process environment, received six evidence entries from the running orchestrator. Provider was backend `fallback`, not `dashboard_fallback`; execution remained disabled. No configuration file or credential was modified.

## Corrections And Limits

Earlier stopped-service and unresolved-credential checkpoints were accurate at their inspection times but no longer describe current runtime. The first read-only query used a nonexistent column; inspected the schema and reran using raw_object_key. No database mutation resulted. The root runtime lacked dotenv; retried with the existing isolated dependency environment.

The existing .env still has no standalone POSTGRES_PASSWORD variable: do not run the new Compose file blindly or assume it can recreate the running stack from that file alone. Existing DATABASE_URL supplies the verified password; no credential reset is required. This check does not authorize destructive recreation.

Dashboard boundary regression: 88 passed, including the other session's environment-proxy refusal fix. Browser rendering, sustained uptime, automatic restart and external deployment remain unverified. No live or paper trading changes, collectors restarted, account mutation, commits or pushes.

Acceptance: runtime observations SHOWN by main-agent probes; separate reviewer did not repeat those runtime probes. Proxy change independently ACCEPTED_WITH_RISK: ten focused tests and90 expanded dashboard tests passed. No actionable findings; total-request deadline and actual browser rendering remain outside acceptance.

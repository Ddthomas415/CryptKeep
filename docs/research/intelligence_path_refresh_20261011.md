# Intelligence Path Refresh

Role: AUDITOR. Scope: local caller-to-consumer trace, not a deployment audit.

| Boundary | Current evidence | State |
|---|---|---|
| Dashboard explanation caller | market_view.get_research_explain requests /api/v1/research/explain, then external /v1/explain, then explicitly labeled static fallback | SHOWN client exists |
| Default local backend | Read-only TCP probes of this shell's configured/default localhost ports8000 and8002 both refused connection | SHOWN unavailable from this environment; dashboard process environment unverified |
| Curated feed ingestion | research/companion_recovery/news_ingestion.py forwards parser/storage requests; explicitly not wired into startup | SHOWN isolated recovery, not operating pipeline |
| Durable memory/retrieval | Recovered memory_retrieval.py retains SQL/vector/object-store dependencies and historical shared imports; prior disposable persistence proof exists | SHOWN candidate and bounded prior proof; deployed service chain unverified |
| Cited dashboard answer | Mock/fallback path exists; no active service response verified here | INCOMPLETE end-to-end operating proof |

Verification: ./.venv/bin/python -B -m pytest -q tests/test_companion_news_recovery.py tests/test_companion_memory_recovery.py tests/test_dashboard_view_data.py -k 'companion or explain':42passed,55deselected,0.59s. These are narrow local tests, not authentic feed ingestion or deployment proof.

This confirms the existing September29 disconnection record, not a new defect discovery. Do not rebuild repaired date/indexing logic or infer absent external deployment from closed local ports. Next material fact: whether a separate companion backend is already deployed and intended for this dashboard. Identify that target before choosing restoration versus reconnection. No runtime, strategy or service changes made. Audit INCOMPLETE pending external-target evidence.

## Deployment lookup

User requested locating the backend rather than assuming its absence. Historical host checkpoint identifies cryptkeep@100.86.128.9 via Tailscale SSH. A read-only service-port/unit/folder inspection was attempted but Tailscale requires an additional human security check; no remote command output was obtained. Host deployment remains UNVERIFIED, not absent.

Local phase1_research_copilot exists only as empty service directories plus an old .env. Only URL host/port fields were inspected: orchestrator:8002, parser-normalizer:8006, memory-retrieval:8007, risk-stub:8008 and audit-log:8009. These are container DNS names, not evidence of live remote deployment. No credentials were displayed. No service started, authentication reset or trust bypass attempted.

Security check subsequently completed and remote inspection returned. SHOWN: no listeners on ports8000/8002/8006/8007/8008/8009; no companion/orchestrator/news-ingestion/memory-retrieval systemd service names. Existing cbp-crypto-edge-collector.service is running. Docker command unavailable for this account; container state cannot be comprehensively ruled out. Directory search under /home/cryptkeep,/opt,/srv to depth4 found only /srv/cryptkeep/app/services/ai_copilot, not the historical companion deployment. Thus no operating companion was found on the documented host within this scope; unrelated hosts and alternate ports remain UNVERIFIED.

Recommendation: restore a bounded local parsed-document-to-durable-retrieval slice using recovered components, with no new background service or execution authority. Reuse prior timestamp/indexing repairs; prove real transport and storage boundaries before dashboard activation. Do not treat the separate services/ai_copilot package as the missing historical backend.

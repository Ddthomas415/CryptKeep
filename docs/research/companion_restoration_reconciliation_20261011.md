# Companion restoration reconciliation

Role: AUDITOR. Scope: optional inactive source restoration, not deployment.

## Shown

- The CLOUD full restoration and Codex three-module restoration overlap in the same folder.
- Comparing news_ingestion/main.py and memory_retrieval/main.py against research/companion_recovery shows only an extra trailing blank line. No competing implementation was substituted.
- Originals retained by the restoration remain on disk. No existing .env was overwritten by this reconciliation.
- Isolated Python route/recovery/config/security slice: 56 passed.
- Gateway/orchestrator/tool/LLM/smoke slice: 31 passed.
- Optional-repository dependency tests: 2 passed.
- Combined count across these disjoint selections: 89 passed. This is not a full repository suite.
- The first broader run failed collection because the isolated environment lacked PyYAML. Installing PyYAML 6.0.2 resolved that dependency; the affected tests were rerun.

Interpreter: /private/tmp/cryptkeep-intelligence-proof-20261011/bin/python.
Route tests do not run service lifespans or background ingestion.

## Activation risks

Historical gateway and orchestrator authentication helpers return without checking a token when passed an unresolved FastAPI Header default. Existing source-text tests do not establish authenticated runtime behavior. Their missing-FastAPI compatibility substitutes also do not prove a usable server.

Remote URL fetching, service-to-service integration, object storage, real feed ingestion, dashboard citations and deployment behavior remain unverified here. Prior disposable database proof is not proof of this entire restored stack.

The source is gitignored: it is present locally, not thereby published, committed or deployable elsewhere.

## Disposition

Preserve the reconciled tree and originals. Do not activate on the strength of unit results. Separate independent review has been requested. Correct confirmed activation blockers before a service-start decision; preserve research capabilities rather than deleting them.

Acceptance: READY_FOR_INDEPENDENT_REVIEW.

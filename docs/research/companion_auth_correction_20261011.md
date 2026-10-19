# Companion authentication correction

Scope: gateway and orchestrator authentication only. No service activation.

The historical helpers accepted an unresolved FastAPI Header object without checking configuration or credentials. Both now require a configured token and a string Bearer credential. Non-string values, missing headers and wrong tokens are rejected; absent configuration returns 503. Valid fixture credentials remain accepted.

Existing direct-call tests now pass explicit fixture credentials instead of relying on the bypass. They import the real HTTP client before their legacy fallback stubs can pollute the test process.

Verification (disposable Python, no lifespan startup):

```sh
/private/tmp/cryptkeep-intelligence-proof-20261011/bin/python -B -m pytest -q tests/test_companion_restored_routes.py tests/test_phase1_research_copilot_gateway.py tests/test_phase1_research_copilot_orchestrator.py
```

Result: 16 passed, 48 lifecycle deprecation warnings. Initial combined run had 8 errors caused by global HTTP-client test stubs; corrected imports and reran.

This does not repair browser-chat credential delivery, deployment permissions, URL-fetch restrictions or missing-framework compatibility behavior. No deployment, trading or account changes. Those remain separate activation blockers.

Independent reviewer reproduced the auth slice plus shared-token config test: 17 passed, 48 warnings. No blockers in this bounded correction.

Acceptance: ACCEPTED_WITH_RISK for this correction only; full restoration remains INCOMPLETE.

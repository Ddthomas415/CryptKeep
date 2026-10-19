# Companion browser access correction

The browser chat now uses /v1/browser/chat with a separate BROWSER_CHAT_TOKEN. It defaults to disabled. SERVICE_TOKEN remains server-side; both tokens must be configured and must differ. The existing service endpoint retains service authentication.

The page accepts the browser credential in a password field, clears that field before sending, and uses an Authorization header. Neither credential is embedded into HTML, URLs, cookies or browser storage by this implementation. Browser users can submit research chat only; no trading route was added.

No credential has been created and no .env has been changed. Before activation, use HTTPS (or an explicitly reviewed local-only access boundary), restrict who receives the browser credential, and complete deployment/URL-fetch review. The browser token is a shared credential, not per-user identity, revocation or rate limiting. Trusted page origin remains necessary.

Local verification: disposable Python ran tests/test_companion_restored_routes.py, tests/test_phase1_research_copilot_gateway.py and tests/test_phase1_shared_config_service_token.py: 16 passed, 60 lifecycle deprecation warnings. Positive gateway delegation is stubbed; this is not real downstream service or browser-engine proof.

Independent review caught a missing network/JSON failure handler. Corrected it: status checked before parsing and failures are displayed. Reviewer reran the 16-test slice and accepted this bounded change with risk. Browser-engine execution remains unverified.

Acceptance: ACCEPTED_WITH_RISK for browser auth/UI only. Services remain inactive.

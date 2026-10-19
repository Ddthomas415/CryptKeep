# Actual Browser Check

## SHOWN

The running gateway page at http://127.0.0.1:8001 rendered in the Codex in-app browser. Visible research-only and execution-disabled notices, labelled password input and Ask Copilot control were present. No real credential was entered.

Clicking with no token showed "Enter your browser access token." Entering an intentionally invalid, nonsecret QA token and clicking showed HTTP503 configuration refusal; the password field cleared. Browser chat is unconfigured on this deployment, not a successful authenticated browser conversation. Existing backend/dashboard-client access remains a separate verified lane.

## Correction

Both failure paths left the answer-metadata panel saying Loading. Corrected source to show terminal metadata and reasoning for missing credentials, refused responses and transport failures. Authentication, credentials and service settings were not changed. Thirteen restored-route tests passed with78 lifecycle deprecation warnings. This source correction has not been deployed or reverified in the running browser.

## Limits

Successful browser chat requires an explicitly configured separate browser credential; never expose the internal service token in this form. No credential provision, persistent service restart, trading or account mutation performed. Browser happy path, sustained operation and collector freshness are not proved by this check. The page showed a collector-dead warning; that is not independently confirmed process status and no collector was restarted.

Acceptance: separate GATE ACCEPTED_WITH_RISK for bounded source correction; independently13tests passed. Tests inspect HTML source, not executed corrected browser states. Earlier rendered failure behavior SHOWN by main agent only. Correction not deployed.

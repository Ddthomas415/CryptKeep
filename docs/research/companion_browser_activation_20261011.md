# Local Browser Activation

Operator explicitly authorized localhost-only browser chat with a separate credential. No trading activation.

The one-shot helper builds a uniquely named gateway image, preserving the previous image, and recreates only the gateway on its existing external network. Existing mounts are copied from the running container. It supplies the complete previous environment plus the separate browser token, without importing or merging .env. Literal dollar characters are escaped for Compose. Exact deployed environment is checked. On failure, the prior image and full environment are restored, with an explicitly empty browser token when previously absent.

Private credential artifact: phase1_research_copilot/.browser-access-token, exclusive-created with mode0600. Deployment configuration: .browser-compose-override.json, also0600; it contains private environment values and must never be shared. Both are excluded from Docker build by .browser* and the sidecar is Git-ignored. Credentials are never printed or embedded in HTML.

Recovery: this is intentionally one-shot. Never delete the private artifacts simply to rerun it. Restart the existing gateway container to retain its saved credential and image; do not use ordinary root Compose commands to recreate it. Recreating from the private standalone configuration is gateway-only and must use the existing project name phase1_research_copilot with --no-deps. It has an external existing network, no other services or persistent volume definitions. A failed activation restores the previous image and browser setting; the retained token artifact alone does not prove activation.

No successful activation is claimed until the execution receipt is recorded. Authentication checks require401 without a token and a source-backed execution-disabled response with the separate browser token, not an upstream failure fallback. Actual browser interaction is a separate proof lane.

## Execution Result

SHOWN: helper exited0, VERIFIED_LOCAL_BROWSER_ROUTE. Token file mode0600; unauthenticated request401; authenticated browser route returned nonempty source-backed response with execution disabled and no upstream failure fallback. No real credential was displayed in tool output or entered into browser automation.

The actual deployed page rendered. Missing credentials showed terminal not-sent metadata; an invalid nonsecret QA credential showed401 and terminal refused metadata. The field cleared. These states no longer remain Loading. Successful authenticated UI interaction is not claimed; successful credential-authenticated HTTP route is the positive proof lane.

Only gateway recreation was requested. Existing databases and other service settings were not changed. Independent runtime disposition pending; sustained uptime remains unverified.

Separate GATE: ACCEPTED_WITH_RISK, bounded localhost research chat. Independently inspected healthy gateway, localhost-only binding, no-trading setting, distinct browser/internal credentials, token-file/runtime equality, readonly mount and0600owner-only build-excluded credential artifacts. Successful request/browser-error observations were not repeated by reviewer. Main-agent pre/post timestamps for database, MinIO, memory and orchestrator remained identical; only gateway start changed. Container inspection confirmed neither private artifact exists in /app. Authenticated browser UI happy path and sustained uptime remain unverified.

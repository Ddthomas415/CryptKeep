# Actual controller and installed-source compatibility review

Date: 2026-10-16, evidence recorded 15:55 UTC (11:55 New York).
Active role: AUDITOR. Operational disposition: INCOMPLETE.
Runtime authorization: NOT GRANTED. No implementation or startup authorized.

## Conclusion

The reviewed evidence does not support authorizing the proposed single retry.
No compliant existing-stack controller was identified in the searched locations.
Installed container source contains the retry and startup behaviors previously
identified in local source. They must not be described as merely hypothetical
local-code differences. Actual effective configuration remains unverified.

This review preserves acceptance of the bounded offline guard repair and keeps
WP4 item1 closed. It does not reject the isolated verifier for its own separate
purpose, remove intelligence capability, or change the proposed retry scope.

## Findings Against The Four Requested Areas

### 1. Retry And Recipient Behavior

SHOWN: five selected application files were read through the archive API from
the existing STOPPED containers, parsed without importing/executing them, and
hashed. All five match the inspected local source exactly. The receipt records
full container IDs, image IDs and source hashes:
`docs/review_artifacts/companion_compatibility_20261016.json`.

SHOWN in installed `/app/shared/tools.py`:
- `_request_json` calls `retry_async(..., retries=1)` at line181. The matching
  installed retry helper permits another downstream call after failure.
- Fixed origins for market-data:8003, news-ingestion:8004 and archive-lookup:8005
  are outside the permitted seven recipients. `get_operations_summary` also
  includes a settings-derived parser origin. Calls use the service token when
  configured. A swallowed connection error is still an attempted request.
- Matching installed orchestrator source calls core tools in the deterministic
  explanation path. Starting only seven containers does not constrain fan-out.

This establishes incompatible source policies for the strict retry proposal,
not that a retry or out-of-scope request happened during this read-only audit.
Effective settings, runtime monkeypatches/import paths, configured parser URL,
proxy behavior and SDK retry policies were not inspected. No environment or
credential-value extraction was used to fill these gaps.

### 2. Startup Side Effects

SHOWN in installed memory source: startup invokes `_ensure_bucket` and
`_ensure_qdrant_collection`; their bodies can create missing resources. The
three named data-volume mounts and image IDs match the previous operation
record. This does not establish namespace existence, schema compatibility or
absence of other startup effects. No storage service was started or queried.

UNVERIFIED: existing bucket/collection/schema, current PG_VERSION/data contents,
entrypoint side effects, image-layer versus writable-layer source provenance,
and exact effective configuration. Do not report that startup cannot create,
migrate or ingest merely because the source files or volume names match.

### 3. Actual Controller Enforcement

Separate AUDITOR inspected candidate scripts and searched filenames and text
under scripts/research and docs/review_artifacts, including hidden/ignored text.
Parent additionally searched selected companion/reconnect/retry/probe/controller
Python names in /private/tmp. Compressed/binary bundles and other workspaces
were not exhaustively searched. No compliant existing-stack runner was found
within those bounds; this is not a claim that no such file exists anywhere.

SHOWN: `scripts/research/verify_companion_stack.py` is an isolated-stack tool,
not the specified controller. It builds and starts a new Compose project,
ingests/retries an article, restarts memory, polls health, sends multiple
explanation/chat requests, and removes its owned volumes. Its 600s build
timeout is not a 600s total deadline; the dashboard subprocess permits90s,
and later cleanup has its own120s. It lacks the required seven-ID baseline,
StartedAt ownership ledger and global remaining-budget enforcement.

`enable_companion_browser.py` is also not an eligible substitute: it handles
credential/configuration artifacts and rebuilds/recreates gateway components.
It was inspected as source only; no credential artifact was opened.

Disposition: those candidates are REJECTED FOR THIS OPERATION, not deleted,
retired, run, or judged against an unrelated purpose. The specified controller
remains missing from the located evidence. A specification cannot supply its
runtime enforcement or its tests.

### 4. Evidence Acceptance And Primary-Route Isolation

SHOWN: the actual dashboard calls its legacy-primary facade first, then the
companion route through the existing normalizer/asset guard. The located
verifier points the primary URL at loopback port1; that still attempts network
access. The proposed suppression has not been implemented in a located harness.

A future disposable probe must suppress ONLY the primary facade before
dispatch while preserving the real companion transport, normalizer, guard and
provider/fallback processing. Returning a canned normalized response is not
equivalent and cannot establish transport or evidence provenance.

Other gaps in the located verifier:
- URL presence and provider exclusions do not prove persisted document identity,
  question relevance, execution.enabled=false or a NO_TRADING risk posture.
- Dashboard normalization can synthesize missing provider metadata; service
  provenance must be checked in the captured transport envelope, not inferred
  solely from the normalized default label.
- Numeric document IDs are not canonicalized to strings by the existing
  diagnostic hash loop. A string evidence ID is not a substitute for matching
  the actual persisted document_id and archive-view mapping.
- Dashboard diagnostics are allowlisted, but the isolated tool's other failure
  receipts retain Compose output/service logs after replacing only two generated
  secrets. That is not the strict new secret-free phase-receipt contract.

UNVERIFIED: real retrieval, citation identity, topical support, causation,
operational safety and profitability. No source proof establishes any of them.

## State And Method Boundaries

SHOWN during this review: all19 containers were exited, including all seven
targets; target restart counts were0 and restart policies no. Seven image IDs
match the prior operation record. Named data-volume destinations were recorded.
These are point-in-time observations, not a preflight reserved for a later run.

Final metadata comparison at15:59:27UTC (11:59:27 New York) confirmed all seven
target IDs, image IDs, exited states, restart counts and policies still matched
the initial audit receipt. The three named volumes use driver local and report
creation time2026-03-12T17:42:05Z. Neither fact proves namespace/schema integrity.

VERIFIED_ENV: native arm64 Docker CLI, explicitly pinned local daemon and fresh
empty temporary CLI configuration, without using the user's Docker credential
configuration. Only metadata and the five whitelisted source archives were
requested. No docker exec, service HTTP, credentials/.env/environment extraction,
start/stop/restart, image pull/build, migration, ingestion or trading action.
No production/test source or retry specification was edited in this review.

Audit limitations/errors retained:
- Initial sandbox socket access was denied; the same allowlisted read-only
  inventory succeeded with approved socket access. No authentication repair.
- An initial metadata template assumed every mount had Name and failed for two
  bind-mounted targets. The corrected optional-mount query returned all seven.
  This was a verifier-template error, not a container or service failure.
- No pytest, actual request or cancellation/cleanup exercise was run.

## Independent Installed-Source Confirmation

After the controller-source review, the separate AUDITOR independently read
two files from the stopped containers via the same pinned local archive API.
It verified the exact hashes against both the parent's receipt and local code:
tools.py, 18,576 bytes, bbf00f30...; memory main.py, 15,813 bytes, c9efd5ff....
It confirmed the retries=1 call site, fixed market/news/archive origins and
conditional bucket/collection creation directly at the copied-file line numbers.
Both containers remained exited with unchanged IDs/images before and after.
No credential/configuration access, exec, HTTP, startup, tests or edits occurred.

Its two-file stage did not independently inspect the retry helper or incoming
orchestrator dispatch; the parent inspected matching installed copies for those
claims. Effective settings, namespaces and immutable-image versus writable-layer
provenance remain UNVERIFIED. Independent disposition: INCOMPLETE, compatibility
conditions substantiated, not operational compliance.

## Recommended Next Scope, Not Authorized Implementation

One bounded offline implementation proposal should cover the missing
existing-stack controller and the demonstrated retry/recipient compatibility
gaps, with synthetic ownership/deadline/secret-handling tests and independent
review. Keep it separate from permission to deploy, change containers, use
credentials or attempt the query. Do not repurpose the isolated-stack lifecycle
tool or silently expand the seven-service scope to make the test run.

Until a reviewed controller and compatible installed behavior are established,
the runtime objective remains INCOMPLETE. This review does not request runtime
authorization or claim a cause for the original failed explanation request.

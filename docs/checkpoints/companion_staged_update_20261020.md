# Staged Replacement Integration

Date: 2026-10-20. Active role: ENGINEER. Risk: HIGH.
Offline implementation: ACCEPTED_WITH_RISK by separate GATE. Runtime: INCOMPLETE.

## Selected Contract

The operator selected: prepare stopped replacements, independently review their
actual IDs, then begin a separately bounded cutover. This explicitly replaces the
earlier requirement that preparation, human review and cutover share one clock.
It does not authorize either operational phase, credential use or trading.

The existing installer accepts opt-in `companion-staged-update-v5`. Existing
profiles retain their contracts. The CLI still refuses operational application
of the running-storage profiles; the new methods are an offline-tested API, not
an approved command or a claim that a deployment packet exists.

## Preparation

`Installer.prepare_staged` has 300 seconds total, reserving 120 for cleanup.
It rechecks all seven original snapshots, builds the four source-only images,
and creates four never-started replacements with unique temporary names and
unique staging aliases on the existing bound network. It does not stop, rename,
disconnect or start an original. Published-port configuration is retained but
cannot bind ports while containers remain unstarted. Build images and stopped
container metadata are persistent side effects if this phase is later authorized.

The public evidence contains actual replacement IDs, images and configuration
snapshots bound to the exact original manifest SHA256 and attempt. Its state is
READY_FOR_INDEPENDENT_REVIEW, never generated approval. The existing independent
runtime pins must then be reviewed against the real IDs, intended final aliases,
source/SDK policy and recipient bindings. Do not print or persist environment
values; the backend compares them transiently when checking the replacement.

Unknown creation outcomes are not adopted as owned resources. Cleanup handles
only acknowledged, unchanged, never-started objects. Failed acknowledgments or
drift remain unresolved rather than being declared clean.

## Separate Cutover

`ReviewedPreparation.load` requires an externally supplied hash for a separate
review record that accepts the exact preparation evidence and original manifest.
It rejects duplicate IDs, baseline IDs, wrong attempts, started objects and invalid
configuration evidence. This is a trust-input boundary, not proof of reviewer
independence or a cryptographic signature. No tool generates that approval.

Cutover has its own 600-second deadline with 180 seconds reserved for recovery.
The review interval is outside both live-operation clocks. Cutover never builds
or recreates replacements: the independently reviewed IDs must still be present
and unchanged. Engine/source prerequisites are revalidated after the review
interval without rebuilding. Source/environment, staged policy and persistent-namespace checks
precede interruption. Recipient/final-alias checks are not waived: after activation,
pre-start compatibility checks configured-only attachments against a freshly
verified daemon network name/ID map. Only never-started created applications may
have blank IDs, and they must have no endpoint/IP evidence. All existing alias
exclusivity, port, volume and DNS checks remain. After all four starts, a separate
unprojected recipient check must show real attachments before any health/query
HTTP. Configuration proof is never reported as actual connectivity. Storage
lifecycle remains out of scope.

Only then does the existing original-application quiesce/rollback path run.
Replacements retain their reviewed IDs as aliases and names move to the final
configuration. Health, one dashboard query, diagnostics before assertions, and
traceable evidence remain separate gates in the existing runtime path.

After interruption, failure consumes the preparation review. Recovery may delete
unchanged owned replacements and restore the original applications; it does not
silently recreate reviewed IDs. A preflight refusal does not certify that the
same evidence is reusable. Any later attempt needs fresh state validation and
separate operational authority. API one-use guards are in-memory only; durable
locking/authorization must be supplied by a separately reviewed operational
entry point. No new executable operational entry point is provided here.

## Verification and Limits

SHOWN: initial four-file synthetic slice passed 218 tests in 1.06 seconds. This
includes the staged state machine and earlier installer regressions, not the full
suite. Final combined verification and separate GATE disposition will be added
below without replacing this intermediate result.

UNVERIFIED: current engine pin compatibility, actual source-only build,
installed-image/SDK behavior, stopped-container metadata/alias transitions,
native rollback, namespace checks and real cited explanations. Synthetic proof
does not establish these. No current service-health refresh is claimed.

No Docker/socket calls, HTTP requests, credentials, image builds, container or
volume lifecycle, scheduler, account, migration, new research experiment or
trading action occurred in this implementation scope. Preserve all previous
receipts and original source manifests. No profitability claim follows.

## Frozen Handoff After Reported Laptop Restart

SHOWN: final isolated twelve-file synthetic slice755passed4.21seconds, exit0;
`git diff --check` passed. Seven source/test hashes and the exact command are in
`../review_artifacts/companion_continuation_20261020/staged_update_verification.json`.
The reviewer invocation returned a usage-limit error without a disposition.
Implementation remains READY_FOR_INDEPENDENT_REVIEW, not ACCEPTED. Do not repeat
the implementation or turn earlier component acceptance into v5 approval.

Following the operator's restart report, read-only checks confirmed frozen hashes
unchanged and seven named research targets running. Collector PIDs exist, but
status timestamps were about100minutes old; active collection was not proved.
Exposed host boot time remained October12, so a full October20 OS restart was
not independently confirmed. Docker signature passed unrestricted read-only
verification; its sandbox failure is not evidence requiring repair. No service
or collector was restarted. Observations and limits are saved in
`../review_artifacts/companion_continuation_20261020/restart_check_20261020.json`.

## Resumed Independent Review

The resumed GATE independently reproduced755passed6.67seconds but REJECTED the
v5 composition on one new synthetic finding: configured-only blank NetworkID on
never-started replacements failed the raw recipient gate after original
interruption. Preserve `staged_update_review_r1.json`; green regressions were not
acceptance. The bounded correction keeps default compatibility strict, verifies
the configured map through a narrowly allowlisted read-only network inspect, and
requires actual unprojected recipient checks after startup before HTTP.
Cross-component regression and corrected independent re-review remain pending.

Corrected final frozen slice:912passed6.86seconds across15 focused files, diff-check
clean. Exact command and11 source/test hashes are saved in
`../review_artifacts/companion_continuation_20261020/staged_update_verification_v2.json`.
The cross-component fixture uses real installer post-activation verification and
real adapter with synthetic native blank-ID metadata, not independently canned
success flags. It also proves missing actual attachment fails before health/query.
The transport accepts only fixed-format read-only network inspection of1-7 unique
full IDs; negative cases and two v5 CLI refusal tests pass. No actual native call
was made. Corrected implementation READY_FOR_INDEPENDENT_REVIEW; separate GATE
disposition pending. Earlier results/rejection remain preserved.

SHOWN read-only continuation: both collectors subsequently refreshed without a
restart by this thread. Context capture succeeded22:24:54UTC, loops2072/writes2070;
paper heartbeat22:24:11UTC, idle/waiting_for_next_day, completed day2026-10-20.
This supersedes the earlier stale-status concern for those observations only.

## Final Independent Disposition

Separate GATE Hegel accepted the frozen offline v5 implementation and bounded P2
correction ACCEPTED_WITH_RISK, reproduced912passed6.57seconds, verified all11hashes
and clean diff-check. No remaining blocker found in that bounded review. Receipt:
`../review_artifacts/companion_continuation_20261020/staged_update_review_r2.json`.
Do not rerun this implementation/review without changed or contradictory evidence.

This closes offline staged identity-binding and post-activation composition proof,
not service restoration. The preparation-only operational entry point/packet,
fresh native compatibility, actual stopped replacement creation, independent
review of their real IDs, separately authorized cutover and real cited explanation
remain outstanding. Both CLI running-profile apply refusals remain. No service,
container, volume, credential, scheduler, account or trading change was performed.

Subsequent preparation-only command implementation and bounded review are now
recorded in `companion_preparation_entrypoint_20261020.md`. The existing installer
CLI v4/v5 apply refusal is unchanged; the separate command defaults to inert
validation and has no cutover/start/query option. Actual fresh input packet,
preparation authority and native verification remain outstanding.

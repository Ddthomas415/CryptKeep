# Restricted S3 Single-Attempt Repair

2026-10-21. Active role ENGINEER. Risk HIGH: restricted request-recipient/replay
policy. Implementation READY_FOR_INDEPENDENT_REVIEW. No operational change.

## Demonstrated Defect and Chosen Boundary

The actual captured Botocore sources establish a region-redirect handler outside
the standard max-attempt condition. See sdk_actual_policy_finding.json and the
unchanged installed_facts_capture source copies. That is conditional source
behavior, not an observed redirect or a cause assigned to the earlier query failure.

The restricted S3 client now bypasses its endpoint's _needs_retry decision method
using an instance-local always-False function. In the pinned captured request loop,
that prevents all retry-event dispatch, including region rediscovery's nested
HeadBucket, rather than relying on an event handler's None result as a veto.
No SDK class/global state or ordinary unrestricted client is modified.

Private SDK hook use is intentional and version-specific. The captured call site
is its compatibility evidence, not a promise about all future Botocore releases.
Before publishing the restricted cache, require a callable hook, assign the guard
and check exact identity on readback. Failure closes the candidate best-effort,
raises only restricted_s3_retry_control_unavailable and leaves the cache empty;
there is no unrestricted fallback. Existing successful response/error propagation
is retained at the tested request-loop boundary.

## Changed Artifacts

- phase1_research_copilot/memory_retrieval/main.py: local restricted guard and cache
  publication ordering only. Prior hash35fc51165e44dba1ab8d28e783285f51f392b01f814096f3950ce720995504a3;
  current c1eaae5a5e1712ad926f556fdaf3195442a2b6e354059542748a429945a36228.
- tests/test_companion_s3_single_attempt.py:16 focused synthetic cases; hash
  e63713b03cf2699661ecb57eded33aad145a92b5796fe6873a7704bed244cef7.
- tests/test_companion_probe_policy.py: existing synthetic S3 constructors now
  provide the required endpoint hook; no assertion removed. Hash
  5f5e0f26eb0b304c23f615346e45c7405f164485da5bcf0d9c9e295f5dbc498e.
- restricted_s3_single_attempt.patch in the October21 review folder preserves
  the exact source-only delta against the captured old source. The recovered
  phase1 source is Git-ignored, so git diff alone omits it; explicit diff/hash
  and this patch are required evidence. No Git tracking changes were made.

## Focused Verification

VERIFIED_ENV for isolated host synthetic tests only:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider \
 -q --tb=short tests/test_companion_s3_single_attempt.py tests/test_companion_probe_policy.py
```

SHOWN80passed2.80s,158 FastAPI startup-event deprecation warnings. Earlier draft
had a test decorator typo and synthetic object-only S3 fixtures; corrected those
fixtures, without relaxing runtime checks. No full-suite result is claimed.

Tests compile only hash-checked AST method bodies from the captured Endpoint and
S3RegionRedirector, with synthetic dependencies/settings/storage and blocked
network sockets. This is not full SDK import/initialization or installed runtime
execution. The unchanged-method control demonstrates2 sends plus1 nested HEAD;
the repaired cases verify1 send,0 retry-event dispatch,0 nested HEAD for redirects,
server errors and a200 error-shaped response. Transport error identity, success,
normal-client isolation, unsupported/ignored setters and failed-cache publication
are covered. Existing probe/read-only endpoint guards remain exercised.

## Preserved Operational Boundary

All captured93 files, previous manifests/reviews and existing container IDs/images
remain unchanged. The stopped memory image still contains the OLD source; this
repair is not deployed. Old source manifests no longer match the edited local
main.py and must not be silently rewritten or treated as approval of these bytes.
After independent review, prepare the updated stopped application from newly
reviewed source bindings before any separately authorized cutover. Do not rerun
the consumed capture/preparation or mutate reviewed containers in place.

No Docker, service, credential, database, scheduler, account, experiment or trading
operation ran. Whole startup/import policy and one real dashboard explanation
remain INCOMPLETE. The narrow offline code review cannot approve those outcomes.

## Independent Disposition

Separate GATE ACCEPTED_WITH_RISK this exact offline repair. Receipt:
docs/review_artifacts/companion_continuation_20261021/companion_s3_single_attempt_review_20261021.json.
No findings; all three frozen source/test hashes and exact patch body match.
Independent same focused command:80passed2.73s,158deprecation warnings, exit0.
The reviewer confirmed private hook/cache ordering, error-response cases,
unrestricted isolation and explicit captured-method rather than native proof.

This closes the bounded offline repair, not the installed policy or service.
Next is a fresh source-binding/preparation plan for the updated stopped memory
application, preserving the other reviewed subjects and all prior evidence where
supported. Do not mutate current prepared containers, silently refresh old hashes
or rerun a consumed attempt. Builds/replacement IDs/startup/cutover require their
separately reviewed operational scope. No further operation was performed.

# V6d Fixed Handoff

Role: ENGINEER. Risk: HIGH. State: READY_FOR_INDEPENDENT_REVIEW.
Accepted record bindings and focused tests complete; runtime remains INCOMPLETE.

## Implementation Boundary

Separate execute_reviewed_v6d.py preserves the reviewed V6c helpers, validated,
execute and validate_only functions exactly after v6c/V6c label substitution.
No old wrapper, old inputs() or old execute() is invoked. Generic JSON/argv,
strict token parser, exact-original source format and anonymous-pipe helpers
remain bound to the unchanged reviewed helper SHA
5c319350681e2fb4fdac363e29b829947e0348678fdcc8ecabc84820713adf12.

The four record constants bind the new independently accepted V6d packet,
scope, runtime and default inert receipt. Initial UNBOUND draft values were
replaced only after acceptance/default verification. Old consumed V6c
records, removed IDs and preparation reservation remain untouched.

Default validation has no native, token or reservation authority. The separate
--execute-once branch is not permission: future execution requires the explicit
operator decision on this exact input set. Input drift must refuse before any
credential source. The existing controller's shared lock and exclusive cutover
reservation remain the authority for once-only mutation, not advisory lexists.

## Future Authorized Effects And Limits

Only if separately approved: private reuse of the existing original internal
service token, graceful interruption of four original research apps, activation
and startup of the four accepted prepared replacements, existing restricted
checks and one cited archived-evidence query. Three storage daemons and volumes,
accounts, schedules, strategies, risk settings and trading are outside scope.

Controller budget is 600 seconds including 180 seconds recovery reserve.
Pre-controller CLI verification and token source each have separate 10-second
bounds, not one whole-wrapper 600-second deadline. File validation is not under
that controller budget. Logs/audit/client effects may persist. Cleanup/original
restoration is attempted on failure, not guaranteed healthy or byte-exact rollback.
Only all-checks/query/receipt success may leave the replacements running.

Only the exact original orchestrator ID/image/running-state source may emit the
SERVICE_TOKEN field; no full environment export or credential fallback. The
strict parser and private pipe keep token values out of argv, env files and
diagnostics. Reference clearing is not secure memory zeroization. Advisory
pre-token path checks do not promise a cross-process single credential read.
No automatic retry, marker reset, new preparation or old-ID adoption is allowed.

## Verification

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6d_handoff.py
```

23 passed in 0.29s. Existing hash-pinned cases reused with labels changed only;
all native source responses and tokens synthetic, real process/socket calls
forbidden. Exact accepted inputs/default/digest drift, scope/subject/network/
argv contradictions, occupied directory/broken symlink, CLI refusal, one-source/
private-pipe delivery, bad token response and sanitized no-retry errors covered.

Actual cutover default passed with 73 bound files verified and native/token/
backend/lock/reservation tripwires: no action, startup or reservation. Receipt
c7cdd352bc420e634df34e6057c4a85a5de676e3ebe21971b3cd8a139847dc9c.
Actual fixed-handoff default module also exited 0 with the same inert stdout;
terminal result transcribed into handoff_inert_validation.json without rerun.

```text
execute_reviewed_v6d.py 0d942f6d41d6e93d07e8129358f20d369b91e2a2f66c607fb157c912ac727959
test_companion_v6d_handoff.py b7ef65c857cc7f800a8a2fb143192952a3810e9a3ca785f92da911d4ee1903b2
packet review d03af968d206cac23bc1180a1019da772a9eee617996d0989c0ac87dd4c42d1e
scope 63a8571166993cfbccb51ae474da9fd43089cdea8f61861ff52fb0bfdc2c74d9
runtime c15d6ea7b98c29c965b95c7a075e82db5a4e8de4acf810e04261afebe197adb6
```

## Remaining Proof

Obtain separate independent review of exact source/test/record hashes and the
unchanged private-handoff mechanism. No further source edits are planned.
Synthetic source responses are not live token verification. No startup, SDK,
attachment, endpoint, cancellation/recovery or cited query success follows from
offline evidence. Historical V6c cause remains UNVERIFIED.

# Explanation failure diagnostics: offline implementation

Date: 2026-10-16 10:06 UTC. Active role: ENGINEER.
Risk: HIGH (client transport and verification boundary).
Acceptance state: READY_FOR_INDEPENDENT_REVIEW.

## Scope

Operator requested sanitized failure details before assertions and offline
client-guard tests. This is not authorization to restart services, make a live
query, use credentials, rebuild, migrate, or change trading operations.
The earlier operation record `companion_reconnection_20261016.md` is unchanged.

SHOWN from source: transport errors and normalization rejections previously
collapsed into None; the verifier could reject the final provider before
retaining the cause. The earlier live failure remains unexplained. These
offline fixtures are not evidence that a particular cause occurred live.

## Changes

- `_explain_diagnostics.py`: opt-in ContextVar capture, bounded to 16 events.
  Fields are allowlisted. Records transport outcome/status, recognized response
  fields, provider category, execution-disabled flag, evidence count and SHA256
  hashes of citation identifiers/URLs (UTF-8 with surrogatepass for escaped
  lone surrogates). No raw headers, tokens, questions,
  narratives, URLs, response bodies or exception text are retained.
- `_shared_http.py`: records missing service token, HTTP errors, transport
  errors, JSON parse failures and successful JSON receipt. Prior auth, redirect,
  proxy and timeout changes were already dirty; they are preserved, not claimed
  as new work. This turn does not alter their policy.
- `market_view.py`: records invalid envelope, missing explanation fields,
  foreign-asset rejection, successful normalization and static fallback.
  The foreign-asset guard, response selection order and fallback remain unchanged.
- `verify_companion_stack.py`: child captures diagnostics; parent revalidates
  the receipt and emits it before proof checks. DashboardProofError carries the
  safe receipt into the saved result, including failed child processes. Raw
  child stderr/stdout is not copied into that receipt.
- Offline tests cover transport/normalization errors, citation hashing,
  redaction, bounded capture, nested context restoration, retained verifier
  failures and unchanged guard/fallback behavior.

The confirmed substring defect is deliberately NOT fixed in this step:
`whether` contains `ETH`, so the current guard can reject a BTC explanation.
The characterization test explicitly asserts that current behavior. It is not
acceptance of that behavior, a guard bypass, or proof of the live failure's cause.

## Verification

VERIFIED_ENV: local Python 3.12.10; no dependency installation.

Initial command used an incorrect listener-test exclusion:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
tests/test_explain_diagnostics.py tests/test_verify_companion_stack.py \
tests/test_dashboard_companion_http.py -k 'not bypasses_environment_proxy'
```

Result: 32 passed, 1 failed in 0.52s. The existing
`test_environment_proxy_never_receives_companion_bearer` attempted a loopback
listener; the sandbox refused its bind with PermissionError. No service startup
or live query was performed. This selection error is retained, not called green.

Corrected fully mocked slice:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
tests/test_explain_diagnostics.py tests/test_verify_companion_stack.py \
tests/test_dashboard_companion_http.py \
-k 'not test_environment_proxy_never_receives_companion_bearer'
```

Result: 32 passed, 1 deselected in 0.42s.

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
tests/test_dashboard_view_data.py -k research_explain
```

Result: 4 passed, 55 deselected in 0.13s. `git diff --check` passed.
No full suite, market-data strategy rerun, live request or runtime health check.

Independent review found a P2: hashing a citation containing an escaped lone
surrogate raised UnicodeEncodeError only with capture enabled. Initial review
disposition was REJECTED pending correction. The hash encoding now handles
those strings without throwing; a new actual-client capture-on/off regression
preserves the result and verifies a serializable digest. Re-running the same
corrected mocked three-file command: 33 passed, 1 deselected in 0.44s. The four
earlier normalization tests remain separate evidence. The separate reviewer
then ACCEPTED the narrow diagnostics correction: 24 tests passed on the two-file
diagnostics/verifier slice, and its original mocked reproduction now shows
capture-on/off parity and retained serializable diagnostics. It did not rerun
the parent's entire three-file slice. Runtime integration and concurrent
isolation remain UNVERIFIED; no runtime success is inferred.

## Offline Usage And Next Boundary

Wrap the existing client call in `capture_explain_diagnostics()` and retain the
events before checking provider/execution/citation assertions. Capture is
opt-in and makes no request by itself. `verify_companion_stack.py` now does this
for its dashboard subprocess; do NOT run that script under this authorization:
its existing run mode builds an isolated stack and removes its owned volumes.

Future use against the seven existing containers requires a separately approved
bounded startup/query/rollback plan. Reuse this capture around the real client;
do not launch the isolated-stack verifier as a substitute. Citation hashes aid
correlation but do not themselves verify stored evidence or its authenticity.

Independent review must check sanitization, failed-child retention, absence of
guard/selection weakening and preservation of existing transport protections.
Operational status and the earlier failure remain INCOMPLETE.

## Source Hashes At Handoff

```text
16239e925790808d0a55054e7d5037727a87146e3c2c28a73263474099f5c091  dashboard/services/views/_explain_diagnostics.py
63875d94a655872fe9b67125e31079e9fc001b02c7514e045de5186fb9087361  dashboard/services/views/_shared_http.py
c280d5797be077cb31413fe7a0609dec267465a49cd910646d068b9be95ab6fe  dashboard/services/views/market_view.py
d95c3a4b7030d1073679e43a2922a63d9ebcbdea4092ede814ac9425ec5154ce  scripts/research/verify_companion_stack.py
e58e7af76cdf88030a588989d633618c910c8b1deb7cadad4206199668cd317a  tests/test_explain_diagnostics.py
34c69a47907605230682b04d4cb67b27e5d69e4bbeb063c2f27de5f982e08dcd  tests/test_verify_companion_stack.py
```

The HTTP-file hash includes pre-existing uncommitted changes. These hashes
identify the reviewed files, not a clean-branch patch or deployment artifact.

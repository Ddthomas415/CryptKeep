# Fixed V6f handoff, October 25

Role: ENGINEER. Risk: HIGH. Separately ACCEPTED_WITH_RISK, offline handoff only.
Runtime/explanation INCOMPLETE. No execution authorization inferred.

## Scope and smallest change

Bind the reviewed V6f stopped IDs, new memory image, accepted restricted policy
scope and actual inert receipt to a fixed handoff. No service operation, actual
credential read, preparation, marker reset or cited query in this work stage.
Old handoffs, policy records, evidence and attempts remain unchanged.

New files:

- `docs/review_artifacts/companion_integration_inputs_v6f_20261025/execute_reviewed_v6f.py`,
  SHA256 `1153fd7650bb0eec2c01049fca12b5afe8c6078cd71b3975e881cb180ece3044`.
- `tests/test_companion_v6f_handoff.py`, SHA256
  `adff3210801a506bda9e261d40e01aa8726be251f55fa6698f2d53334dda375a`.

The execution flow is exactly the reviewed V6e launcher. Changes are version
labels, prospective attempt, four fixed hashes and two lookups that bind the
current review's published_outputs hash table rather than the prior bindings
schema. An exact-delta test prevents additional flow changes. The generic
private-pipe helper is reused by its existing exact hash under a non-main name;
its old launcher, input bindings and execute function are not invoked.

Default remains inert. Record/consumer/real-loader checks precede any future
token-source operation. Twenty current consumers, seven subjects, 132 source
pins, actual staged IDs, configured network binding and exact scope-linked
reviewer fields remain required. No old packet is silently adopted.

## Targeted verification

VERIFIED_ENV offline:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6f_handoff.py
```

SHOWN: 29 passed in 0.31 seconds. Reuses 23 hash-bound prior synthetic cases,
plus exact-delta comparison, three current consumer drift cases and two new
published-output binding mismatches. Tokens and native responses are fixtures;
network/native entrypoints are tripwired. No full suite or actual token read.

Actual default module invoked via runpy without --execute-once. Socket,
subprocess, native transport, backend, token read, reservation, flock, pipe,
temporary directory, core-limit and write-open operations blocked. Only the
thirteen declared input files could be opened via os.open, read-only. Exit 0,
stdout matches the accepted packet's inert receipt, no tripwire calls, cutover
marker absent before and after. This is entrypoint proof, not service proof.

`runtime_packet_v6f/handoff_inert_proof.json` SHA256:
`d0c393eff7eb3ada8956b53355a16dac3a6d0721f332112b96b5d518e706d31c`.
It binds launcher, tests and prior packet receipt, with exact default result.

## Operational boundary, not permission

The proposed later operation is one invocation: privately reuse the existing
internal service token, gracefully stop the four original research applications,
activate/start the four prepared replacements, run existing fresh checks and
one frozen-question cited-evidence request. Storage lifecycle, volumes, accounts,
trading and schedules remain outside the mutation scope.

Controller budget: 600 seconds including 180 seconds for recovery. Native CLI
verification and token-source inspection have separate ten-second caps before
handoff; this is not a whole-wrapper 600-second wall guarantee. Source/artifact
read overhead is also outside that controller budget. No automatic retry or
receipt reset. Log/audit effects can persist; recovery is not guaranteed.

Pre-token lexists is advisory, not atomic exclusion; the existing controller
lock/reservation remains mandatory. Python references are cleared, not securely
zeroized. Successful flags require the existing complete runtime/citation
acceptance checks; independent packet policy acceptance does not waive them.
Failure uses the existing owned cleanup/restoration. Full success alone permits
leaving the four replacements running. No current cause, health or profit claim.

## Independent acceptance and closeout

Separate GATE ACCEPTED_WITH_RISK, no blocking findings, for fixed handoff source,
bindings and inert behavior only. Review SHA256
`e6056228ab7618a0a923d27ddf5dbc64bcc608700d69ad3c631de340c56f777e`,
at `runtime_packet_v6f/handoff_independent_review.json` in the artifact directory.
Reviewer read the complete launcher/helper/test flow and retained operational
limits, independently ran all 29 tests (0.26 seconds), and executed the actual
default module via runpy under operation/write tripwires. Exit 0, zero tripwire
calls, empty stderr and stdout equal to the saved proof/packet receipt. Cutover
marker absent before and after. No native call, token read or service operation.

Parent read the complete review and verified all 31 listed source/artifact
bindings. Sources/tests/proof/packet remain unchanged after review; only the
checkpoint, current index and work log were updated. No additional tests needed
for that documentation step; no full suite or runtime operation performed.

The accepted offline implementation and review objective is complete. Explicit
separate operator authorization is required for the one runtime operation
described above. Preparation must not repeat or reset, and no current daemon,
installed-source, health or cited-query outcome is inferred from this acceptance.

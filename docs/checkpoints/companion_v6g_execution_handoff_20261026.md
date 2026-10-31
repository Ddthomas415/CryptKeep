# Fixed V6g execution handoff, October 26

Role: ENGINEER, followed by separate GATE review. Risk: HIGH.
Offline handoff independently ACCEPTED_WITH_RISK; no operational acceptance.
Runtime remains INCOMPLETE. No token read, startup, cutover or query authorized.

## Objective and minimal change

Continue the accepted offline integration objective using the existing V6f
handoff flow, fixed to the actual V6g packet, receipt and review hashes. Files
remain under the existing companion_integration_inputs_v6g_20261025 artifact
directory because that is the accepted preparation/packet identity, not a claim
that the new handoff work occurred on October 25.

Added execute_reviewed_v6g.py, tests/test_companion_v6g_handoff.py and the
verification probe verify_handoff_default.py. No production consumer, old record,
source-policy meaning, witness, runtime controller or credential mechanism changed.

The exact-delta test limits changes from the reviewed V6f launcher to V6g
labels/four hashes and the actual receipt schema. V6g's fixed-hash receipt has
response, not stdout, and no review_sha256/scope_sha256/runtime_sha256 fields.
The handoff therefore reads response and does not invent those missing fields.
Separate fixed hashes still bind receipt/review/scope/runtime, published-output
hashes still cross-bind scope/runtime, real input loading still binds all records,
and new explicit response attempt/manifest comparisons bind the proof to the plan.
No new approval bridge or synthetic operational evidence is created.

## Execution behavior retained, not exercised

Default is validation only. Execution requires the explicit --execute-once flag
and separate operator approval; the flag itself is not authorization.

The optional execution path retains original source ID/image/running checks and
the SERVICE_TOKEN-only formatter; one bounded private source read; anonymous
pipe handoff to the existing cutover; fixed sanitized failure output; no fallback
credential source, retry or secret printing/logging. Reference clearing is not
secure memory zeroization. Core-limit changes occur only on execution.

The cutover has 600 seconds including 180 for recovery; CLI validation and source
inspection have separate ten-second bounds before it. This is not a 600-second
whole-wrapper guarantee. Consumed-marker lexists is an advisory pre-token check;
the existing controller's atomic reservation remains authoritative. Logs/audit
writes may persist and recovery is not guaranteed. Nothing in this work grants
service startup, volume mutation, trading, schedule or account authority.

## Targeted proof

VERIFIED_ENV isolated local verification:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6g_handoff.py
```

SHOWN: 31 passed in 0.54 seconds. Retained synthetic source/private-pipe,
malformed-token, CLI refusal, no-retry/error sanitization and consumed/broken-link
cases; current guard/verifier/installer drift; published-output mismatch; actual
receipt plan mismatch; exact launcher delta. All tokens/source responses in these
tests are synthetic. No native source or credential access occurred.

Actual default-module proof:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6g_20261025.verify_handoff_default
```

SHOWN: runpy executed the actual module as __main__ without --execute-once, exit
0, empty stderr, output exactly equal to the existing default cutover response.
Native/backend/token/socket/subprocess/reservation/flock/pipe/temp-config/core-limit
tripwires stayed at zero. Exact file allowlists prohibited unrelated reads and
writes. The real input loader runs twice in the retained validation flow, yielding
26 read-only os.open calls; these are local validations, not HTTP/query retries.
No cutover marker existed before or after.

Proof: runtime_packet_v6g/handoff_inert_proof.json, SHA256
b0232f7ead82f6f91091675fcb4f9cc6ba138703fcf7e8749fe78b3637d1b953.
Launcher SHA256 f07d6bc90f0d2d2e578da1f03d8d73ee2dac0cdc465e7535491ad29afe4554f4.
Tests SHA256 b140831d03d74b99c67df837988a95f08e9986748977dba7953b84cbe7703aba.
Full suite, current daemon state, installed-source/SDK checks and live query
were not run. Snapshot/configuration/provenance limitations remain unchanged.

## Handoff

Independent GATE ACCEPTED_WITH_RISK, no blockers, exact offline handoff only.
Review: runtime_packet_v6g/handoff_independent_review.json, SHA256
c3df4a6f24f8ea21ce0a29464f4d7739aa20091fa2489b28f722b1018a115b16.
The reviewer reproduced 31 focused tests in 0.29 seconds and the actual inert
proof exactly, with zero operation tripwires. Additional synthetic source/consumer
KeyboardInterrupt cases propagated once without output or retry. These are not
live cancellation/recovery tests. No source, test, packet or proof was changed.

Parent read the complete review and verified all 33 bindings before this
documentation-only closeout. Its checkpoint digest refers to the submitted
pre-closeout text, not this updated status. The accepted source/proof hashes
remain unchanged. No real token, daemon or service operations occurred.

Offline handoff implementation/review objective is complete. It does not prove
the previous runtime failure fixed; runtime remains INCOMPLETE. Request separate
approval for exactly one reviewed V6g invocation: private existing service-token
reuse, graceful stop of four original research applications, activation/start of
four prepared replacements, existing fresh checks and one frozen cited query.
Three storage services/volumes, trading and schedules remain untouched. Success
may leave replacements running only after all acceptance checks pass. Failure
invokes existing owned cleanup/original restoration, not guaranteed recovery.
Controller 600 seconds includes 180 recovery plus separate ten-second CLI/source
prechecks; writes may persist. No automatic retry, reset or new preparation.

# Actual V6g runtime attempt, October 26

Role: ENGINEER, followed by separate GATE review. Risk: HIGH.
Runtime INCOMPLETE. Saved failure evidence ACCEPTED_WITH_RISK only.

Explicit operator approval covers exactly one reviewed V6g handoff: private
existing internal service-token reuse, graceful stop of four original research
applications, activation/start of four prepared replacements, mandatory checks
and one frozen cited-evidence query. Three storage services/volumes, trading and
schedules remain untouched. Only complete success permits leaving replacements
running. Failure invokes owned cleanup/original restoration, not guaranteed.

The controller has 600 seconds including 180 recovery; separate ten-second CLI
and source-token checks precede it. This is not a whole-wrapper 600-second wall
guarantee. Logs/audit effects may persist. No retry, reset, new preparation or
unrelated operational action is authorized.

VERIFIED_ENV file preflight: 32 nonhistorical handoff-review bindings/current
consumers matched; pure input loader passed; CLI digest matched; proposed cutover
marker was absent. These do not establish current daemon/source/SDK/health/
namespace/lineage/citation success; those remain mandatory operational gates.

Exactly one invocation, execution session 75647:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6g_20261025.execute_reviewed_v6g --execute-once
```

## Actual result

SHOWN tool result: exit 1, query attempted but not passed, receipt complete,
services started, running update incomplete. Controller reports configuration
rollback verified, exact baseline restoration false and all tracked unresolved
lists empty. Prepared IDs were not preserved and preparation was consumed.
No retry/reset/recreation, additional native inspection or live query occurred.

The complete 98-event receipt shows companion HTTP 200 with five citations and
execution disabled. Client normalization accepted the companion response; no
foreign_asset rejection or static dashboard fallback was selected. This differs
from the V6f failure and is direct evidence of passing that client boundary, not
of a fully verified explanation.

The stored-evidence verifier was invoked. Its event reports outcome complete,
shape_valid true and five false Boolean fields. Its explicit false meaning is
not_established_or_not_evaluated. This is NOT proof of five independent failures.
The pure evaluator and remote entrypoint collapse caught failures into the same
all-false dictionary; the dedicated eight-second deadline also emits all false.
No first failed predicate, response prose/types or live DB rows were retained.
The specific verification cause remains UNVERIFIED. No claim of absent timeout,
bad database, invalid article body or false topical evidence is justified.

Recovery event records configuration_restored true, exact_baseline_restored false,
network_connectivity_verified false. It does not establish post-recovery health,
connectivity, volume-byte identity, exact restoration or current running state.
No success or profitability claim is made.

## Preserved evidence and bounded offline diagnosis

Directory:
`docs/review_artifacts/companion_integration_inputs_v6g_20261025/actual_runtime_v6g/`.

- receipt.jsonl: byte-identical state copy, SHA256
  eb2ebdd2013f73d6649885b8714281f91585cedab479d2e2bbc75942d25fdfbc.
- outcome.json: explicitly attributed parent transcription of session 75647,
  not independently captured process output.
- diagnose_saved_result.py and diagnosis.json: local reproducible saved-receipt
  and archive correlation, with exact source/input hashes; no remote execution.

VERIFIED_ENV offline command, exit 0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6g_20261025.actual_runtime_v6g.diagnose_saved_result
```

Five citation ID/URL hash pairs match frozen archive records 5,47,18,5,26. This
does not prove persisted identity, body hashes, topical or causal verification.
Inspection of unchanged verifier code confirms the diagnostic ambiguity; it
does not reconstruct missing response or DB data. No production source, witness,
archive or acceptance criterion was changed and no full suite ran.

## Independent saved-result review

Separate GATE ACCEPTED_WITH_RISK, saved evidence only, no blocking findings.
Review: actual_runtime_v6g/independent_review.json, SHA256
824de144aaf08e96ce3a634f13bbbf43a0dc6de4e7525e3df585384b504122a3.
The reviewer read all 98 events, verified state-copy equality, reproduced the
diagnosis exactly under network/subprocess tripwires and confirmed the ambiguous
all-false and recovery limits against unchanged source. No native, token, DB,
service or query operation was performed by the reviewer. No full suite ran.

Parent read the complete review and checked all 11 source/evidence bindings
before this documentation-only closeout. Source, receipt, outcome, script,
diagnosis and review are unchanged. The reviewed checkpoint digest identifies
the submitted pre-closeout text, not this updated result status.

## Next boundary

The approved single attempt, result preservation and independent evidence review
are complete, not the service-restoration objective. The highest-leverage repair is
secret-free first-failure/stage diagnostics for the verifier, preserving its
existing fail-closed criteria and timeout behavior. That repair is not implemented
here. Another cutover with the same opaque diagnostic is not recommended.
Any new preparation or runtime action requires fresh scope/authorization; consumed
V6g evidence/IDs must not be reset or reused. No next operation is authorized.

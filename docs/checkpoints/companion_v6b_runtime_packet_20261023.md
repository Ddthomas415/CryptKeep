# V6b Runtime Packet Draft

Active role: ENGINEER. Risk: HIGH (prospective runtime configuration).
Objective: derive the existing runtime packet for the four independently
accepted stopped `workerprep20261023v6b` containers, without operational work.
State: READY_FOR_INDEPENDENT_REVIEW. Runtime/explanation: INCOMPLETE.

## Shown Offline

- Accepted manifest `67e29202...7485e`, actual evidence `da7ee2de...35ef` and
  separate actual-ID review `c8fd96dd...ce96` pass existing pure loaders.
- Seven subjects retain 128 source pins. Storage3 bindings are unchanged.
  Application4 images and all source pins equal the old accepted runtime
  records; only application container IDs and preservation hashes change.
- The 43 application source entries match the direct saved v6b witnesses and
  frozen local bytes. Other source pins reuse same-image accepted archival
  evidence, not new-ID captures. These distinctions remain in provenance.
- Four staged snapshots reconstruct exactly. Final alias-only configuration
  and preservation projections are MODELLED, not live attachment evidence.
- Seven installed-policy proposals and one runtime proposal remain INCOMPLETE
  with empty reviewers; no accepted policy record is copied or manufactured.
  Independent review must assess the new IDs, direct-module Uvicorn launch
  path and current consumer applicability against existing scoped evidence.

## Changes And Verification

New immutable artifact directory:
`docs/review_artifacts/companion_worker_preparation_20261023/runtime_packet_v6b/`.
Existing source, policy, preparation, receipt and failed-attempt records untouched.

Producer: `docs/review_artifacts/companion_worker_preparation_20261023/assemble_runtime_packet.py`
SHA256 `d9324398722f85bdb285ca1695c1de24ab3ec184d9784715539a63a3c9982d2d`.
Tests: `tests/test_companion_v6b_runtime_packet.py`
SHA256 `2fbc644784dbf95d575dcb74e5a4a216898be2ce04fa9e639e4ee2b64b1184c3`.

VERIFIED_ENV, repository virtualenv, empty environment, no bytecode/cache writes:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
  -m docs.review_artifacts.companion_worker_preparation_20261023.assemble_runtime_packet
```

Exit0: 12 artifacts, seven subjects, 128 source pins, native operations false,
policy approvals false. Producer creates a new directory exclusively; do not
rerun its publishing main. Pure `derive()` may reproduce bytes offline.
An initial direct-file invocation failed at import before any output was
created; module invocation above is the verified command.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./.venv/bin/python -B -m pytest -q -o addopts= -p no:cacheprovider \
  tests/test_companion_v6b_runtime_packet.py
```

Result: 7 passed in 0.18s. Tests forbid subprocess launch and network connections,
check exact subject/source preservation, reject changed input/consumer/witness
bindings, preserve absence of authority and reproduce all 12 artifact bytes.
No full suite or operational test repeated.

Key outputs SHA256:

- subjects.draft.json: `afadff45eafff21a102c0d4a9ba153e30b248d79f480540a976669f9b852d8dd`
- staged_metadata.derived.json: `ca7101c34446f7b04cc0e1c08dcfcba2026e197d3cecbedb8de13e3cf70118e8`
- provenance.json: `9fe33a809937cb746fd8ea699613dea4cb2cf25154fc1c45e986eae48772a96d`
- runtime_review.draft.json: `60dddd417092e51313f959d8912cc1f2bd82933f2779e67a2fb66e190aac68f1`
- topical_approvals.json: `f4de03c65058769eb434e5931065deaeb5795087983a92a3b2f54dacd8feff45`

## Boundary

No Docker command, build, create, start, stop, signal, credential access,
reservation, service query, cutover, scheduler, account or trading operation.
No policy verdict or service readiness follows from structural validation.
Attempt label provenance remains accepted controller evidence, not independent
raw-label capture. Existing fresh installed-source/configuration/storage and
recipient checks are not waived. Health, shutdown/ack/cancellation/recovery,
usable cited explanation and profitability remain UNVERIFIED.

Next proof: independent review of exact draft derivation and policy applicability.
Only a separate reviewer may author accepted derivative runtime/policy records.
Any later native observation or runtime attempt requires separate bounded
authorization; this draft is not an executable handoff or token producer.

# V6f offline runtime packet, October 25

Role: ENGINEER. Risk: HIGH. Separately ACCEPTED_WITH_RISK, restricted offline
source-policy scope only. Actual default/inert validation passed.
Runtime/explanation remains INCOMPLETE; no startup/cutover/query authorized.

## Scope and exact changes

Continue integration of the independently accepted archival-probe repair using
the four actual reviewed stopped V6f replacements. No new architecture, source
repair, native metadata capture, token access, background process or service
operation. Old packets, IDs, captures and consumed attempts remain unchanged.

Artifacts under
`docs/review_artifacts/companion_integration_inputs_v6f_20261025/`:

- `assemble_runtime_packet.py` SHA256
  `16c8616f9152fec3e004ad54e1bd81795323cb88827ff6ccaf2f3933a8d36453`.
- `runtime_packet_v6f/`: twelve canonical drafts, including seven subjects,
  per-subject policy drafts, V2 runtime draft, staged metadata, topical approvals
  and provenance. Draft decisions INCOMPLETE, reviewer blank, policy flags
  UNVERIFIED. No approval authority is created by the assembler.
- `tests/test_companion_v6f_runtime_packet.py` SHA256
  `0030860eec82d6ea3d68aa9cc623c02aae62f487befbb83c6c4076384fe2af2c`.
- `runtime_packet_v6f/provenance.json` SHA256
  `69cbc1a2a4db0261468ba46b8c82d486167fa2b007ac40c593cfa3dc7a0ffdfc`.

Three storage subjects remain exactly unchanged. Four application IDs are the
separately accepted V6f IDs, not removed V6e stages. Only memory's image and two
application source digests change. Its original parent ID/image/foundation
match the prior accepted preparation manifest. Commands, options, source paths,
declared final configuration and three restricted policy meanings/seven limits
remain unchanged. Final aliases are MODELLED, not observed connectivity.

Twenty current consumer hashes are bound. The only changed consumer is the
independently accepted installer diagnostic repair. Host guard and evidence
verifier remain unchanged. Canonical archived witnesses are still 7, 5, 47, 18;
no selection forcing, changed question or relaxed body/lineage predicate.

## Source provenance: deliberately not the old same-image claim

There are 132 source pins, with distinct evidence bases:

- 43 application entries: preparation controller verified at creation; not
  independently recaptured source streams in this packet.
- 52 inherited library/storage pins on unchanged image identities.
- 37 memory-library/launcher pins inherited through the common original parent
  and reviewed source-only overlay build path, not an unchanged memory image.

The hash-bound existing builder uses the exact original image, COPY-only app
destinations, no pull/network build, and verifies parent layer prefix and layer
count. Accepted preparation completion attests that path. This supports a
bounded inheritance rationale, not an independent installed-library capture or
blanket SDK/startup proof. The new memory image is not silently treated as old.
Mandatory fresh installed-byte, namespace, recipient, compatibility and citation
checks remain in the existing runtime path. Independent policy applicability
review must judge this evidence; structural loading alone cannot approve it.

## Verification

VERIFIED_ENV:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6f_runtime_packet.py
```

SHOWN: 21 passed in 0.54 seconds. Tests cover exact subject/source/image delta,
truthful provenance counts, real pure-loader composition under synthetic
temporary reviews, input hashes, original/stage/alias/command/pair drift,
detached identity review, consumer drift, parent mismatch, prior child/library
change and repair-lineage mismatch. Network/subprocess/token/backend/reservation
tripwires enabled. Full suite not run. No market data or services accessed.

## Independent acceptance and actual inert validation

Separate GATE ACCEPTED_WITH_RISK, no blocking findings. Review SHA256
`e603f8d8d3bab5cd9afc7528f08c184677a534f8b127b9a09e3a2f1610dd6543`
at `runtime_packet_v6f/independent_review.json`. Reviewer reproduced all twelve
draft bytes, independently ran 21 tests in 0.39 seconds, read the prior per-subject
rationales and source maps, and assessed the actual source/image/consumer delta.
It accepted the restricted inheritance rationale, not fresh installed-library
capture or general SDK readiness. It performed no native/service operation.

Reviewer emitted a new scope, seven exact-subject child records and V2 runtime
record. New scope SHA256:
`a165d3db68fe6dd139e44d5052049b162bbc7214d8df0d213974f2d4e2e58ef7`.
New runtime record SHA256:
`4d92115db3d5a52f4df97294e27e7d8b5b02dcbdc9faedb5a8d2ad74ba4ef5bc`.
All eight child/runtime reviewer fields bind the exact scope digest. Initial
reviewer labels exceeded the consumer's 200-character limit and were rejected
offline; only the new labels and dependent hashes were corrected before final
pure loading passed. No source, gate, schema, draft or acceptance criterion was
changed to accommodate them. This is not a runtime failure or operation.

Parent read the complete review, checked 77 unique input/source/output bindings,
verified literal preservation of the three policy meanings and seven limits,
then invoked actual `companion_cutover.main` DEFAULT with socket/subprocess/
native/backend/token/reservation/lock tripwires. Only thirteen declared input
files could be opened read-only; exactly thirteen opens occurred. Exit 0,
input_bindings_validated true, actions false and startup false. The cutover
marker was absent before and after. Receipt SHA256:
`1d1fe0ccb5e3e44a50ffd69ed56c479317f30690f2b2a37aae77c6336f74f241`.
The receipt retains exact inert argv/result and the accepted review hashes.
No code/test/draft/policy record changed after review; full suite not rerun.

The accepted packet and inert-validation objective is complete. No fixed
execution handoff or actual runtime attempt is supplied by this stage. Next:
bind the new receipt/review/scope/runtime to a fixed private-token handoff,
verify it offline and obtain its independent review. The new review uses its
actual published-output hash table; an old wrapper's record assumptions must
not be silently carried forward. No new framework or service action is needed
for that offline step. Startup/cutover/query remains separately authorized.

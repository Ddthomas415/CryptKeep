# Exact Launcher Pin Integration

Active role: ENGINEER. Risk: HIGH (transport guard/runtime configuration).
Objective: finish I1's bounded offline integration after accepted capture/R1
review, preserving prior artifacts and requiring no new native observation.
State: READY_FOR_INDEPENDENT_REVIEW. Runtime remains INCOMPLETE.

## Smallest Delta

One production line adds only
`/usr/local/lib/python3.11/site-packages/uvicorn/__main__.py` to transport `_FILES`.
No SDK regex expansion, bypass, auth/ID/limit/timeout change or lifecycle change.
Removing that exact line reconstructs the prior accepted transport SHA256
`817c378c289093a7f7c5395f3eb28291e5af1c3a7ae8b09eed2bde5868d2ecc5`.
Current transport SHA256:
`5cbdf417a6b180bdd6e77cf7c9b85eba6649ebd15212f0836725f13301edcd81`.
Git HEAD diff also contains earlier accepted work; it is not all new this turn.

New `derive_launcher_packet.py` reuses hash-bound accepted draft/capture/review
records and verifies all 13 current consumers. Only transport's consumer hash
changes. Exactly four captured launcher pins are added to the application
subjects, with explicit mandatory presence/hash checks: 128 to132. Every old
subject field, source pin, storage subject, image, ID and modeled preservation
hash is unchanged. Missing/wrong/additional source entries are refused.

Artifacts are separate under
`docs/review_artifacts/companion_worker_preparation_20261023/runtime_packet_v6b_launcher/`.
Seven policy proposals and runtime proposal remain INCOMPLETE/empty-reviewer.
Original draft, actual-ID acceptance, captures, consumed attempts and policies
are preserved. No self-issued policy acceptance or operational grant.
Earlier producers retain their frozen old-consumer pins and are not new handoffs.

## Verification

VERIFIED_ENV repository virtualenv, empty environment, no bytecode/cache writes:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
  -m docs.review_artifacts.companion_worker_preparation_20261023.derive_launcher_packet
```

Exit0:12 artifacts,132 source pins,native operations false,policy approvals false.
Publishing main exclusively creates its output directory; do not repeat it.
Pure derive() can reproduce saved output without native operations.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./.venv/bin/python -B -m pytest -q -o addopts= -p no:cacheprovider \
  tests/test_companion_launcher_packet.py tests/test_companion_docker_transport.py \
  tests/test_companion_cutover_inputs.py
```

Result:152 passed in1.54s. Includes8 new packet cases plus the new accepted path
and5 rejected nearby paths; existing context/authorization/limit/tar/secret-path
guards and loader cross-bindings remain tested. Packet tests forbid subprocess
and network access. Existing transport tests use fake runners or owned local
test processes, not Docker/service operations. No full suite or native tests run.

Hashes:

- derive_launcher_packet.py: `41a219108b4fccced72491c3de7f2c75843a799fa894512e6b3f075d56438e19`
- tests/test_companion_launcher_packet.py: `0da8e838753d48d9bc3658bc950f8583544fae4880d78fff08b53f32773f0ce5`
- tests/test_companion_docker_transport.py: `7d5674bcd6d16eba3f81ee5b9330e6409e89932f18d60a7f7bd3dbdcfb64c1cd`
- refreshed provenance.json: `6438a9aa91a1cdc5dafcd266a0f66e00cd1ce08a401a23d63e955c3ee56852f9`
- refreshed subjects.draft.json: `0e6cfcc5bdf823659cf6d1f17aab0a961267d9d881e317b62dfa280141402107`

## Review And Operational Boundary

Independent review must verify exact one-path production delta, additive four
pins, unchanged scoped startup/client meanings, existing repair applicability
and current consumer bindings. Only that reviewer may author accepted policy/
runtime derivative records. Parent may then run the existing default inert
loader against accepted records, without token/backend/reservation/execute flags.

No Docker, credential, container, storage, scheduler, account or trading operation
occurred. Final alias/network state remains MODELLED; runtime import, health,
shutdown/ack, cancellation/recovery and a usable cited query remain UNVERIFIED.
Any executable handoff or runtime attempt still needs separate bounded approval.

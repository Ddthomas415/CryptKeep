# V6i Memory-Image Evidence Capture

Role: GATE closeout of separate R2 review. Risk: HIGH. ACCEPTED_WITH_RISK
for the exact R2 implementation only. Capture and runtime NOT AUTHORIZED.

## Missing Proof and Bounded Scope

The saved preparation/actual-ID review accepted four stopped replacements, not
SDK applicability for the changed memory image. Prepare one fixed read-only
capture rather than repeating the older 11-subject/storage inspection. Reuse the
existing pinned streaming transport, CLI verifier, regular-file tar validator,
Plan and ReviewedPreparation loaders. Do not invoke the old capture entrypoints
or change production transport, source-policy, configuration or controller code.

Script: docs/review_artifacts/companion_integration_inputs_v6i_20261027/capture_memory_image.py.
Default is inert. Any later --execute-capture needs exact source hash, separate
independent implementation review and explicit operator authorization. A matching
flag alone is not permission. No actual memory_image_capture/ exists yet.

Exact targets, from accepted manifest and actual-ID evidence:

- Original memory container 869205e8c8cf9c53bdf5563aebe9b50198fd64d57c340b84b88cdde0a02dd071,
  image sha256:276ce227380a64af3602a045e99b95100461070284dd15df75e07d72a857681d,
  expected running with saved timestamp/restart policy/count unchanged.
- Stopped memory replacement 50998076e44610503e9e72d5e9135541ebbfc0d0abd3980d8b90a6dc32f4a8e6,
  image sha256:989471c8465a31e06f6a6765a919422a36d3f96f67f799cbaeebee6c3ab75e05,
  expected created/never-started, restart count zero, restart policy no.

Two selected before/after metadata inspections cover only those containers. One
image inspection covers only those two image IDs, projecting IDs, rootfs layer
digests and an empty-OnBuild boolean; no raw Env/history/commands/OnBuild content.
Check the original layer list is an exact prefix of the new list with 11 extra
layers, matching the reviewed COPY-only builder's 11 memory-source entries.
Prefix/count evidence does not independently prove every layer's contents.

Copy exactly the 48 paths in the fixed V6h memory policy subject, from the stopped
replacement only: 11 application files plus 37 SDK/launcher source files. Update
only /app/memory_retrieval/main.py's expected digest to its accepted repair hash.
All other expected hashes remain unchanged. Each path passes the existing path
allowlist, each copied tar must contain only one bounded regular-file member,
and bytes are saved/hashed without importing or executing them. No arbitrary
directory copy, application query or credential/file discovery is permitted.

## Preconditions and Limits

Fixed hashes bind manifest, provenance, preparation evidence, external actual-ID
review, saved preparation review, old memory policy, transport and tar helper.
The current 13 preparation/20 runtime source maps and 11 local memory sources
must still match. The actual preparation remains consumed; nothing is reset.
Any identity/image/state/hash difference leaves evidence INCOMPLETE, without
substitution, repair or retry. Existing output directory refuses another run.

One proposed run: at most 51 native commands (2 container inspections, 1 image
inspection, 48 fixed file copies), 10 seconds per command within a 120-second
command deadline measured from capture entry, with 10 seconds reserved for the
final selected inventory. CLI hashing uses the same deadline. Initial local
preflight and final file persistence are not interruptible wall-clock guarantees.
One MiB payload maximum per file; 8 MiB aggregate file-transfer charge including
tar overhead. Failed transport charges its maximum requested transfer plus one
overflow-probe byte, then stops ordinary work; the final inventory is still
attempted within remaining deadline. Metadata is separately limited to 64 KiB
per command, at most three such commands. No automatic repeat or cleanup of
containers. A timeout is not proof that the daemon cancelled an in-flight read.

An exclusive local output directory and temporary empty CLI config are the only
requested filesystem setup. Sanitized raw metadata, source bytes/hashes and report
may persist. Docker access/daemon logs may reflect reads; this is not zero
physical side effects. No create/build/start/stop/rename/remove/exec, storage
query, credentials, private token action, networking change or trading.

## Offline Verification

VERIFIED_ENV for local bindings and synthetic tests only; native state unknown:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6i_memory_image_capture.py
```

SHOWN: 15 passed in 0.47 seconds, no warnings. Entire synthetic 51-command path,
source identity/48-file selection, before/after drift, image-ID/layer/OnBuild
refusal, file hash/symlink/partial-transfer failure, aggregate/deadline stops,
one-use output, input drift, wrong execution hash and inert default verified.
Real module default exited zero with native_operations=false/runtime_authorized=false.
No CLI binary read by the default, real capture, SDK execution or full suite.

## Acceptance Boundary

Review the exact implementation and synthetic proof before requesting the one
capture. A successful capture is READY_FOR_INDEPENDENT_REVIEW evidence, not a
policy approval. Actual source hashes, lineage evidence and applicability must
then be independently reviewed, with controller source-only build checks kept
distinct from direct captured facts. Matching selected sources does not prove
full dependency/import closure, application health, restored explanation path,
original configuration continuity or profitability. Do not inherit old memory
SDK policy automatically. Runtime remains INCOMPLETE. No material assumptions.

## R1 Review and R2 Reserve Correction

Separate GATE rejected R1 (V6I-MEMCAP-01): ordinary command timeouts reserved ten
seconds, but CLI verification received the full 120-second deadline. Its synthetic
slow hash consumed that reserve, leaving only one second for final inventory.
The 15 original tests passing did not cover that boundary. No capture ran.
Preserved original review/report and memory_capture_rejected_r1.tar containing
the rejected source, tests, checkpoint, report and review.

R2 uses one command_deadline for both CLI verification and subprocess timeout:
ordinary work gets deadline minus ten seconds; final inventory gets full deadline.
No other operational selection, policy or budget changes. A near-cutoff synthetic
regression leaves the final ten seconds available, and rejects archived R1 under
offline tripwires. Focused module now 16 passed in 0.37 seconds, no warnings.
memory_capture_implementation_report_v2.json records the updated bindings.
READY_FOR_INDEPENDENT_REVIEW for R2; native capture remains unauthorized.

## R2 Independent Acceptance

Separate GATE accepted R2 with risk, no blockers, closing V6I-MEMCAP-01. Review:
memory_capture_implementation_review_v2.json, SHA256
252039a360894066ffa0924a59bb085de8056f704ab7b0ac8bab94d070c20669.
It verified the entire capture-source diff is only the deadline correction,
preservation of R1 evidence, 16 tests once (0.38 seconds, no warnings), and an
independent pure clock challenge giving ordinary/final deadlines 110/120 and
ten seconds for final inventory. All seven review bindings matched before this
documentation-only closeout; the checkpoint digest now denotes pre-closeout
text. Source/tests/reports/reviews/archive remain unchanged.

Exact accepted source SHA256:
351879131ca4db8541c0cd7dbd888eda3d89ca075827b391ae7a6522febb6e01.
No actual capture, native call or source-policy acceptance occurred. Next is the
operator's explicit decision on one reviewed read-only capture:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6i_20261027.capture_memory_image --execute-capture --approved-sha256 351879131ca4db8541c0cd7dbd888eda3d89ca075827b391ae7a6522febb6e01
```

NOT AUTHORIZED by this record or review. The proposed run inspects the two fixed
memory containers/images and copies the 48 reviewed public source files only,
with the limits above. No source is executed. New local evidence and daemon
read logs may persist. No automatic repeat or reset; actual evidence still needs
independent applicability review. Runtime remains INCOMPLETE.

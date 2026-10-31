# Actual V6g stopped preparation, October 25

Role: ENGINEER, followed by separate GATE review. Risk: HIGH.
Saved preparation evidence and actual IDs independently ACCEPTED_WITH_RISK.
Runtime remains INCOMPLETE. No startup, cutover or query authorization.

## Authorized action and result

The operator explicitly approved one preparation-only action with reviewed
inputs: build/reuse four local source-only images and create four stopped
replacements, privately copying existing configuration without displaying it.
The controller budget is 300 seconds including 120 for recovery. Cache/config/log
effects may persist; cleanup is not guaranteed. Originals and storage stay
untouched. No startup, cutover, query, trading or schedule change; no retry/reset.

VERIFIED_ENV file preflight checked 20 current nonhistorical input-review bindings,
source/consumer hashes, actual Plan loader, CLI digest and absence of proposed
markers. The known pre-closeout checkpoint digest remains historical. Fresh
daemon/source/configuration/ownership checks were left to the existing controller,
not claimed as passed from these file checks.

Exactly one invocation, execution session 44449:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m scripts.research.companion_prepare --manifest docs/review_artifacts/companion_integration_inputs_v6g_20261025/reviewed_preparation_manifest.json --reviewed-manifest-sha256 33e6633229e9399ec695be2f8e743930212b9ed926277235fd071e675fcf2e26 --execute-preparation
```

SHOWN tool result: exit 0, preparation complete/actions true, services started
false, originals interrupted false, attempt reserved true, startup authorized
false. No retry or separate native postcheck was performed. No current endpoint
health or continuous-state claim follows from this result.

## Preserved evidence

Directory: `docs/review_artifacts/companion_integration_inputs_v6g_20261025/actual_preparation/`.

- receipt.jsonl, seven events, SHA256
  9c10af111eae466709555ec8691b1262b5be3a00ea3a1648b9404337166ef498.
- preparation_evidence.json, SHA256
  d5dabf08f0c20cb5976f517b53d7492b3bac8361f1cc9dbb5c947172b29c7143.
- outcome.json: explicit parent transcription of the execution tool result,
  not independent process capture.

The receipt and evidence are byte copies of the controller's state records.
All seven receipt events were read. The published evidence lists four new
created-state replacements, never-started timestamps, zero restarts, restart
policy no and current preparation ownership labels:

| Application | New ID | Image Prefix |
| --- | --- | --- |
| Audit | 996ce9119aecacd10846d573275a8a2a6c687b05dfb6335d6261fa43a325f117 | 27753fce |
| Risk | b2e1d4c6cf22ffe0e91ef485384cda7f735133a8c654e442bdc306e2c4b405c7 | b479fe20 |
| Memory | ddbe21829ab06255eb1cec2634a0e256daa0f9b810d41877cf9d042342b3bfcb | 6dca2b97 |
| Orchestrator | 5c0b0ee52f1b27ecff3d4fa650ff4860f8524a446e24155c982840cddd2ddcf0 | c3059654 |

Images match the prior V6f preparation; this does not prove whether each path
rebuilt or reused cache. Application sources are unchanged. The accepted guard
repair is a host runtime-consumer change, not a new application image change.

## Proof limits and handoff

Existing controller at-creation source/identity/configuration checks are
attestations, not independently recaptured source-file streams or current SDK/
health/connectivity proof. Configured-network evidence is not connectivity.
No private configuration value is exported in these public records. No new
source changes or test/full-suite reruns were needed for this operation.

Separate GATE accepted saved preparation evidence and actual IDs with risk,
no blocking findings. It read all seven events, verified source-copy equality,
manifest/state/ownership contracts, current source/tool hashes and model
consistency. No raw metadata, installed-source streams or native operations were
added by the reviewer. Outcome acquisition remains parent-attributed; existing
at-creation checks do not become independent current-state proof.

Independent review SHA256:
443f678b37ad2cd893cbc2e65fae87e7abdb87eadb485c749f3d2ec2447b78f3.
Reviewer-created actual_id_review.json SHA256:
68dd1328293f97a9213e914a434a7ba2a96a4f1abd33cce8d33856537d2aedce.
Both are in the actual_preparation directory. The latter is the existing
five-field external-review contract, not operation permission.

Parent read the complete review, checked all 48 bindings before this
documentation-only closeout, and the actual pure ReviewedPreparation.load
accepted four replacements. Reviewed source/data/review records are unchanged;
the checkpoint digest in the review identifies the pre-closeout submitted text.
No new tests/full-suite/native calls were made for this closing proof.

The approved preparation plus actual-ID review objective is complete.
Preparation is consumed, cutover unused. Next is an offline runtime packet
binding these actual IDs, current host guard and applicable source/policy
evidence. No startup or cutover may be inferred from preparation success or
this review; an eventual runtime attempt needs separate authorization.

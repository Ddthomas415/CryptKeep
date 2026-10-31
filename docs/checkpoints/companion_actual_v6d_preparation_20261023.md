# Actual V6d Stopped Preparation

Role: ENGINEER. Risk: HIGH. State: READY_FOR_INDEPENDENT_REVIEW.
Runtime: INCOMPLETE. User approved the single stopped-preparation operation
after its explicit scope/side-effect question. No startup/cutover granted.

## Result

The reviewed preparation CLI ran once, exit 0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m scripts.research.companion_prepare --manifest docs/review_artifacts/companion_worker_preparation_20261023/fresh_preparation_v6d/reviewed_preparation_manifest.json --reviewed-manifest-sha256 629662e509e099be8601be1c9499d7139f03803f4f998f5b31fce15b2551b4a0 --execute-preparation
```

Controller reports preparation_complete=true, startup_authorized=false,
services_started=false, originals_interrupted=false. The new preparation
reservation is consumed and must not be reset/rerun. The separate cutover
reservation was not invoked. Configuration copy, Docker cache and preparation
records may persist as disclosed; no private credential values were exported.

## New Identities

All four are created, never started, integer zero restarts and restart disabled.
These IDs differ from historical V6c IDs; immutable cached image IDs match the
previous corresponding images. Image reuse is not container-identity reuse.

| App | New Container ID |
| --- | --- |
| audit-log | 71e6fadd0c4f91aa357f7be5cbf370fbaa7e135d9df6205a328ce7a52883d5d5 |
| risk-stub | 420cde54fbce2b9bc1ca053cf484aa7490c4331821a1b41c8d7c3b9d847500a4 |
| memory | 065c59b4d712fdb46fcd747f9a9de0b88a4550d4114e78af4bbae8717da089c6 |
| orchestrator | 35167f2524e93b2a89920a4135a9f2c5a143ced8c3f361ceea3736b2f234145f |

## Read-Only Verification

SHOWN parent-native capture: known network identity, two selected eleven-ID
metadata reads and 43 regular-file Docker cp streams, 46 bounded reads total.
No container exec, startup, lifecycle change or health/query request in this
postcheck. Only source digests are retained, not source bodies. Config fields
are guarded/allowlisted and environment data is presence/match booleans only.

- Seven originals' complete snapshots equal the accepted fresh baseline.
- Four staged snapshots equal the actual preparation evidence exactly.
- Eleven selected metadata rows equal before/after the source reads.
- All 43 installed app source hashes equal the manifest and local files.
- Temporary stage names/aliases are observed; final aliases/attachment remain
  untested. Empty NetworkID is configured-only evidence, not connectivity.

No full-daemon or other historical stage equality, atomic source snapshot,
volume-byte, service-health, final-network or explanation-path proof is claimed.
Source reads are sequential witnesses; future preflight must recheck them.
No code/tests changed or broad suite repeated for this operation.

## Frozen Evidence

Under docs/review_artifacts/companion_worker_preparation_20261023/actual_d/:

```text
outcome.json 77a85a5c6bf31dc1154d550e181100ad1672f061422b0cc1780f92b1ae55753b
preparation_evidence.json 9441411ba4ad31194b4f53aa99e1705a46365a93a0ebd5527e1e23957f52d65e
preparation_receipt.jsonl 0672601e4b9d8d2e687a966ff09f0fe2f9d51ea4eed72aa03ba0073fb29cbced
postcheck.json 6c85eaf31ec66f89ba34114c1eb90c990436bf95929651b0d971074e5c06dec6
staged_metadata.json b571301e009d0005a7498076db63ccd91b72ef7a7bc9cc4bff9446f6f73722ec
```

Receipt/evidence are unchanged copies from the consumed preparation directory.
No original V6c packet, failed receipt or removed ID was edited or adopted.

## Next Boundary

Independent actual-ID/image/configuration/source-evidence review, not same-thread
approval. It may issue the existing preparation-review record for these exact
hashes; that is not runtime-policy acceptance or permission to start them.
After acceptance, prepare a fresh exact-ID runtime packet and handoff offline.
No actual cutover/query follows automatically. Trading/storage/accounts and
scheduled tasks remain outside this operation. Historical V6c cause UNVERIFIED.

# One Approved V6b Runtime Attempt

Active role: AUDITOR after the authorized ENGINEER execution.
Runtime outcome: INCOMPLETE. Attempt workerprep20261023v6b is consumed.
No automatic retry, receipt reset, new preparation or further runtime authority.

## Actual Operation

The operator explicitly approved one frozen handoff invocation. Before dispatch,
the separate handoff review c923b36c...7487 and all23 bound artifact/current
consumer hashes matched, pure validation accepted the132-pin packet, and the
cutover reservation did not exist. No credentials/native work in that precheck.

Executed ONCE, exit1:

env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B
-m docs.review_artifacts.companion_worker_preparation_20261023.execute_reviewed_v6b --execute-once

Wrapper SHA f9362e808538fa9d3fdbe7dc29b8bb947283bbd2ae720771963df1b8d4b37dfe.
Actual command was one line from the repository. Native token handling and
controller operations used the separately reviewed implementation, not a new
driver. No secret/token was printed, logged, exported or copied into public
evidence. Native internals were not separately traced command-by-command.

SHOWN from the61-record receipt:

- Input/staged/storage preconditions completed and four original worker
  shutdowns were acknowledged and confirmed at exit_verified.
- All four stages were renamed/reconnected; replacement identity/image/
  never-started/configuration checks passed.
- Runtime inventory was reached, then configured_compatibility was attempted.
  The controller failed in runtime_verification before any replacement start
  intent, health-loop or cited-query intent.
- Owned recovery removed the four prepared replacements, restored original
  names/network bindings and restarted the four original application objects.
- Controller output: rollback_verified=true, rollback_exact_baseline=false,
  receipt_complete=true, no unresolved operation arrays. services_started=true
  includes original restarts; it does not show new replacement startup.

Full sanitized output is in runtime_attempt_v6b/operation_outcome.json.
No --execute-once retry or alteration of the frozen inputs was made.

## Independent Read-Only Postcheck

Two bounded native read commands (list IDs, inspect only surviving known IDs)
captured11 selected rows. CLI hash reverified before each command; no exec,
service query, credentials, startup or lifecycle action during this postcheck.

SHOWN: all seven originals run under the same IDs/images/names and their
configured-network projections match the prior rows. Storage3 startup timestamps
did not change. Application4 startup timestamps changed because they restarted.
All four older stages retain equal shared captured fields. The four v6b IDs
are absent after owned cleanup. No health or data-volume contents were checked.

The raw postcheck's initial two aggregate flags are false and are preserved,
not overwritten. Their limitations are explained by the offline addendum:
the old capture had five fields not collected by the postcheck, preventing
full-row equality; three restored originals show IPAMConfig null versus {},
which changes the raw preservation hash but not the configured-network
projection. This does not establish byte-exact state restoration or service
health, and those five fields remain unverified in the postcheck.

## Concrete Offline Defect, Not An Invented Runtime Trace

Replaying the accepted packet shows all four final runtime preservation pins
were derived from staged raw network attachments retaining NetworkID="".
Filling only the already-reviewed immutable network ID changes every predicted
preservation digest while leaving the configured-network projection unchanged.
This is a SHOWN packet-model/adapter representation mismatch in the packet
prepared and reviewed by Codex, not a market/account or operator defect.

It is a concrete candidate explanation for configured_compatibility rejecting
after activation. However, the activated replacements' raw rows and exact failed
predicate/exception were not retained before rollback. Causation at that exact
runtime predicate remains UNVERIFIED. The NetworkID-only replay is not a complete
corrected final fingerprint: IPAM/default-alias representation must also be
covered before proposing a new packet. Do not weaken the identity/source guard.

## Evidence And Verification

Base: docs/review_artifacts/companion_worker_preparation_20261023/.

- runtime_attempt_v6b/operation_outcome.json SHA
  1ce084cbf3b204254414549b2c0ae3befafd93edb6006f6f88096a45506d744f
- runtime_attempt_v6b/receipt.jsonl SHA
  63003bed13993c1d5d044ba16c271b4cd51d16209ebcb206dec16b4be2315d5a
- runtime_attempt_v6b/post_inventory.json SHA
  44602ff88a1d978fe5b6ae50d47becb71f6d135de32a526feda930a837cc4d40
- runtime_attempt_v6b/offline_replay.json SHA
  939dc97df6e1a223e7bc597bbe2e6c92003093704fff2990e49d9c76de7e8cae
- replay_failed_runtime_packet.py SHA
  daa054973e85bbe20aebe0f5084062a8cfe792e960c515eef9fca8e3c546d17b

The public receipt is byte-identical to the private receipt, verified by hash
after completion. All61 records were inspected; no raw credential/document/
response payload is copied. Prior consumed receipts and accepted snapshots
are untouched. No success result was published for this failed attempt.

VERIFIED_ENV offline command:

env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B
-m docs.review_artifacts.companion_worker_preparation_20261023.replay_failed_runtime_packet

Exit0: seven originals running/same identities, all11 configured projections
match, older4 shared fields unchanged,0 replacement start/query intents and4
deterministic network-model mismatches. No pytest/full suite repeated, no extra
native capture or services invoked by this replay.

Next: separate bounded review of failure evidence and replay. After that, only
offline correction of the demonstrated packet representation defect and any
strictly necessary diagnostic gap is proposed. No patch/rebuild/preparation/
service retry is authorized by this checkpoint. New exact prepared IDs would
be required after an independently reviewed correction and fresh approval.
Runtime remains INCOMPLETE, evidence READY_FOR_INDEPENDENT_REVIEW.

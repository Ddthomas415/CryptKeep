# Journal prototype and contract extension - 2026-10-07

Active role: AUDITOR. Overall review INCOMPLETE.

## Historical versus current evidence

- Full read of 0020, its original accepted patch and all 13 supplied reviewer
  probe bodies. The original prototype is a storage primitive, not runner
  integration. The tests cover ordering, identity, rollback and replay.
- The historical reviewer probes deliberately demonstrate missing durable
  confirmation, corrupt-payload listing failure and unrestricted reducer
  writes. Passing such a probe means its expected limitation was observed,
  not that the limitation was fixed.
- Full read of 0021's production diff, NOT its entire patch/test body. It adds
  confirmation independent of application order, raw quarantine, a tolerant
  unresolved reader, schema upgrade and production reducer-key restrictions.
- Current candidate journal was read in full. Later changes require confirmed
  evidence for production apply, reject contradictory unwritten evidence and
  retain malformed identifiers/scopes. These distinguish resolved historical
  findings from current behavior. Legacy settle(written=True) still accepts
  caller confirmation; production uses apply with the stronger contract.
- Quarantine blocks application behind the damaged event. This is preservation
  of evidence, not successful recovery or a release tool. Power-loss durability
  and runner handling remain separate from the transaction guarantees below.

## Narrow verification

SHOWN, VERIFIED_ENV: candidate journal loaded directly with a stub storage
dependency. Only temporary, probe-owned SQLite files are opened; production
path resolution and repository conftest are not imported. Real transactions,
event schema and candidate journal code are exercised.

Command: ./.venv/bin/python -B
docs/review_artifacts/rev87_review_20261005/test_journal_storage_contract_probe.py

Result: 5 passed in 0.034 seconds, exit 0:

- later confirmation survives object reopen, ordered application counts once;
- unconfirmed production application refuses;
- quarantine keeps raw evidence and blocks overtaking/discard;
- production reducer cannot write a stop-state key;
- injected second counter write failure rolls back the first and event status.

Reopening is not process/power failure injection. Storage dependency is a
controlled adapter, not full production integration. No runner suite, CI,
host, actual campaign or exchange proof; no new current defect reproduced.

Candidate journal SHA256:
6c8ee1c44cd551a65139a16bfaa5fa18fbc29b4b5bee93c6e66835ae6e6f3ff8.

## Exact full-read submitted artifacts

Paths relative to extracted cryptkeep_review_bundle_2026-10-02.

| SHA256 | Artifact |
| --- | --- |
| `e7b83d2277dab4bbc09dff2cbcdb106fa7365b780f8e1402d3e9a9a1e618d470` | `27_exit_event_journal_prototype_ACCEPTED_WITH_RISK/codex_prototype_as_accepted.patch` |
| `6dd08b9d3e48f1f18af6f0c09f1df53b427d04466f407124e7358b3eb54378af` | `27_exit_event_journal_prototype_ACCEPTED_WITH_RISK/0020-storage-ordered-exit-event-journal-prototype-Codex-h.patch` |
| `ead286291145df3b64ed8ed66d241616732970bfadc574728f3d562fcacdc3b1` | `27_exit_event_journal_prototype_ACCEPTED_WITH_RISK/claude_review_probe.patch` |
| `328e96a3381d0a7d56d7eb333e627fa3ee0e366f56aa6d786acba99610ae6b7c` | `28_exit_event_journal_contract/production_files_only.diff` |

No production/config/account/campaign/process changes, publishing or deployment.

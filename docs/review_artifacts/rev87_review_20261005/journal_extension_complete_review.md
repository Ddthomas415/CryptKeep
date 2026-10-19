# Complete journal-extension patch 0021 - 2026-10-07

Active role: AUDITOR. Overall review INCOMPLETE.

All 1,121 lines of patch 0021 were read in five contiguous ranges, including
the full 610-line test addition and work-log contracts. This extends the
previous production-diff review; no complete runner-integration review is
implied.

## Evidence and limits

- SHOWN: supplied tests exercise confirmation, quarantine, byte preservation,
  restricted reducer types/keys, permanent identity after 120 events, old-table
  upgrade, lock failures and concurrent schema openings. The child-process
  tests kill after the first counter write and immediately after commit.
  Their presence is inspected evidence, not fresh passing process-kill proof.
- The historical test_production_mode_stores_plain_numbers_as_text applies
  an event without confirm. Later candidate requires confirmation through
  apply; preserve the later contract rather than treating that old expected
  behavior as current authority. Legacy settle(written=True) remains a
  different interface whose caller supplies confirmation.
- Quarantine deliberately blocks later application and keeps evidence. It
  does not establish an authorized repair/release procedure. A damaged scope
  causes the later candidate to hold application across scopes; preservation
  and service availability are separate properties.
- Schema-upgrade tests preserve old applied/unwritten/pending meanings. A
  newly upgraded old pending row is not automatically evidence of a written
  sell. Actual queue reconciliation remains required before application.
- Process crash, operating-system/power loss, runner failure handling and
  exchange-fill accounting are distinct; no permanent durability guarantee.

## Current isolated verification

Extended test_journal_storage_contract_probe.py with three tests: old-table
upgrade and row preservation; invalid UTF-8 payload preservation; damaged
scope blocking application in another scope. Together with the five prior
checks: 8 passed in 0.050 seconds, exit 0.

Command: ./.venv/bin/python -B
docs/review_artifacts/rev87_review_20261005/test_journal_storage_contract_probe.py

VERIFIED_ENV: direct candidate journal module, controlled storage adapter and
temporary probe-owned SQLite files only. No production imports, repository
conftest, operator databases, processes, config or accounts. No full supplied
suite, child-process kill, concurrency stress, CI, host or campaign rerun.
No new current defect reproduced in this slice.

## Exact full-read artifact

Path relative to extracted cryptkeep_review_bundle_2026-10-02.

| SHA256 | Artifact |
| --- | --- |
| `733ace79d9101ead763162833cae5c95bc448be0152a0d7bd5c2c83a8e31d39f` | `28_exit_event_journal_contract/0021-storage-exit-event-journal-gains-confirmation-quaran.patch` |

No production source, runtime settings, campaign, account, push, merge or
deployment changed. Review and isolated test artifacts only.

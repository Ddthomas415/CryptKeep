# Entry and exit dependency diffs - 2026-10-07

Active role: AUDITOR. Acceptance state: INCOMPLETE.

Full-content reading of five artifacts below, with bounded tracing against
the assembled rev87 candidate. This is not full reading of the corresponding
complete patches, renewed acceptance, test execution or deployment proof.

## Disposition

- 0016 refuses buys on any in-flight strategy intent or unreadable queue,
  before entry-state and risk-block writes. Signal history is still updated
  elsewhere. The lookup is not an atomic check-and-reservation transaction.
- 0017 moves the existing newest-200 queued/submitted sell scan ahead of
  bookkeeping. Its claim that bookkeeping occurs only after a written sell
  was too broad: the original code still records before queue submission.
  The supplied write-failure probe directly specifies that missing guarantee.
- 0018 moves application after queue writing, but uses one pending plan per
  scope, containing precomputed counter values. Unreadable evidence is dropped
  in that historical implementation. These are historical shortcomings, not
  new claims against the later journal implementation.
- Current candidate strategy_runner.py:505-645 recovers events from written
  queue rows, preserves unusable evidence through quarantine, and applies
  ordered events through the journal. Lines 2430-2568 attach evidence to the
  sell and reconcile only after upsert_intent. The older single-plan functions
  are superseded. Static tracing does not prove every crash/concurrency path.
- The current performance contract remains intent_reference_price. It is
  provisional risk-policy evidence, not reconciled realized PnL; rejected or
  cancelled sell intents are not actual completed trades.

No new current defect reproduced in this bounded slice. Existing findings in
the consolidated report remain open; absence of a new finding is not all-clear.
No tests run in this slice. No campaign, source, config, account, process or
deployment changes.

## Exact full-read artifacts

Paths relative to extracted cryptkeep_review_bundle_2026-10-02.

| SHA256 | Artifact |
| --- | --- |
| `994ae05844bc718aed55443c692666226c3fcf87e3b211c21c72436f31af70c2` | `23_entry_open_intent_fix/production_files_only.diff` |
| `28ae5afbd61131fb88cee49d39e1f26d8f647f1f625066ee9634fd51cae988dc` | `24_held_back_exit_bookkeeping/production_files_only.diff` |
| `aa5d5634a7922648b38c4738839bdd3e8c11cf59922c5e683bfc75f85b280327` | `25_exit_accounting_event/production_files_only.diff` |
| `53fd96e3b84565a71fe7831f14dfc2d1710eac3dd8a5cbed34869fe5dff17e49` | `23_entry_open_intent_fix/codex_probe_as_received.patch` |
| `b319a77d8e402c9f84b886b2e84bc97063d6fb1b400bab3c1d1015a7ff99b57a` | `25_exit_accounting_event/codex_probe_as_received.patch` |

# Runner journal correction diff and probes - 2026-10-07

Active role AUDITOR. Overall review INCOMPLETE. Four artifacts fully read,
626 lines total. Complete 0022/0023 patches are not claimed read by this slice.

## Disposition

- The 0023 production diff preserves malformed own-scope event evidence,
  prevents unconfirmed production application and handles damaged identifiers
  and scope. Latest candidate retains these changes. Historical silent-skip
  and no-confirm findings are not reopened as current defects.
- probe_r22_real.py covers rejected sells, replay-anchor loss, rowid reuse,
  manual removal of journal identity, multi-scope separation and backlog cost.
  Most results are printed rather than asserted. The file's name does not
  make every assertion independent proof of a safety contract.
- Rejected/cancelled intents count under the chosen provisional intent-time
  policy, not as realised losses. Deleting applied journal identity and then
  rebuilding from queue can cause replay; exactly-once requires retaining its
  durable evidence, not only the queue and current counter values.
- probe_r22_runner.py deletes state database/WAL/SHM files and prints venue
  escape/state reset outcomes. It was not executed; neither runtime isolation
  nor authorization to mutate operator state is inferred from a quoted probe.
- probe_r22_mutate.py hardcodes cloud interpreter and mutates files relative
  to its directory. Finally-restoration does not survive hard process death.
  A nonzero test result is labelled killed without distinguishing assertion
  failure from setup/import failure. Not a safe local mutation-run command or
  fresh coverage result; not run.

## Bounded current verification

Added two assertion-based checks to the existing isolated journal probe:
own-scope null exit event is quarantined/confirmed and replay is idempotent;
changed replay anchor triggers full reread without duplicate known identity.

Command: ./.venv/bin/python -B
docs/review_artifacts/rev87_review_20261005/test_journal_storage_contract_probe.py

Result: 10 tests passed in 0.224s, exit 0. VERIFIED_ENV: candidate journal
loaded directly, three selected runner helpers AST-extracted, temporary real
SQLite journal, in-memory state/queue doubles. No production imports or path
resolution. These two recovery checks are not real queue/store concurrency,
full runner integration, crash recovery, CI or host proof.

No new current defect reproduced. No production/config/account/campaign or
process changes. Existing reproduced findings elsewhere remain unresolved.

## Exact full-read artifacts

Paths relative to extracted cryptkeep_review_bundle_2026-10-02.

| SHA256 | Artifact |
| --- | --- |
| `1bc7cff87d822475f72b83a4ebf5eb27205e425761438d78a41d76b6aa5aa797` | `30_review_fixes_0021_0022/production_files_only.diff` |
| `a84218ffd950150489e83c2ce46e3acfb38885ddb0c385b6c8266246a57a6454` | `30_review_fixes_0021_0022/reviewer_probes_0022/probe_r22_mutate.py` |
| `d021c3da404782f03034a60a1327196d5af49fa33ed774c61372fa4b1b8c7879` | `30_review_fixes_0021_0022/reviewer_probes_0022/probe_r22_real.py` |
| `b5a6c36c65c1e240f47ccdbef6f7a96aa0cb820fc74cb4a9333670a61cc15241` | `30_review_fixes_0021_0022/reviewer_probes_0022/probe_r22_runner.py` |

# Screened Recovery Result, 2026-10-18

## Scope And Result

Active role: GATE (recording separate review). Selected-file recovery evidence is
ACCEPTED_WITH_RISK. Complete repository recovery remains INCOMPLETE.

SHOWN by the parent's completed command (exit 0): the reviewed helper made a
fresh selected-file copy at
`/Users/baitus/Documents/cryptkeep_data_archive/screened_recovery_20261018T190049Z_r2`.
The manifest timestamp is `2026-10-18T19:16:16.840995+00:00`.

- 6,414 files, 567,124,940 source bytes, extracted and hash-verified.
- 34 companion Python source files included.
- 41 explicit exclusions; checkpoint CSV has 6,455 data rows.
- Recovery archive size: 81,041,871 bytes.
- Four of seven raw input archives included; three excluded.
- All four selected public SQLite databases excluded because journals were
  present. No source database was opened through SQLite; no database recovery
  or restored database integrity result is claimed.

Exact command, hashes, exclusions by reason and limits:
`docs/review_artifacts/recovery_copy_20261018/actual_outcome.json`.
Detailed path inventory and per-file hashes are in the external
`backup_manifest.json` and `refreshed_checkpoint.csv`.

## Material Gaps

The following raw archives remain outside this copy:

- `docs/research/raw_archives_20261009/cmc_weekly_and_trending.tar.xz`:
  possible secret-pattern match, not a proven credential or leak.
- `docs/research/raw_archives_20261009/coinbase_hourly_last60d.tar.xz`:
  archive member refused by the bounded scanner.
- `docs/research/raw_archives_20261009/coinbase_hourly_prior10m.tar.xz`:
  archive member refused by the bounded scanner.

Excluded database paths:

- `research/coinbase_confirmation_usd_v1/public_archive.sqlite`
- `research/coinbase_confirmation_v1/public_archive.sqlite`
- `research/coinbase_retrospective_20261009/public_archive.sqlite`
- `research/multisymbol_baseline_v1/public_archive.sqlite`

Other exclusions include journal/SHM files, credential/runtime paths, opaque
assets/nested artifacts and possible secret patterns in test/public-data files.
No blanket false-positive clearance is inferred from earlier audits.

## Verification And Boundaries

VERIFIED_ENV for the completed command. Bound helper SHA256:
`8efaf5fc4e3ff508640fb038d6d2b1f74c7a30ece9ef1233449f491f051655a9`.
Bound test SHA256:
`281bf5be9942502c8801fda2216be1754303af7444a33e171c3eca247a301c60`.
The final synthetic gate passed 39 tests; separate preflight review accepted
the bounded correction with risk in `root_hardening_review.json`.
No unchanged tests were rerun after the actual copy.

The earlier failed copy at the sibling path without `_r2` remains INCOMPLETE:
820 copied files, no success manifest/archive/restore/CSV. It was not resumed,
overwritten or deleted. Rejected intermediate implementations and reviews remain
preserved; the successful copy does not retrospectively accept them.

HEAD remains `620bc8dbeee71cca327042902759e219e18f30b6`.
The zero-byte October 4 Git index lock remains untouched. All three original
checkpoint-draft checksums still match. No commit, push, source deletion, service
startup, scheduler, credential configuration, account or trading action occurred.

This is on the same laptop/disk, not offsite protection. Per-file consistency
and restored hashes are not a globally atomic snapshot or a working environment
restore. Git history is not copied. Heuristic screening is not universal secret
clearance or permission to publish. Final outcome/review/closeout records postdate
the copy and are not included in its snapshot.

## Next Boundary

Separate GATE saved-outcome review completed at 19:20:11 UTC:
`docs/review_artifacts/recovery_copy_20261018/outcome_review.json`.
It independently verified all 6,414 staged files, restored files and archive
members against manifest hashes, sizes and modes; the receipt hashes and all
6,455 CSV rows match. All 34 expected companion Python paths are included.
Disposition: ACCEPTED_WITH_RISK for selected-file local recovery only. The
reviewer did not independently observe the parent's invocation exit status or
read original excluded files. It did not rerun unchanged tests.

Preserve the successful selected-file copy and explicitly retain the
database/archive gaps.
The next meaningful preservation task is a separately scoped safe database
snapshot and read-only diagnosis of the three excluded raw archives, not another
blind full-copy rerun. No such follow-up operation is performed by this record.

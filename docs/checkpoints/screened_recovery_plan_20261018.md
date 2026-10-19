# Screened selected-file recovery copy

Date2026-10-18. ENGINEER stage; HIGH risk for copying potentially sensitive files.
Objective authorized by operator continuation: refresh the checkpoint list and
create a hash-verified recovery copy, without deleting or committing anything.
Implementation READY_FOR_INDEPENDENT_REVIEW before actual repository copy.

## Scope

Source: `/Users/baitus/Downloads/crypto-bot-pro`.
New exclusive destination outside Git:
`/Users/baitus/Documents/cryptkeep_data_archive/screened_recovery_20261018T190049Z`.
This is on the same Mac/disk, not an offsite or hardware-failure backup.

Inventory uses Git tracked+untracked nonignored paths with `--no-optional-locks`;
adds ignored companion source/config/docs and four public research archive
databases. It does not copy `.git`, runtime accounts/state, credentials, virtual
environments, caches or companion operational logs. It never removes the Git lock.
The earlier checkpoint list and all original files remain unchanged.

Known credential/runtime paths are rejected before reads. Existing byte-pattern
scanner plus additional fixed patterns screens candidates without printing
values. Compressed archives are inspected recursively within explicit bounds;
unsupported opaque content, possible secrets, unsafe archive members, symlinks,
unreadable/oversized files and journaled databases are not silently cleared.
An exclusion list explains each omission; excluded content is never copied.
Heuristic screening is not universal secret certification or permission to publish.

Each included source is hashed, copied, re-read before sealing and placed in a
new archive. The archive is restored manually into a new private directory;
only expected regular-file members are allowed. Every extracted file's size/hash
is checked, and restored SQLite copies receive a readonly immutable quick_check.
No SQL is run against original databases; no live account is read.
Directory access is owner-only; source executable flags are retained as owner
execution, while broader permissions are not reproduced.

The result includes `files/`, `recovery.tar.gz`, `restored/`,
`backup_manifest.json` and `refreshed_checkpoint.csv`. It proves selected-file
recovery, not a globally atomic concurrent snapshot, complete repository/history,
clean-checkout execution, service restoration or recoverability of excluded files.
Code is never executed from the recovery copy. Failures preserve partial output
and withhold the success manifest; nothing is automatically deleted or retried.

## Local Verification

VERIFIED_ENV local isolated synthetic run, exit0:24passed0.34s:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
  tests/test_build_recovery_copy.py tests/test_backup_artifact_secret_scan.py
```

Implementation SHA25612205c3260dd0184d349822f9a129165a82d580f86e6724b9b5bd74a71120aac;
tests b497a708fb0736b3546fbcacb401321cb78f1c9129290f4c70354a4f373be2d4;
unchanged existing scanner d87d3042307170ac43a29ff706032423fb2e9cf1c32bafcb9528e6c16af35e9f.

Only after separate review, one approved copy invocation is:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -E -B \
  -m scripts.research.build_recovery_copy \
  --root /Users/baitus/Downloads/crypto-bot-pro \
  --output /Users/baitus/Documents/cryptkeep_data_archive/screened_recovery_20261018T190049Z
```

External-directory write needs the normal sandbox permission. Review does not
authorize trading, startup, accounts, credential configuration, Git mutation or
deletion. No such action is included in this plan. Actual copy/restore proof is
pending; no recovery success is claimed from these synthetic tests.

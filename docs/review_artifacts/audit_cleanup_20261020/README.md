# Authorized obsolete audit-report cleanup

Scope: only top-level directories in `.cbp_state/audit_reports` matching
`(manual|repo_audit|repo_root_audit_reports)_202603(21|22)_[0-9]{6}`.
The user's pasted count100 is not reproduced: the exact-date scope is74
top-level directories,5094 regular files,213079770798 logical bytes and
213094068224 allocated bytes. There are217 retained root children, including
later reports, `archive`, `latest` and `handoffs`.

`inventory_before.json` preserves names, sizes, inode/device and modification
metadata only; no report contents or secret matches were read/copied. SHA256:
`0f0480b9fd7835e49ce8682fb6a2487c0f202c8b9efef5f093a43502ed87de0a`.
`targets.txt` lists the exact names. No tracked Git paths were found in this root.
The exact-name reference search in scripts/services/tools/tests/docs and the
task list found no references outside inventory/generated evidence exclusions.
That bounded search is not proof that every possible external consumer is absent.

Separate GATE reviewer Hegel independently verified all5225 metadata entries
and217 retained children, but blocked the first deletion command over concurrent
modification/path-identity risk. That first command was not executed. The review
is recorded in this Codex conversation. Cleanup must not be described as complete
until a successful final receipt and retained-child verification are recorded.

A subsequent `lsof` metadata check showed PID7539,
`com.apple.Virtualization.Virtua`, holding16843 report-tree descriptors, all
read-only. The operator says Claude is idle, not closed. No process was stopped.
Open file handles or filesystem snapshots may retain blocks after unlink; actual
free-space change must be reported, not the logical-size sum. Deletion is not
secure erasure and cannot erase copies in old backups. Possible historic secret
contents remain UNVERIFIED; no credential exposure or remediation is inferred.

Permanent deletion has no content rollback in this task. Inventory is a record,
not a recovery copy. Any partial failure must retain the receipt and report the
remaining targets; do not broaden the date range to reach the earlier count100.

## Execution result

2026-10-20T12:02:27.139893Z: the revised command completed, exit0. Separate
GATE Hegel returned ACCEPTED_WITH_RISK before execution for the accidental-writer
threat model. It uses a private quarantine, complete post-move revalidation,
descriptor-anchored operations and only inventoried filenames, not recursive
wildcard deletion. It is not secure against a hostile same-UID/root actor and
is not transactional/crash-durable recovery. The first rejected command was
never used. No process or service was stopped.

`cleanup_receipt.json` records5094 files and74 target directories removed,
217 retained children verified with matching device/inode/mode/mtime, no error
and no remaining quarantine. The inventory remains preserved. Immediate
reported free space was207667200000 bytes before and after (change0). Logical
bytes unlinked are not a claim of reclaimed disk capacity. The operator may
quit idle Claude normally when convenient and recheck disk space; no automatic
quit, kill or filesystem-snapshot removal is authorized or performed.

Separate post-execution GATE Hegel returned ACCEPTED_WITH_RISK: metadata-only
check exit0, all74 targets absent, all217 retained children unchanged, no
quarantine, receipt error=null. Receipt SHA256:
`73579403f0d35ebfa4b7a4a9742e7060b231e947293d0a5555c2ffe7aeb895df`.

At12:03:43Z, `lsof` on PID7539 with unlinked-file selection was joined by
device/inode to the inventory: all5094 removed regular files,213079770798
logical bytes, remain open by the VM. This is SHOWN metadata evidence, not
merely an inference from a flat free-space reading. The aggregate result is
`open_deleted_file_check.json`; no payloads, full process arguments or secrets
were read. Free space still needs a fresh check after the operator quits Claude.
